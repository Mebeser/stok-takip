from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group, Permission
from django.core.exceptions import ValidationError
User = get_user_model()  # Döngüsel importu engeller
from django.utils.timezone import now
import uuid

class Firma(models.Model):
    ad = models.CharField(max_length=255, unique=True)  # Firma adı benzersiz olmalı
    adres = models.TextField(blank=True, null=True)
    telefon = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.ad


class Urun(models.Model):
    BIRIM_SECENEKLERI = [
        ('adet', 'Adet'),
        ('kg', 'Kilogram'),
        ('m', 'Metre'),
        ('lt', 'Litre'),
        ('kutu', 'Kutu'),
    ]

    ad = models.CharField(max_length=100)
    kategori = models.CharField(max_length=50)
    stok_miktari = models.IntegerField()
    birim = models.CharField(max_length=10, choices=BIRIM_SECENEKLERI, default='adet')  
    fiyat = models.DecimalField(max_digits=10, decimal_places=2)
    tarih = models.DateTimeField(auto_now_add=True)
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    firma = models.ForeignKey("Firma", on_delete=models.CASCADE, null=True, blank=True)
    kritik_stok = models.PositiveIntegerField(default=5)
    son_kritik_stok_tarihi = models.DateTimeField(null=True, blank=True)

    # ✅ Barkod Alanı (Manuel + Otomatik Destekli)
    barkod = models.CharField(max_length=50, unique=True, null=True, blank=True)

    def kritik_seviyede_mi(self):
        return self.stok_miktari <= self.kritik_stok  

    def save(self, *args, **kwargs):
        # Eğer barkod yoksa, otomatik oluştur
        if not self.barkod:
            self.barkod = self.generate_barkod()
        super().save(*args, **kwargs)

    def generate_barkod(self):
        """Barkod üretme fonksiyonu"""
        new_barkod = str(uuid.uuid4().int)[:12]  # 12 haneli benzersiz barkod oluştur
        while Urun.objects.filter(barkod=new_barkod).exists():  # Aynı barkod varsa yeniden oluştur
            new_barkod = str(uuid.uuid4().int)[:12]
        return new_barkod

    def __str__(self):
        return f"{self.ad} ({self.birim}) - {self.barkod if self.barkod else 'Barkod Yok'}"



class Musteri(models.Model):
    firma = models.ForeignKey(
        "Firma", 
        on_delete=models.CASCADE,  # Firma silinirse müşteriler de silinsin
        related_name="musteriler", # Geriye doğru erişim için
        null=True, blank=True 
    )
    ad_soyad = models.CharField(max_length=255)
    telefon = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    adres = models.TextField(blank=True, null=True)
    eklenme_tarihi = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.ad_soyad 






class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    firma = models.ForeignKey(
    "Firma", 
    on_delete=models.SET_NULL, 
    null=True, 
    blank=True,
    default=None
)
    is_admin = models.BooleanField(default=False)  # Yönetici yetkisi
    can_manage_critical_stock = models.BooleanField(default=False)  # Kritik stok yönetimi izni
    can_add_product = models.BooleanField(default=True)  # Ürün ekleme izni
    can_edit_product = models.BooleanField(default=True)  # Ürün güncelleme izni
    can_delete_product = models.BooleanField(default=True)  # Ürün silme izni

    def __str__(self):
        return self.user.username

class Satis(models.Model):
    urun = models.ForeignKey(Urun, on_delete=models.CASCADE)
    musteri = models.ForeignKey(Musteri, on_delete=models.SET_NULL, null=True, blank=True)
    satis_yapan = models.ForeignKey(User, on_delete=models.CASCADE)
    satis_adedi = models.PositiveIntegerField()
    satis_fiyati = models.DecimalField(max_digits=10, decimal_places=2)
    satis_tarihi = models.DateTimeField(default=now)
    firma = models.ForeignKey(Firma, on_delete=models.CASCADE, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.pk is None:  # Yeni kayıt ekleniyorsa stok düşülsün
            if self.urun.stok_miktari < self.satis_adedi:
                raise ValidationError(f"⚠ {self.urun.ad} için stok yetersiz! Mevcut: {self.urun.stok_miktari}, Satış: {self.satis_adedi}")
            self.urun.stok_miktari -= self.satis_adedi
            self.urun.save()

        super(Satis, self).save(*args, **kwargs)

    def toplam_tutar(self):
        return self.satis_adedi * self.satis_fiyati

    def __str__(self):
        return f"{self.musteri} - {self.urun.ad} - {self.satis_adedi} Adet - {self.satis_fiyati} ₺"
    




class Log(models.Model):
    KATEGORI_SECENEKLERI = [
        ('ÜRÜN', 'Ürün İşlemi'),
        ('SATIŞ', 'Satış İşlemi'),
        ('STOK', 'Stok Güncelleme'),
        ('GENEL', 'Genel İşlem'),
    ]

    kullanici = models.ForeignKey(User, on_delete=models.CASCADE)  # İşlemi yapan kullanıcı
    firma = models.ForeignKey("Firma", on_delete=models.CASCADE, null=True, blank=True)  # Firma bilgisi
    kategori = models.CharField(max_length=20, choices=KATEGORI_SECENEKLERI)  # İşlem kategorisi
    mesaj = models.TextField()  # Yapılan işlem detayı
    tarih = models.DateTimeField(default=now )  # İşlem zamanı

    def __str__(self):
        return f"{self.kullanici} - {self.kategori} - {self.tarih.strftime('%d/%m/%Y %H:%M')}"






