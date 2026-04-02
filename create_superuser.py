import os
import django

# Django'nun ayarlarını yükle
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stok_takip.settings')
django.setup()

from django.contrib.auth.models import User

# Ortam değişkenlerinden süper kullanıcı bilgilerini al
username = os.getenv("ADMIN_USERNAME")
email = os.getenv("ADMIN_EMAIL")
password = os.getenv("ADMIN_PASSWORD")

# Eğer ortam değişkenleri boşsa hata ver
if not username or not email or not password:
    print("⚠️ Superuser bilgileri eksik! Lütfen .env dosyasını kontrol edin.")
else:
    # Eğer kullanıcı zaten varsa, yeniden oluşturma
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)
        print(f"✅ Superuser '{username}' başarıyla oluşturuldu!")
    else:
        print(f"⚠️ Superuser '{username}' zaten mevcut.")
