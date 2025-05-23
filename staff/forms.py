from django import forms
from .models import film, show, banner, Salle

class FilmForm(forms.ModelForm):
    class Meta:
        model = film
        fields = ['movie_name', 'url', 'movie_lang', 'movie_genre', 'movie_plot', 'duration']
        widgets = {
            'movie_plot': forms.Textarea(attrs={'rows': 4}),
            'duration': forms.NumberInput(attrs={'min': 60}),
        }

class ShowForm(forms.ModelForm):
    class Meta:
        model = show
        fields = ['movie', 'salle', 'showtime', 'price', 'start_date', 'end_date']
        widgets = {
            'showtime': forms.TimeInput(attrs={'type': 'time'}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'price': forms.NumberInput(attrs={'min': 0}),
        }

    def clean(self):
        cleaned_data = super().clean()
        # Form-specific validation: ensure start_date <= end_date
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("Start date cannot be after end date.")
        # Do not call show.clean here; let model validation handle conflicts
        return cleaned_data

class BannerForm(forms.ModelForm):
    class Meta:
        model = banner
        fields = ['movie', 'url']

class SalleForm(forms.ModelForm):
    class Meta:
        model = Salle
        fields = ['name', 'capacity']
        widgets = {
            'capacity': forms.NumberInput(attrs={'min': 1}),
        }