from django.urls import path, include, re_path
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
import os

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('gps_app.urls')),
]

# Serve media files
if settings.DEBUG or True:  # Allow in production for now
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve React frontend
if hasattr(settings, 'REACT_BUILD_DIR'):
    class ReactAppView(TemplateView):
        template_name = 'index.html'
        
        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            return context
    
    # Catch-all pattern for React Router
    urlpatterns += [
        re_path(r'^.*$', ReactAppView.as_view(), name='react-app'),
    ]