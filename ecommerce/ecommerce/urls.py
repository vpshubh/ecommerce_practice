from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('store.urls')),  # Replace 'store' with your app name
    path('users/', include('users.urls')),
    path('', include('users.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)