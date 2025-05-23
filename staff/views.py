from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import render
from .models import film, show, banner, Salle
from .forms import FilmForm, ShowForm, BannerForm, SalleForm

def staff_required(user):
    return user.is_staff or user.is_superuser

class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return staff_required(self.request.user)

class StaffDashboardView(StaffRequiredMixin, ListView):
    template_name = 'staff/dashboard.html'
    context_object_name = 'data'

    def get_queryset(self):
        return {
            'films': film.objects.all(),
            'shows': show.objects.select_related('movie', 'salle').all(),
            'banners': banner.objects.all(),
            'salles': Salle.objects.all(),
        }

class FilmCreateView(StaffRequiredMixin, CreateView):
    model = film
    form_class = FilmForm
    template_name = 'staff/form.html'
    success_url = reverse_lazy('staff:dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Film'
        return context

class FilmUpdateView(StaffRequiredMixin, UpdateView):
    model = film
    form_class = FilmForm
    template_name = 'staff/form.html'
    success_url = reverse_lazy('staff:dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Film'
        return context

class FilmDeleteView(StaffRequiredMixin, DeleteView):
    model = film
    template_name = 'staff/confirm_delete.html'
    success_url = reverse_lazy('staff:dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Delete Film'
        context['item'] = self.object.movie_name
        return context

class ShowCreateView(StaffRequiredMixin, CreateView):
    model = show
    form_class = ShowForm
    template_name = 'staff/form.html'
    success_url = reverse_lazy('staff:dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Show'
        context['error'] = self.request.GET.get('error', '')  # Pass error message if any
        return context

    def form_invalid(self, form):
        # Pass validation error to template
        error_message = ''
        for field, errors in form.errors.items():
            for error in errors:
                error_message += error + ' '
        return self.render_to_response(
            self.get_context_data(form=form, error=error_message)
        )

class ShowUpdateView(StaffRequiredMixin, UpdateView):
    model = show
    form_class = ShowForm
    template_name = 'staff/form.html'
    success_url = reverse_lazy('staff:dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Show'
        context['error'] = self.request.GET.get('error', '')
        return context

    def form_invalid(self, form):
        error_message = ''
        for field, errors in form.errors.items():
            for error in errors:
                error_message += error + ' '
        return self.render_to_response(
            self.get_context_data(form=form, error=error_message)
        )

class ShowDeleteView(StaffRequiredMixin, DeleteView):
    model = show
    template_name = 'staff/confirm_delete.html'
    success_url = reverse_lazy('staff:dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Delete Show'
        context['item'] = f"{self.object.movie.movie_name} in {self.object.salle.name} at {self.object.showtime}"
        return context

class BannerCreateView(StaffRequiredMixin, CreateView):
    model = banner
    form_class = BannerForm
    template_name = 'staff/form.html'
    success_url = reverse_lazy('staff:dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Banner'
        return context

class BannerUpdateView(StaffRequiredMixin, UpdateView):
    model = banner
    form_class = BannerForm
    template_name = 'staff/form.html'
    success_url = reverse_lazy('staff:dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Banner'
        return context

class BannerDeleteView(StaffRequiredMixin, DeleteView):
    model = banner
    template_name = 'staff/confirm_delete.html'
    success_url = reverse_lazy('staff:dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Delete Banner'
        context['item'] = f"Banner for {self.object.movie.movie_name}"
        return context

class SalleCreateView(StaffRequiredMixin, CreateView):
    model = Salle
    form_class = SalleForm
    template_name = 'staff/form.html'
    success_url = reverse_lazy('staff:dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Salle'
        return context

class SalleUpdateView(StaffRequiredMixin, UpdateView):
    model = Salle
    form_class = SalleForm
    template_name = 'staff/form.html'
    success_url = reverse_lazy('staff:dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Salle'
        return context

class SalleDeleteView(StaffRequiredMixin, DeleteView):
    model = Salle
    template_name = 'staff/confirm_delete.html'
    success_url = reverse_lazy('staff:dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Delete Salle'
        context['item'] = self.object.name
        return context