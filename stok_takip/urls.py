from django.contrib import admin
from django.urls import path, include,re_path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.contrib.staticfiles.views import serve
from django.views.generic import TemplateView
import os
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('stok_app.urls')),  
    path('accounts/', include('django.contrib.auth.urls')),  # Django'nun hazır kullanıcı giriş-çıkış sistemini ekledik
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),  # Çıkış işlemi için URL
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),  # LOGIN EKLENDİ
    #re_path(r'^admin/(?P<path>.*)$', serve, {'document_root': os.path.join(settings.STATIC_ROOT, 'admin')}),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
]
