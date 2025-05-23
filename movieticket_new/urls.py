from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('staff/', include('staff.urls', namespace='staff')),
    path('', include('booking.urls')),
]