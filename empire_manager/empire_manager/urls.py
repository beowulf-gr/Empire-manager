from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('realm/', include('realms.urls')),  # Include realms URLs
    path('', lambda request: redirect('realm_list')),  # Redirect root URL to realm list
]
