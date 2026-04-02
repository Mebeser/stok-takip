from django.contrib import admin
from .models import UserProfile, Musteri, Satis, Firma, Urun,Log

# ✅ Firma Yönetimi - Sadece Admin Firma Ekleyebilir
@admin.register(Firma)
class FirmaAdmin(admin.ModelAdmin):
    list_display = ("ad", "adres", "telefon")
    search_fields = ("ad",)
    ordering = ("ad",)


# ✅ Kullanıcı Yönetimi - Kullanıcıları Yönetmek Kolaylaştırıldı
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "firma", "is_admin")  # Yetkiler kaldırıldı, detayları ekledik
    list_editable = ("firma",)
    search_fields = ("user__username",)
    list_filter = ("firma", "is_admin")

    fieldsets = (
        ("Kullanıcı Bilgileri", {"fields": ("user", "firma", "is_admin")}),
        ("Yetkiler", {
            "fields": ("can_manage_critical_stock", "can_add_product", "can_edit_product", "can_delete_product"),
            "classes": ("collapse",),  # Yetkileri gizleyerek daha düzenli görünüm sağladık
        }),
    )

# ✅ Satış Yönetimi - Toplam Tutar ve Filtreleme Geliştirildi
@admin.register(Satis)
class SatisAdmin(admin.ModelAdmin):
    list_display = ("urun", "musteri", "satis_yapan", "satis_adedi", "satis_fiyati", "toplam_tutar", "satis_tarihi", "firma")  
    search_fields = ("urun__ad", "musteri__ad_soyad", "satis_yapan__username")
    list_filter = ("firma", "satis_tarihi")
    ordering = ("-satis_tarihi",)

    def toplam_tutar(self, obj):
        return f"{obj.satis_adedi * obj.satis_fiyati:.2f} ₺"  # Admin panelinde gösterilecek
    toplam_tutar.short_description = "Toplam Tutar"  # Admin panelindeki başlığı belirledik

# ✅ Müşteri Yönetimi - Daha Kullanışlı Hale Getirildi
@admin.register(Musteri)
class MusteriAdmin(admin.ModelAdmin):
    list_display = ("ad_soyad", "firma", "telefon", "email", "eklenme_tarihi")
    search_fields = ("ad_soyad", "firma__ad", "telefon", "email")
    list_filter = ("firma", "eklenme_tarihi")
    ordering = ("-eklenme_tarihi",)

# ✅ Ürün Yönetimi - Ürünlerin Yönetimini Kolaylaştıralım
@admin.register(Urun)
class UrunAdmin(admin.ModelAdmin):
    list_display = ("ad", "kategori", "stok_miktari", "birim", "fiyat", "firma")
    list_editable = ("stok_miktari", "fiyat")
    search_fields = ("ad", "kategori", "firma__ad")
    list_filter = ("firma", "kategori")
    ordering = ("ad",)

#log kayıtları

@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ("kullanici", "firma", "kategori", "mesaj", "tarih")
    search_fields = ("kullanici__username", "kategori", "mesaj")
    list_filter = ("kategori", "tarih")
    ordering = ("-tarih",)