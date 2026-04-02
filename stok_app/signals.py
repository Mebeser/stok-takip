from django.db.models.signals import post_save,post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.apps import apps  # Dinamik model çağırmak için
from .models import Firma, Musteri,Urun,Satis,Log
from django.core.mail import send_mail
from django.conf import settings

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile = apps.get_model('stok_app', 'UserProfile')  # Modeli buradan çağır
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'userProfile'):
        instance.userProfile.save()


@receiver(post_save, sender=Firma)
def anonim_musteri_ekle(sender, instance, created, **kwargs):
    """Her yeni firma için varsayılan 'Anonim Müşteri' ekler."""
    if created:  # Firma yeni oluşturulduğunda çalışsın
        Musteri.objects.get_or_create(
            firma=instance,
            ad_soyad="Anonim Müşteri",
            defaults={
                "telefon": "",
                "email": "",
                "adres": "Bilinmiyor",
            }
        )
        print(f"✅ {instance.ad} firmasına 'Anonim Müşteri' eklendi!")



# ✅ ÜRÜN EKLENDİĞİNDE LOG OLUŞTUR
@receiver(post_save, sender=Urun)
def log_urun_ekleme(sender, instance, created, **kwargs):
    if created:
        mesaj = f"Yeni ürün eklendi: {instance.ad} (Stok: {instance.stok_miktari})"
    else:
        mesaj = f"Ürün güncellendi: {instance.ad} (Yeni Stok: {instance.stok_miktari})"
    
    Log.objects.create(
        kullanici=instance.kullanici,  
        firma=instance.firma,
        kategori="ÜRÜN",
        mesaj=mesaj
    )

# ✅ ÜRÜN SİLİNDİĞİNDE LOG OLUŞTUR
@receiver(post_delete, sender=Urun)
def log_urun_silme(sender, instance, **kwargs):
    mesaj = f"Ürün silindi: {instance.ad}"
    
    Log.objects.create(
        kullanici=instance.kullanici,
        firma=instance.firma,
        kategori="ÜRÜN",
        mesaj=mesaj
    )

# ✅ SATIŞ YAPILDIĞINDA LOG OLUŞTUR
@receiver(post_save, sender=Satis)
def log_satis_yapildi(sender, instance, created, **kwargs):
    if created:
        mesaj = f"{instance.musteri} müşterisine {instance.satis_adedi} adet {instance.urun.ad} satıldı. (Fiyat: {instance.satis_fiyati}₺)"
        
        Log.objects.create(
            kullanici=instance.satis_yapan,
            firma=instance.firma,
            kategori="SATIŞ",
            mesaj=mesaj
        )

#kullanıcı eklendiğinde mail gönder
@receiver(post_save, sender=User)
def user_created_email(sender, instance, created, **kwargs):
    if created:
        admin_email = getattr(settings, 'ADMIN_EMAIL', None)
        if admin_email:
            send_mail(
                subject='Yeni Kullanıcı Kaydı 📩',
                message=f'Yeni bir kullanıcı kaydoldu: {instance.username}',
                from_email=None,
                recipient_list=[admin_email],
                fail_silently=True,
            )