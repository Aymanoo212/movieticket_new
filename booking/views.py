from django.forms import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from staff.models import film, show, banner, Salle
from .models import Booking
from django.http import HttpResponse, JsonResponse
from datetime import datetime, timedelta, time
from django.utils import timezone  # Correct import for timezone
from django.db.models import Q
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO

import logging  # For debugging

# Set up logging
logger = logging.getLogger(__name__)

def index(request):
    banners = banner.objects.all()
    now = timezone.now()
    logger.debug(f"Current time: {now}")
    
    # Get all films with shows between start_date and end_date
    films = film.objects.filter(
        show__end_date__gte=now.date(),
        show__start_date__lte=now.date()
    ).distinct()
    
    # Log films for debugging
    logger.debug(f"Films found: {[f.movie_name for f in films]}")
    
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    return render(request, 'booking/index.html', {
        'banners': banners,
        'films': films,  # Pass all films with valid shows
        'tomorrow': tomorrow
    })

def movie_detail(request, movie_id):
    film_obj = get_object_or_404(film, id=movie_id)
    now = timezone.now()
    logger.debug(f"Movie: {film_obj.movie_name}, Duration: {film_obj.duration}, Current time: {now}")
    
    showtimes = show.objects.filter(
        movie=film_obj,
        end_date__gte=now.date(),
        start_date__lte=now.date()
    ).select_related('salle')

    # Filter out shows that have ended today
    filtered_showtimes = []
    tz = timezone.get_current_timezone()
    for s in showtimes:
        show_datetime = datetime.combine(now.date(), s.showtime, tzinfo=tz)
        end_datetime = show_datetime + timedelta(minutes=film_obj.duration)
        logger.debug(f"Show: {s.showtime}, Start: {show_datetime}, End: {end_datetime}")
        if now.date() < s.start_date or (now.date() == s.start_date and now < end_datetime):
            filtered_showtimes.append(s)

    logger.debug(f"Filtered showtimes: {[s.showtime for s in filtered_showtimes]}")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    return render(request, 'booking/movie_detail.html', {
        'film': film_obj,
        'showtimes': filtered_showtimes,
        'tomorrow': tomorrow
    })

def show_selection(request):
    date_str = request.GET.get('date')
    default_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    if date_str and re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            date = date_str
        except ValueError:
            selected_date = datetime.now().date() + timedelta(days=1)
            date = default_date
    else:
        selected_date = datetime.now().date() + timedelta(days=1)
        date = default_date

    now = timezone.now()
    logger.debug(f"Selected date: {selected_date}, Current time: {now}")
    
    films = film.objects.prefetch_related('show_set__salle').filter(
        show__start_date__lte=selected_date, 
        show__end_date__gte=selected_date
    ).distinct()
    
    films_dict = {}
    tz = timezone.get_current_timezone()
    for f in films:
        showtimes = {}
        for s in f.show_set.filter(
            start_date__lte=selected_date, 
            end_date__gte=selected_date
        ):
            show_datetime = datetime.combine(selected_date, s.showtime, tzinfo=tz)
            end_datetime = show_datetime + timedelta(minutes=f.duration)
            logger.debug(f"Film: {f.movie_name}, Show: {s.showtime}, Start: {show_datetime}, End: {end_datetime}")
            # Include show if it's on a future date or hasn't ended today
            if selected_date > now.date() or (selected_date == now.date() and now < end_datetime):
                showtimes[s.id] = {'showtime': s.showtime, 'salle': s.salle.name}
        if showtimes:
            films_dict[f.movie_name] = {'url': f.url, 'showtimes': showtimes}
    
    logger.debug(f"Films with showtimes: {films_dict.keys()}")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    thirty_days_later = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    return render(request, 'booking/show_selection.html', {
        'films': films_dict, 
        'date': date, 
        'tomorrow': tomorrow, 
        'thirty_days_later': thirty_days_later
    })

@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-show_date').select_related('show__movie', 'show__salle')
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    today = datetime.now().date()
    return render(request, 'booking/bookings.html', {'data': bookings, 'today': today, 'tomorrow': tomorrow})

