from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('detail/<int:movie_id>/', views.movie_detail, name='movie_detail'),
    path('show/', views.show_selection, name='show_selection'),
    path('mybookings/', views.my_bookings, name='my_bookings'),
    path('checkout/', views.checkout, name='checkout'),
    path('cancelbooking/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('bookedseats/', views.booked_seats, name='booked_seats'),
    path('show_details/', views.show_details, name='show_details'),
]