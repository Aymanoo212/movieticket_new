from django.contrib import admin

from .models import Salle, film,banner,show


admin.site.register(Salle)
admin.site.register(film)
admin.site.register(show)
admin.site.register(banner)