def generate_booking_pdf(booking, film, salle, show, sdate, seats, total):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        name='Title',
        fontSize=18,
        spaceAfter=20,
        alignment=1,  # Center
        textColor=colors.darkblue,
        fontName='Helvetica-Bold'
    )
    normal_style = ParagraphStyle(
        name='Normal',
        fontSize=12,
        spaceAfter=10,
        fontName='Helvetica'
    )
    
    # Title
    elements.append(Paragraph("MovieTicket Booking Receipt", title_style))
    elements.append(Spacer(1, 12))
    
    # Booking details
    data = [
        ["Movie:", film.movie_name],
        ["Hall:", salle.name],
        ["Date:", sdate],
        ["Showtime:", show.showtime.strftime('%I:%M %p')],
        ["Seats:", seats],  # Keep as-is (e.g., "C4,A5")
        ["Total:", f"${total:.2f}"],
        ["User:", booking.user.username],
        ["Booking ID:", str(booking.id)],
        ["Booking Date:", booking.show_date.strftime('%Y-%m-%d')],
    ]
    
    table = Table(data, colWidths=[100, 300])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
    ]))
    elements.append(table)
    
    # Footer
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Thank you for booking with MovieTicket!", normal_style))
    elements.append(Paragraph("Contact us at support@movieticket.com", normal_style))
    
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

@login_required
def checkout(request):
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    if request.method == 'POST':
        show_id = request.POST.get('showid')
        show_date = request.POST.get('showdate')
        seats = request.POST.get('seats')
        if show_id and show_date and seats:
            show_obj = get_object_or_404(show, id=show_id)
            seat_list = seats.split(',')
            # Basic format check before model validation
            seat_pattern = re.compile(r'^[A-Z][1-9][0-9]*$')
            for seat in seat_list:
                if not seat_pattern.match(seat.strip()):
                    return render(request, 'booking/error.html', {
                        'error': f"Seat '{seat}' is not in a valid format (e.g., A1, B12).",
                        'tomorrow': tomorrow
                    })
            try:
                booking = Booking.objects.create(
                    user=request.user,
                    show=show_obj,
                    show_date=show_date,
                    seat_num=seats
                )
            except ValidationError as e:
                return render(request, 'booking/error.html', {
                    'error': str(e),
                    'tomorrow': tomorrow
                })
            total = len(seat_list) * show_obj.price
            context = {
                'film': show_obj.movie,
                'salle': show_obj.salle,
                'sdate': show_date,
                'show': show_obj,
                'seats': seats,
                'total': total,
                'tomorrow': tomorrow,
                'booking_id': booking.id
            }
            return render(request, 'booking/checkout.html', context)
    elif request.GET.get('download_pdf') == 'true':
        booking_id = request.GET.get('booking_id')
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        show_obj = booking.show
        film = show_obj.movie
        salle = show_obj.salle
        sdate = booking.show_date.strftime('%Y-%m-%d')
        seats = booking.seat_num
        total = len(seats.split(',')) * show_obj.price
        
        pdf = generate_booking_pdf(booking, film, salle, show_obj, sdate, seats, total)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="booking_{booking.id}_receipt.pdf"'
        response.write(pdf)
        return response
    return redirect('index')

@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if booking.show_date >= datetime.now().date():
        booking.delete()
    return redirect('my_bookings')

def booked_seats(request):
    show_id = request.GET.get('show_id')
    show_date = request.GET.get('show_date')
    bookings = Booking.objects.filter(show_id=show_id, show_date=show_date)
    seats = ','.join([b.seat_num for b in bookings])
    return HttpResponse(seats)

def show_details(request):
    show_id = request.GET.get('show_id')
    try:
        show_obj = show.objects.select_related('salle').get(id=show_id)
        return JsonResponse({
            'capacity': show_obj.salle.capacity,
            'salle_name': show_obj.salle.name,
        })
    except show.DoesNotExist:
        return JsonResponse({'error': 'Show not found'}, status=404)