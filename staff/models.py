from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.validators import MinValueValidator

class Salle(models.Model):
    name = models.CharField(max_length=50, unique=True)  # e.g., "Hall 1", "Hall 2"
    capacity = models.PositiveIntegerField()  # Number of seats in the hall

    def __str__(self):
        return self.name

class film(models.Model):
    movie_name = models.CharField(max_length=100)
    url = models.URLField()
    movie_lang = models.CharField(max_length=50, blank=True)
    movie_genre = models.CharField(max_length=50, blank=True)
    movie_plot = models.TextField(blank=True)
    duration = models.PositiveIntegerField(
        default=120,
        help_text="Duration in minutes",
        validators=[MinValueValidator(60)]  # Ensure duration is at least 60 minutes
    )

    def __str__(self):
        return self.movie_name

class show(models.Model):
    movie = models.ForeignKey(film, on_delete=models.CASCADE)
    salle = models.ForeignKey(Salle, on_delete=models.CASCADE)
    showtime = models.TimeField()
    price = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.movie.movie_name} in {self.salle.name} at {self.showtime}"

    def clean(self):
        # Ensure start_date is not after end_date
        if self.start_date > self.end_date:
            raise ValidationError("Start date cannot be after end date.")

        # Check for overlapping shows in the same salle

        if self.movie and self.salle:  # Ensure movie and salle are set
            tz = timezone.get_current_timezone()
            current_show_start_date = self.start_date
            current_show_end_date = self.end_date
            duration_minutes = self.movie.duration

            # pour vérifier les conflits de programmation.
            current_date = current_show_start_date
            while current_date <= current_show_end_date:
                # Calculate start and end datetimes for the current show
                show_datetime = datetime.combine(current_date, self.showtime, tzinfo=tz)
                end_datetime = show_datetime + timedelta(minutes=duration_minutes)

                # Check for existing shows in the same salle on this date
                conflicting_shows = show.objects.filter(
                    salle=self.salle,
                    start_date__lte=current_date,
                    end_date__gte=current_date
                ).exclude(pk=self.pk)  # Exclude the current show when editing

                for existing_show in conflicting_shows:
                    existing_show_datetime = datetime.combine(current_date, existing_show.showtime, tzinfo=tz)
                    existing_end_datetime = existing_show_datetime + timedelta(minutes=existing_show.movie.duration)

                    # Vérifie s'il y a un chevauchement entre la séance actuelle et une séance existante :
                    # Si l'heure de fin de la nouvelle séance est après le début de l'existante et
                    # l'heure de début de la nouvelle séance est avant la fin de l'existante, il y a un conflit.
                    if not (end_datetime <= existing_show_datetime or show_datetime >= existing_end_datetime):
                        raise ValidationError(
                            f"Show conflicts with '{existing_show.movie.movie_name}' "
                            f"on {current_date.strftime('%Y-%m-%d')} from {existing_show.showtime.strftime('%I:%M %p')} "
                            f"to {(existing_show_datetime + timedelta(minutes=existing_show.movie.duration)).strftime('%I:%M %p')} "
                            f"in {self.salle.name}."
                        )
                # Passe à la date suivante dans la boucle.
                current_date += timedelta(days=1)

    def save(self, *args, **kwargs):
        # Run full_clean (which calls clean) before saving
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=['start_date', 'end_date', 'showtime']),
        ]

class banner(models.Model):
    movie = models.ForeignKey(film, on_delete=models.CASCADE)
    url = models.URLField()

    def __str__(self):
        return f"Banner for {self.movie.movie_name}"