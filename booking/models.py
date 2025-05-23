from django.db import models
from django.conf import settings
from staff.models import show, Salle
from django.core.exceptions import ValidationError
import re

class Booking(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    show = models.ForeignKey(show, on_delete=models.CASCADE)
    show_date = models.DateField()
    seat_num = models.CharField(max_length=100)

    def clean(self):
        if not self.seat_num:
            raise ValidationError("Seat numbers cannot be empty.")
        
        seats = self.seat_num.split(',')
        salle_capacity = self.show.salle.capacity
        seat_pattern = re.compile(r'^[A-Z][1-9][0-9]*$')  # Matches A1, B12, etc.
        max_seats_per_row = 8  # Matches show_selection.html (8 seats per row)
        row_labels = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

        for seat in seats:
            seat = seat.strip()
            if not seat_pattern.match(seat):
                raise ValidationError(f"Seat '{seat}' is not in a valid format (e.g., A1, B12).")
            
            row = seat[0]  # e.g., 'C'
            try:
                col = int(seat[1:])  # e.g., '4' from 'C4'
            except ValueError:
                raise ValidationError(f"Seat '{seat}' column must be a valid integer.")
            
            if row not in row_labels:
                raise ValidationError(f"Seat '{seat}' row '{row}' is invalid.")
            
            row_index = row_labels.index(row)
            max_rows = (salle_capacity + max_seats_per_row - 1) // max_seats_per_row
            
            if row_index >= max_rows:
                raise ValidationError(f"Seat '{seat}' row '{row}' exceeds hall capacity (max {max_rows} rows).")
            
            if col < 1 or col > max_seats_per_row:
                raise ValidationError(f"Seat '{seat}' column {col} is invalid (must be 1 to {max_seats_per_row}).")
            
            seat_index = row_index * max_seats_per_row + col
            if seat_index > salle_capacity:
                raise ValidationError(f"Seat '{seat}' exceeds hall capacity of {salle_capacity}.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)