from django.forms import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from staff.models import film, show, banner, Salle
from .models import Booking
from django.http import HttpResponse, JsonResponse
from datetime import datetime, timedelta, time
from django.utils import timezone
from django.db.models import Q
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO

# qui affiche la page d'accueil avec les bannières et les films disponibles.
def index(request): 
    banners = banner.objects.all()
    now = timezone.now()
    
    # Get all films with shows between start_date and end_date
    films = film.objects.filter(
        show__end_date__gte=now.date(),
        show__start_date__lte=now.date()
    ).distinct()
    
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    return render(request, 'booking/index.html', {
        'banners': banners,
        'films': films,
        'tomorrow': tomorrow
    })

# pour afficher les détails d'un film spécifique
def movie_detail(request, movie_id):
    film_obj = get_object_or_404(film, id=movie_id)
    now = timezone.now()
    
    showtimes = show.objects.filter(
        movie=film_obj,
        end_date__gte=now.date(),
        start_date__lte=now.date()
    ).select_related('salle')

    # filtrer les séances encore valides aujourd'hui
    filtered_showtimes = []
    tz = timezone.get_current_timezone()

    # Parcourt les séances pour filtrer celles qui ne sont pas encore terminées :
    for s in showtimes:
        show_datetime = datetime.combine(now.date(), s.showtime, tzinfo=tz)
        end_datetime = show_datetime + timedelta(minutes=film_obj.duration)
        if now.date() < s.start_date or (now.date() == s.start_date and now < end_datetime):
            filtered_showtimes.append(s)

    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    return render(request, 'booking/movie_detail.html', {
        'film': film_obj,
        'showtimes': filtered_showtimes,
        'tomorrow': tomorrow
    })

# pour permettre à l'utilisateur de choisir une séance pour une date donnée.
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
    
    films = film.objects.prefetch_related('show_set__salle').filter(
        show__start_date__lte=selected_date, 
        show__end_date__gte=selected_date
    ).distinct()
    
    films_dict = {}
    tz = timezone.get_current_timezone()

    # Parcourt les films et leurs séances pour créer un dictionnaire
    for f in films:
        showtimes = {}
        for s in f.show_set.filter(
            start_date__lte=selected_date, 
            end_date__gte=selected_date
        ):
            # vérifie que la séance n'est pas terminée
            show_datetime = datetime.combine(selected_date, s.showtime, tzinfo=tz)
            end_datetime = show_datetime + timedelta(minutes=f.duration)
            if selected_date > now.date() or (selected_date == now.date() and now < end_datetime):
                showtimes[s.id] = {'showtime': s.showtime, 'salle': s.salle.name}
        if showtimes:
            films_dict[f.movie_name] = {'url': f.url, 'showtimes': showtimes}
    
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    # Calcule la date de demain et celle dans 30 jours pour limiter les choix de dates.
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
    # Crée un buffer en mémoire pour stocker le PDF
    buffer = BytesIO()
    # Initialise un document PDF avec la taille letter
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        name='Title',
        fontSize=18,
        spaceAfter=20,
        alignment=1,
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
    elements.append(Paragraph("Morro_Cine Booking Receipt", title_style))
    elements.append(Spacer(1, 12))
    
    # Booking details
    data = [
        ["Movie:", film.movie_name],
        ["Hall:", salle.name],
        ["Date:", sdate],
        ["Showtime:", show.showtime.strftime('%I:%M %p')],
        ["Seats:", seats],
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
    elements.append(Paragraph("Thank you for booking with Morro_Cine!", normal_style))
    elements.append(Paragraph("Contact us at support@Morro_Cine.com", normal_style))

    #Génère le PDF à partir des éléments.
    doc.build(elements)
    #Récupère le contenu du buffer.
    pdf = buffer.getvalue()
    #Ferme le buffer et retourne le PDF.
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
            # Calcule le coût total (nombre de sièges × prix de la séance).
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
        
        # Génère le PDF de réservation.
        pdf = generate_booking_pdf(booking, film, salle, show_obj, sdate, seats, total)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="booking_{booking.id}_receipt.pdf"'
        response.write(pdf)
        return response
    return redirect('index')

# pour annuler une réservation.
@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if booking.show_date >= datetime.now().date():
        booking.delete()
    return redirect('my_bookings')

# pour récupérer les sièges réservés pour une séance spécifique.
def booked_seats(request):
    show_id = request.GET.get('show_id')
    show_date = request.GET.get('show_date')
    bookings = Booking.objects.filter(show_id=show_id, show_date=show_date)
    # Combine tous les numéros de sièges réservés en une seule chaîne séparée par des virgules.
    seats = ','.join([b.seat_num for b in bookings])
    return HttpResponse(seats)

# pour retourner les détails d'une séance en JSON.
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