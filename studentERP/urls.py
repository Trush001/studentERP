from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', core_views.index, name='index'),
    path('core/', include('core.urls')),
    path('student/', include('student.urls')),
    path('faculty/', include('faculty.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Add a fallback for the old submissions URL so cached pages don't break
    urlpatterns += static('/submissions/', document_root=settings.MEDIA_ROOT / 'submissions')
