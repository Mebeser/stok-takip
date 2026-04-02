from django.shortcuts import render,redirect, get_object_or_404
from .models import Urun,UserProfile,Satis,Musteri,Log 
from .forms import UrunForm,UserRegisterForm,KayitFormu,SatisForm
from django.contrib.auth.decorators import login_required,permission_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm,AuthenticationForm
from django.contrib.auth import login,authenticate
from django.contrib.auth.models import User,Group
from django.contrib import messages
from .forms import SatisForm,MusteriForm
from django.db import transaction,models,IntegrityError
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import F,Q
from datetime import timedelta,datetime
from django.utils.timezone import now, timedelta
from django.http import HttpResponse
import csv
import pdfkit
from django.urls import path
from decimal import Decimal
import uuid

@login_required
def stok_list(request):
    user = request.user

    #  Kullanıcının firması
    try:
        user_profile = UserProfile.objects.get(user=user)
        kullanici_firma = user_profile.firma
    except UserProfile.DoesNotExist:
        messages.error(request, "⚠ Kullanıcı profili bulunamadı, lütfen yöneticinize başvurun!")
        return redirect("dashboard")

    #  Yetki Kontrolleri
    user_groups = user.groups.values_list('name', flat=True)
    is_admin = "Yönetici" in user_groups
    is_depo_sorumlusu = "Depo Sorumlusu" in user_groups
    is_satis_sorumlusu = "Satış Sorumlusu" in user_groups

    #  Yetki Tanımları
    can_add_urun = is_admin or is_depo_sorumlusu
    can_change_urun = is_admin or is_depo_sorumlusu
    can_delete_urun = is_admin
    can_sell_urun = is_admin or is_satis_sorumlusu
    can_add_musteri = user.has_perm("stok_app.add_musteri")

    #  Ürünleri Listele (Sadece Kullanıcının Firmasına Ait Ürünler)
    urunler = Urun.objects.filter(firma=kullanici_firma)

    #  **Filtreleme İşlemi**
    kategori = request.GET.get("kategori")
    min_fiyat = request.GET.get("min_fiyat")
    max_fiyat = request.GET.get("max_fiyat")
    stok_durum = request.GET.get("stok_durum")
    barkod = request.GET.get("barkod")  # ✅ **Barkod Filtreleme Eklendi**

    if kategori:
        urunler = urunler.filter(kategori__icontains=kategori)

    if min_fiyat:
        urunler = urunler.filter(fiyat__gte=min_fiyat)

    if max_fiyat:
        urunler = urunler.filter(fiyat__lte=max_fiyat)

    if stok_durum == "stokta_var":
        urunler = urunler.filter(stok_miktari__gt=0)
    elif stok_durum == "stokta_yok":
        urunler = urunler.filter(stok_miktari=0)

    if barkod:
        urunler = urunler.filter(barkod__iexact=barkod)  # ✅ **Barkod Tam Eşleşmeli Filtreleme Eklendi**

    # 🚨 Kritik Stok Kontrolü
    kritik_urunler = urunler.filter(stok_miktari__lte=models.F('kritik_stok'))

    return render(request, "stok_list.html", {
        "urunler": urunler,
        "user_groups": user_groups,
        "can_add_urun": can_add_urun,
        "can_change_urun": can_change_urun,
        "can_delete_urun": can_delete_urun,
        "can_sell_urun": can_sell_urun,
        "can_add_musteri": can_add_musteri,
        "kritik_urunler": kritik_urunler
    })



#ürün Ekleme

@login_required
@permission_required('stok_app.add_urun', raise_exception=True)
def urun_ekle(request):
    kullanici = request.user

    try:
        user_profile = UserProfile.objects.get(user=kullanici)
        kullanici_firma = user_profile.firma
    except UserProfile.DoesNotExist:
        messages.error(request, "⚠ Kullanıcı profili bulunamadı!")
        return redirect("stok_list")

    if request.method == "POST":
        form = UrunForm(request.POST)
        if form.is_valid():
            ad = form.cleaned_data["ad"].strip().lower()
            kategori = form.cleaned_data["kategori"].strip().lower()
            birim = form.cleaned_data["birim"].strip().lower()
            fiyat = form.cleaned_data["fiyat"]
            yeni_stok = form.cleaned_data["stok_miktari"]
            kritik_stok = form.cleaned_data["kritik_stok"]
            barkod = form.cleaned_data["barkod"]

            # ✅ **Barkod Kontrolü**
            if barkod:
                urun_barkod_var = Urun.objects.filter(barkod=barkod, firma=kullanici_firma).first()
                if urun_barkod_var:
                    if urun_barkod_var.ad.lower() != ad or urun_barkod_var.kategori.lower() != kategori:
                        messages.error(request, f"🚨 Bu barkod zaten **{urun_barkod_var.ad}** ürünü için kullanılmış!")
                        print("❌ Barkod çakışması oldu!")  # Terminalde hata kontrolü
                        return render(request, "urun_ekle.html", {"form": form})  
            else:
                barkod = str(uuid.uuid4().int)[:12]  

            # ✅ **Aynı Ürün Daha Önce Eklenmiş mi Kontrol Et?**
            mevcut_urun = Urun.objects.filter(
                ad__iexact=ad, kategori__iexact=kategori, birim__iexact=birim,
                fiyat=fiyat, firma=kullanici_firma
            ).first()

            if mevcut_urun:
                mevcut_urun.stok_miktari += yeni_stok
                mevcut_urun.barkod = mevcut_urun.barkod or barkod
                mevcut_urun.save()
                messages.success(request, f"✅ {ad} adlı ürün güncellendi! Yeni stok: {mevcut_urun.stok_miktari}")
            else:
                yeni_urun = form.save(commit=False)
                yeni_urun.firma = kullanici_firma
                yeni_urun.kullanici = kullanici
                yeni_urun.barkod = barkod
                yeni_urun.save()
                messages.success(request, f"🎉 {ad} adlı yeni ürün eklendi! Barkod: {barkod}")

            return redirect("stok_list")

        else:
            print("❌ Form validasyon hataları:", form.errors)  # Form hatalarını terminale yazdır

    else:
        form = UrunForm()

    return render(request, "urun_ekle.html", {"form": form})





#ürün silme

@permission_required('stok_app.delete_urun', raise_exception=True)
def urun_sil(request, urun_id):
    urun = get_object_or_404(Urun, id=urun_id)
    if request.method == "POST":
        urun.delete()
        return redirect('stok_list')

    return render(request, 'urun_sil.html', {'urun': urun})


#ürün güncelleme için
@permission_required('stok_app.change_urun', raise_exception=True)
def urun_guncelle(request, urun_id):
    #print("🚀 urun_guncelle fonksiyonu çalıştı! -> POST mu?", request.method == "POST")

    urun = get_object_or_404(Urun, id=urun_id)
    kullanici = request.user
    kullanici_firma = getattr(kullanici, 'userprofile', None) and kullanici.userprofile.firma  
    eski_barkod = urun.barkod  

    # ✅ Yönetici kontrolü
    kullanici_yonetici_mi = kullanici.groups.filter(name="Yönetici").exists() or kullanici.is_superuser
    #print(f"🔍 Yönetici Kontrolü -> Kullanıcı: {kullanici}, Yönetici Mi?: {kullanici_yonetici_mi}")

    if request.method == "POST":
        form = UrunForm(request.POST, instance=urun)
        
        # **💡 Barkod Çakışma Kontrolünü FORM VALIDASYONU ÖNCESİNDE YAP**
        yeni_barkod = request.POST.get("barkod")  # Formdan gelen barkod
        #print(f"🛠 Yeni Barkod: {yeni_barkod}, Eski Barkod: {eski_barkod}")

        if yeni_barkod != eski_barkod:
            barkod_var = Urun.objects.filter(barkod=yeni_barkod).exclude(id=urun.id).exists()
            #print(f"🔎 Barkod Çakışma Kontrolü: {barkod_var}")  # Terminalde görünecek

            if barkod_var:
                messages.error(request, "⚠️ Bu barkod başka bir ürüne ait! Lütfen farklı bir barkod girin.")
                #print("❌ Barkod çakışması oldu!")  # 🔴 Terminalde görünmeli
                return render(request, "urun_guncelle.html", {  
                    "form": form,
                    "urun": urun,
                    "kullanici_yonetici_mi": kullanici_yonetici_mi
                })

        # **Form validasyonu çalıştır**
        if form.is_valid():
            eski_stok = urun.stok_miktari  
            urun = form.save(commit=False)
            if kullanici_firma:
                urun.firma = kullanici_firma  

            urun.save()

            # 📌 LOG EKLEME
            if kullanici and kullanici_firma:
                Log.objects.create(
                    kullanici=kullanici,
                    firma=kullanici_firma,
                    kategori="ÜRÜN",
                    mesaj=f"Ürün güncellendi: {urun.ad} (Eski Stok: {eski_stok} → Yeni Stok: {urun.stok_miktari})",
                    tarih=now()
                )

            messages.success(request, "✅ Ürün başarıyla güncellendi!")
            return redirect("stok_list")

    else:
        form = UrunForm(instance=urun)
        if not kullanici_yonetici_mi:
            form.fields["barkod"].widget.attrs["readonly"] = True
        else:
            form.fields["barkod"].widget.attrs.pop("readonly", None)

    return render(request, "urun_guncelle.html", {
        "form": form,
        "urun": urun,
        "kullanici_yonetici_mi": kullanici_yonetici_mi
    })













#hatalı giriş için



def yetkisiz_giris(request):
    messages.error(request, "Bu sayfaya erişmek için giriş yapmalısınız!")
    return redirect('login')

#kayıt fonksiyonu

def kayit_ol(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Kullanıcıyı pasif yapıyoruz, admin onaylamalı
            user.save()
            messages.success(request, "Üyeliğiniz admin tarafından onaylandıktan sonra giriş yapabilirsiniz.")
            return redirect("login")  # Kullanıcıyı giriş sayfasına yönlendir
    else:
        form = UserRegisterForm()
    
    return render(request, "registration/signup.html", {"form": form})


from django.db.models.functions import TruncDate
from django.db.models import Sum, Count
import json
# Dashboard şablonu
from django.db.models import Sum, F
from django.db.models.functions import TruncDate
from django.utils.timezone import now
import json

@login_required
def dashboard(request):
    user = request.user

    # Kullanıcının firmasını al
    try:
        user_profile = UserProfile.objects.get(user=user)
        kullanici_firma = user_profile.firma
    except UserProfile.DoesNotExist:
        messages.error(request, "⚠ Kullanıcı profili bulunamadı, lütfen yöneticinize başvurun!")
        return redirect("dashboard")

    today = now().date()

    # 🛒 Bugünkü toplam satışları al (Sadece kendi firmasına ait)
    gunluk_satis_tutari = (
        Satis.objects.filter(satis_tarihi__date=today)
        .filter(urun__firma=kullanici_firma)
        .aggregate(toplam_tutar=Sum(F("satis_adedi") * F("satis_fiyati")))
    )["toplam_tutar"] or 0

    # 🏆 En çok satılan ürünü bul (Sadece kendi firmasına ait)
    en_cok_satan = (
        Satis.objects.filter(urun__firma=kullanici_firma)
        .values("urun__ad")
        .annotate(toplam_satis=Sum("satis_adedi"))
        .order_by("-toplam_satis")
        .first()
    )

    # 📊 Toplam satış sayısı (Sadece kendi firmasına ait)
    toplam_satis_sayisi = Satis.objects.filter(urun__firma=kullanici_firma).count()

    # 🚨 Kritik stokta olan ürünler (Sadece kendi firmasına ait)
    kritik_urunler = Urun.objects.filter(
        firma=kullanici_firma,
        stok_miktari__lte=F("kritik_stok"),
        stok_miktari__gt=0
    )

    # 📊 **Son 7 günün satış trendi** (Sadece kendi firmasına ait)
    satis_trendi = (
        Satis.objects.filter(urun__firma=kullanici_firma, satis_tarihi__gte=today - timedelta(days=7))
        .annotate(tarih=TruncDate("satis_tarihi"))
        .values("tarih")
        .annotate(toplam_satis=Sum(F("satis_adedi") * F("satis_fiyati")))
        .order_by("tarih")
    )

    satis_trendi_labels = [entry["tarih"].strftime("%d/%m") for entry in satis_trendi]
    satis_trendi_data = [float(entry["toplam_satis"]) if entry["toplam_satis"] else 0 for entry in satis_trendi]

    # 🏅 **En Çok Satılan Ürünler (Top 5) (Sadece kendi firmasına ait)**
    en_cok_satan_urunler = (
        Satis.objects.filter(urun__firma=kullanici_firma)
        .values("urun__ad")
        .annotate(toplam_satis=Sum("satis_adedi"))
        .order_by("-toplam_satis")[:5]
    )

    en_cok_satan_labels = [entry["urun__ad"] for entry in en_cok_satan_urunler]
    en_cok_satan_data = [float(entry["toplam_satis"]) for entry in en_cok_satan_urunler]

    return render(request, "dashboard.html", {
        "gunluk_satis_tutari": gunluk_satis_tutari,
        "en_cok_satan": en_cok_satan,
        "toplam_satis_sayisi": toplam_satis_sayisi,
        "kritik_urunler": kritik_urunler,
        "satis_trendi_labels": json.dumps(satis_trendi_labels),
        "satis_trendi_data": json.dumps(satis_trendi_data),
        "en_cok_satan_labels": json.dumps(en_cok_satan_labels),
        "en_cok_satan_data": json.dumps(en_cok_satan_data),
    })


#grafikler
from django.http import JsonResponse
@login_required
def dashboard_data(request):
    # 📅 Son 7 Günlük Satış Verisi
    today = now().date()
    labels = []
    sales_data = []

    for i in range(7):  # Son 7 günü al
        day = today - timedelta(days=i)
        labels.append(day.strftime("%d/%m"))  # Tarihi formatla
        daily_sales = Satis.objects.filter(satis_tarihi__date=day).aggregate(total=Sum('satis_fiyati'))["total"] or 0
        sales_data.append(daily_sales)

    labels.reverse()
    sales_data.reverse()

    # 🔥 En Çok Satan 5 Ürün
    top_products = Satis.objects.values("urun__ad").annotate(total_sold=Sum("satis_adedi")).order_by("-total_sold")[:5]
    product_labels = [urun["urun__ad"] for urun in top_products]
    product_sales = [urun["total_sold"] for urun in top_products]

    return JsonResponse({
        "labels": labels,
        "sales_data": sales_data,
        "product_labels": product_labels,
        "product_sales": product_sales
    })



#üyelik kontrolü

def custom_login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=username, password=password)

            if user is not None:
                if user.is_active:  # Kullanıcı onaylandı mı?
                    login(request, user)
                    return redirect("stok_list")  # Başarılı giriş sonrası yönlendirme
                else:
                    messages.error(request, "Hesabınız henüz admin tarafından onaylanmadı.")
            else:
                messages.error(request, "Geçersiz kullanıcı adı veya şifre.")

    else:
        form = AuthenticationForm()

    return render(request, "registration/login.html", {"form": form})


#satış ekranı 

@login_required
def satis_ekrani(request):
    urunler = Urun.objects.all()  # Satış için stoktaki ürünleri getir

    return render(request, "satis_ekrani.html", {"urunler": urunler})


#kritik stok mail

def kritik_stok_kontrol():
    kritik_urunler = Urun.objects.filter(
        stok_miktari__lte=models.F('kritik_stok'),
        stok_miktari__gt=0
    ).filter(
        models.Q(son_kritik_stok_tarihi__isnull=True) | 
        models.Q(son_kritik_stok_tarihi__lte=now() - timedelta(days=1))  # 1 gün önce bildirilmişse tekrar bildir
    )

    if kritik_urunler.exists():
        konu = "⚠ Kritik Stok Uyarısı"
        mesaj = "Aşağıdaki ürünler kritik stok seviyesine ulaştı:\n\n"
        
        for urun in kritik_urunler:
            mesaj += f"- {urun.ad}: {urun.stok_miktari} adet kaldı (Eşik: {urun.kritik_stok})\n"
            urun.son_kritik_stok_tarihi = now()  # Mail atıldığı için tarih güncellendi
            urun.save()

        yetkili_kullanicilar = User.objects.filter(groups__permissions__codename="view_urun").values_list("email", flat=True)
        mail_listesi = list(set(yetkili_kullanicilar))

        if mail_listesi:
            try:
                send_mail(konu, mesaj, settings.DEFAULT_FROM_EMAIL, mail_listesi)
                print("✅ Kritik stok uyarı maili gönderildi.")
            except Exception as e:
                print(f"❌ Mail gönderme hatası: {e}")





#ürün satış







@login_required
def urun_satis(request, urun_id):
    urun = get_object_or_404(Urun, id=urun_id)

    kullanici = request.user  
    try:
        user_profile = UserProfile.objects.get(user=kullanici)
        kullanici_firma = user_profile.firma  
    except UserProfile.DoesNotExist:
        messages.error(request, "⚠ Kullanıcı profili bulunamadı, lütfen yöneticinizle iletişime geçin!")
        return redirect("stok_list")

    # Kullanıcı yetkisi ve firma doğrulaması
    if not kullanici.is_superuser and urun.firma != kullanici_firma:
        messages.error(request, "🚫 Bu ürünü satmaya yetkiniz yok!")
        return redirect("stok_list")

    # 🔥 **Anonim Müşteri ID'sini bulalım**
    anonim_musteri, created = Musteri.objects.get_or_create(
        firma=kullanici_firma, ad_soyad="Anonim Müşteri",
        defaults={"telefon": "", "email": "", "adres": "Bilinmiyor"}
    )

    if request.method == "POST":
        form = SatisForm(request.POST)
        form.fields["musteri"].queryset = Musteri.objects.filter(firma=kullanici_firma)  # Müşteri listesini güncelle

        if form.is_valid():
            satis_adedi = form.cleaned_data["satis_adedi"]
            satis_fiyati = form.cleaned_data["satis_fiyati"]
            musteri = form.cleaned_data["musteri"]

            # 📌 **Eğer müşteri seçilmezse, varsayılan olarak "Anonim Müşteri"yi kullan**
            if not musteri:
                musteri = anonim_musteri

            if satis_adedi > urun.stok_miktari:
                messages.error(request, f"⚠ Stokta yeterli {urun.ad} yok! Mevcut stok: {urun.stok_miktari}")
                return redirect("stok_list")

            with transaction.atomic():
                satis = Satis.objects.create(
                    urun=urun,
                    musteri=musteri,
                    satis_yapan=kullanici,
                    satis_adedi=satis_adedi,
                    satis_fiyati=satis_fiyati,
                    firma=kullanici_firma
                )

                messages.success(request, f"✅ {musteri.ad_soyad} müşterisine {satis_adedi} adet {urun.ad} satıldı!")
                return redirect("stok_list")
        else:
            hata_mesajlari = " | ".join([f"{field}: {error}" for field, error in form.errors.items()])
            messages.error(request, f"❌ Form hatalı: {hata_mesajlari}")
            print("📌 Form Hataları:", form.errors)

    else:
        form = SatisForm()
        form.fields["musteri"].queryset = Musteri.objects.filter(firma=kullanici_firma)

    return render(request, "satis_ekrani.html", {
        "form": form, 
        "urun": urun,
        "anonim_musteri": anonim_musteri  # 🔥 **HTML tarafında varsayılan müşteri olarak seçilebilir!**
    })










@login_required
def satis_list(request):
    user = request.user

    try:
        kullanici_firma = user.userprofile.firma  # Kullanıcının firması
    except UserProfile.DoesNotExist:
        messages.error(request, "⚠ Kullanıcı profili bulunamadı, lütfen yöneticinize başvurun!")
        return redirect("dashboard")

    # 🔥 **Admin tüm satışları görebilir, diğer kullanıcılar sadece kendi firmasının satışlarını görür**
    satislar = Satis.objects.select_related("urun", "musteri", "satis_yapan").only(
        "satis_tarihi", "satis_adedi", "satis_fiyati", "urun__ad", "musteri__ad_soyad", "satis_yapan__username"
    )

    if not user.is_superuser:
        satislar = satislar.filter(urun__firma=kullanici_firma)
        urunler = Urun.objects.filter(firma=kullanici_firma).order_by("ad")
        musteriler = Musteri.objects.filter(firma=kullanici_firma)
    else:
        urunler = Urun.objects.filter(firma=kullanici_firma).order_by("ad")
        musteriler = Musteri.objects.filter(firma=kullanici_firma)
    # **Filtreleme İşlemi**
    urun = request.GET.get("urun")
    min_tarih = request.GET.get("min_tarih")
    max_tarih = request.GET.get("max_tarih")
    satis_yapan = request.GET.get("satis_yapan")
    musteri = request.GET.get("musteri")

    filtreler = Q()

    if urun:
        filtreler &= Q(urun__id=urun)

    if musteri:
        filtreler &= Q(musteri__id=musteri)

    if min_tarih:
        try:
            min_tarih = datetime.strptime(min_tarih, "%Y-%m-%d")
            filtreler &= Q(satis_tarihi__gte=min_tarih)
        except ValueError:
            messages.error(request, "Geçersiz başlangıç tarihi! Lütfen YYYY-MM-DD formatında giriniz.")
            return redirect("satis_list")

    if max_tarih:
        try:
            max_tarih = datetime.strptime(max_tarih, "%Y-%m-%d") + timedelta(days=1)
            filtreler &= Q(satis_tarihi__lt=max_tarih)
        except ValueError:
            messages.error(request, "Geçersiz bitiş tarihi! Lütfen YYYY-MM-DD formatında giriniz.")
            return redirect("satis_list")

    if satis_yapan:
        filtreler &= Q(satis_yapan__username__icontains=satis_yapan)

    # **Filtreleri uygula**
    satislar = satislar.filter(filtreler)

    return render(request, "satis_list.html", {
        "satislar": satislar,
        "urunler": urunler,
        "musteriler": musteriler,
    })


#müşteri ekleme



def is_manager(user):
    """ Kullanıcının 'Yönetici' grubunda olup olmadığını kontrol eder. """
    return user.is_authenticated and user.groups.filter(name="Yönetici").exists()


@login_required
def musteri_list(request):
    user = request.user

    try:
        kullanici_firma = user.userprofile.firma  # Kullanıcının firmasını al
    except UserProfile.DoesNotExist:
        messages.error(request, "⚠ Kullanıcı profili bulunamadı, lütfen yöneticinize başvurun!")
        return redirect("dashboard")  

    # 🔥 **Admin ise tüm müşterileri görsün, değilse sadece kendi firmasının müşterilerini**
    if user.is_superuser:
        musteriler = Musteri.objects.all()
    else:
        musteriler = Musteri.objects.filter(firma=kullanici_firma)

    can_add_musteri = user.has_perm("stok_app.add_musteri")
    can_change_musteri = user.has_perm("stok_app.change_musteri")
    can_delete_musteri = user.has_perm("stok_app.delete_musteri")

    return render(request, "musteri_list.html", {
        "musteriler": musteriler,
        "can_add_musteri": can_add_musteri,
        "can_change_musteri": can_change_musteri,
        "can_delete_musteri": can_delete_musteri
    })



@login_required
@permission_required('stok_app.add_musteri', raise_exception=True)
def musteri_ekle(request):
    user = request.user

    try:
        kullanici_firma = user.userprofile.firma  # Kullanıcının firmasını al
    except UserProfile.DoesNotExist:
        messages.error(request, "⚠ Kullanıcı profili bulunamadı, lütfen yöneticinize başvurun!")
        return redirect("musteri_list")

    if request.method == "POST":
        form = MusteriForm(request.POST)
        if form.is_valid():
            yeni_musteri = form.save(commit=False)
            if not user.is_superuser:  
                yeni_musteri.firma = kullanici_firma  # Normal kullanıcı sadece kendi firmasına müşteri ekleyebilir
            yeni_musteri.save()
            messages.success(request, f"{yeni_musteri.ad_soyad} başarıyla eklendi!")
            return redirect("musteri_list")
    else:
        form = MusteriForm()

    return render(request, "musteri_ekle.html", {"form": form})


#müşteri sil-düzenle

@login_required
@permission_required('stok_app.change_musteri', raise_exception=True)
def musteri_guncelle(request, musteri_id):
    musteri = get_object_or_404(Musteri, id=musteri_id)
    if request.method == "POST":
        form = MusteriForm(request.POST, instance=musteri)
        if form.is_valid():
            form.save()
            return redirect("musteri_list")
    else:
        form = MusteriForm(instance=musteri)

    return render(request, "musteri_ekle.html", {"form": form})  # Aynı form sayfasını kullanıyoruz


@login_required
@permission_required('stok_app.delete_musteri', raise_exception=True)
def musteri_sil(request, musteri_id):
    musteri = get_object_or_404(Musteri, id=musteri_id)
    if request.method == "POST":
        musteri.delete()
        return redirect("musteri_list")

    return render(request, "musteri_sil.html", {"musteri": musteri})


#toplu satış


from django.utils import timezone  # Saat bilgisini almak için


@login_required
def toplu_satis(request):
    kullanici = request.user
    print(f"👤 Aktif Kullanıcı: {kullanici} (ID: {getattr(kullanici, 'id', None)})")

    try:
        user_profile = UserProfile.objects.get(user=kullanici)
        kullanici_firma = user_profile.firma
    except UserProfile.DoesNotExist:
        messages.error(request, "⚠ Kullanıcı profili bulunamadı, lütfen yöneticinizle iletişime geçin!")
        return redirect("dashboard")

    urunler = Urun.objects.filter(firma=kullanici_firma, stok_miktari__gt=0)
    musteriler = Musteri.objects.filter(firma=kullanici_firma)
    anonim_musteri = Musteri.objects.filter(firma=kullanici_firma, ad_soyad="Anonim Müşteri").first()

    if not anonim_musteri:
        messages.error(request, "⚠ Anonim müşteri bulunamadı! Lütfen yöneticinizle iletişime geçin.")
        return redirect("dashboard")

    if request.method == "POST":
        secili_urunler = request.POST.getlist("secili_urun[]")
        musteri_id = request.POST.get("musteri_id")
        barkod_girilen = request.POST.get("barkod", "").strip()

        print(f"📩 Gelen Form Verileri: {request.POST}")

        if barkod_girilen:
            urun = Urun.objects.filter(barkod=barkod_girilen, firma=kullanici_firma).first()
            if urun:
                secili_urunler.append(str(urun.id))
                print(f"✅ Barkod ile ürün bulundu: {urun.ad}")
            else:
                messages.error(request, f"⚠ Barkod bulunamadı: {barkod_girilen}")
                return redirect("toplu_satis")

        musteri = (
            anonim_musteri if musteri_id == "anonim"
            else get_object_or_404(Musteri, id=musteri_id, firma=kullanici_firma)
        )

        print(f"✅ Seçilen Müşteri: {musteri.ad_soyad}")

        if not secili_urunler:
            messages.error(request, "⚠️ Hiçbir ürün seçilmedi!")
            return redirect("toplu_satis")

        satis_listesi = []
        toplam_satis_fiyati = 0

        with transaction.atomic():
            for urun_id in secili_urunler:
                try:
                    urun = Urun.objects.get(id=urun_id, firma=kullanici_firma)
                except Urun.DoesNotExist:
                    messages.error(request, f"🚫 Ürün bulunamadı: {urun_id}")
                    continue

                adet_str = request.POST.get(f"adet_{urun_id}", "").strip()
                fiyat_str = request.POST.get(f"fiyat_{urun_id}", "").strip()

                try:
                    adet = int(adet_str)
                    if adet <= 0:
                        messages.error(request, f"🚫 {urun.ad} için geçersiz adet girildi!")
                        continue
                except ValueError:
                    messages.error(request, f"🚫 {urun.ad} için geçersiz adet girildi!")
                    continue

                try:
                    fiyat = Decimal(fiyat_str.replace(",", "."))
                    if fiyat <= 0:
                        messages.error(request, f"🚫 {urun.ad} için geçersiz fiyat girildi!")
                        continue
                except Exception:
                    messages.error(request, f"🚫 {urun.ad} için geçersiz fiyat girildi!")
                    continue

                if adet > urun.stok_miktari:
                    messages.error(request, f"🚫 {urun.ad} için stok yetersiz! Maksimum: {urun.stok_miktari}")
                    return redirect("toplu_satis")

                toplam_tutar = fiyat * adet
                if toplam_tutar > Decimal("99999999.99"):
                    messages.error(request, f"🚫 {urun.ad} için toplam tutar fazla! {toplam_tutar}")
                    continue

                try:
                    urun.stok_miktari -= adet
                    urun.save()

                    satis = Satis.objects.create(
                        urun=urun,
                        musteri=musteri,
                        satis_yapan=kullanici,
                        satis_adedi=adet,
                        satis_fiyati=fiyat,
                        firma=kullanici_firma
                    )

                    satis_listesi.append(satis)
                    toplam_satis_fiyati += toplam_tutar

                    Log.objects.create(
                        kullanici=kullanici,
                        firma=kullanici_firma,
                        kategori="ÜRÜN",
                        mesaj=f"{urun.ad} satıldı. Adet: {adet}, Fiyat: {fiyat} ₺",
                        tarih=timezone.now()
                    )
                except Exception as e:
                    messages.error(request, f"⚠ {urun.ad} için satış sırasında hata oluştu: {str(e)}")
                    continue

        if not satis_listesi:
            messages.error(request, "⚠️ Hiçbir satış gerçekleşmedi!")
            return redirect("toplu_satis")

        print("✅ SATIŞ BAŞARIYLA GERÇEKLEŞTİ!")  
        return render(request, "toplu_satis_onay.html", {
            "musteri": musteri,
            "satislar": satis_listesi,
            "toplam_satis_fiyati": toplam_satis_fiyati
        })

    return render(request, "toplu_satis.html", {
        "urunler": urunler,
        "musteriler": musteriler,
        "anonim_musteri": anonim_musteri
    })















#rapor araçları 




def rapor_sonuc(request):
    user = request.user

    # 🔥 Kullanıcının firması olup olmadığını kontrol et
    try:
        kullanici_firma = user.userprofile.firma
    except UserProfile.DoesNotExist:
        messages.error(request, "⚠ Kullanıcı profili bulunamadı, lütfen yöneticinize başvurun!")
        return redirect("dashboard")

    print("📌 Excel için gelen filtreler:", request.GET)

    # **Sadece kullanıcının firmasına ait satışları listele!**
    satislar = Satis.objects.filter(firma=kullanici_firma)
    urunler = Urun.objects.filter(firma=kullanici_firma).order_by("ad")
    musteriler = Musteri.objects.filter(firma=kullanici_firma)

    # 📌 Tarih filtreleme
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    urun = request.GET.get("urun")
    musteri = request.GET.get("musteri")

    if start_date:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            satislar = satislar.filter(satis_tarihi__gte=start_date)
        except ValueError:
            messages.error(request, "Geçersiz başlangıç tarihi! Lütfen YYYY-MM-DD formatında giriniz.")
            return redirect("rapor_sonuc")

    if end_date:
        try:
            end_date = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            satislar = satislar.filter(satis_tarihi__lt=end_date)
        except ValueError:
            messages.error(request, "Geçersiz bitiş tarihi! Lütfen YYYY-MM-DD formatında giriniz.")
            return redirect("rapor_sonuc")

    # 📌 Ürün ve müşteri filtreleme (Firma bazlı!)
    if urun:
        satislar = satislar.filter(urun__id=urun, urun__firma=kullanici_firma)

    if musteri:
        satislar = satislar.filter(musteri__id=musteri, musteri__firma=kullanici_firma)

    # **Toplam Tutar (Ürün Fiyatı × Satış Adedi)**
    genel_toplam_tutar = sum(float(satis.satis_fiyati) * float(satis.satis_adedi) for satis in satislar)

    # ✅ **Filtrelenmiş veriyi JSON uyumlu hale getir (Decimal sorunu giderildi)**
    satislar_list = [
        {
            "satis_tarihi": satis.satis_tarihi.strftime("%Y-%m-%d %H:%M:%S") if satis.satis_tarihi else None,
            "urun_ad": satis.urun.ad if satis.urun else "Bilinmeyen Ürün",
            "musteri_ad": satis.musteri.ad_soyad if satis.musteri else "Bilinmeyen Müşteri",
            "satis_adedi": int(satis.satis_adedi),
            "satis_fiyati": float(satis.satis_fiyati),
            "toplam_tutar": float(satis.satis_fiyati * satis.satis_adedi)
        }
        for satis in satislar
    ]

    # ✅ **SESSION'A JSON VERİYİ KAYDET (Decimal hatası fixlendi)**
    request.session['filtrelenmis_satislar'] = satislar_list

    print("🚀 Raporlama verisi başarıyla işlendi!")

    return render(request, "raporlama.html", {
        "satislar": satislar,
        "urunler": urunler,
        "musteriler": musteriler,
        "genel_toplam_tutar": genel_toplam_tutar
    })








import csv
from datetime import datetime
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import os


def excel_rapor(request):
    satislar = request.session.get('filtrelenmis_satislar', [])

    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    response['Content-Disposition'] = 'attachment; filename="satis_raporu.csv"'

    writer = csv.writer(response, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    
    # ✅ Başlıklar
    writer.writerow(["Tarih", "Ürün", "Müşteri", "Adet", "Birim Fiyat", "Toplam Tutar"]) 

    genel_toplam = 0  # Genel toplam hesaplamak için değişken

    for satis in satislar:
        toplam_tutar = satis["satis_adedi"] * satis["satis_fiyati"]
        genel_toplam += toplam_tutar  # Genel toplama ekle
        
        writer.writerow([
            satis["satis_tarihi"] if satis["satis_tarihi"] else "Bilinmiyor",
            satis["urun_ad"],
            satis["musteri_ad"],
            satis["satis_adedi"],
            satis["satis_fiyati"],
            f"{toplam_tutar:.2f} ₺"
        ])

    # ✅ Genel toplam satırı ekleyelim
    writer.writerow(["", "", "", "", "Genel Toplam", f"{genel_toplam:.2f} ₺"])

    return response


def pdf_rapor(request):
    satislar = request.session.get('filtrelenmis_satislar', [])

    if not satislar:
        return HttpResponse("Filtrelenmiş veri bulunamadı!", status=400)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="satis_raporu.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []

    # ✅ Windows’ta Arial Unicode MS yoksa Arial kullan
    font_path = "C:/Windows/Fonts/arial.ttf"  # Arial varsayılan font
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont("Arial", font_path))
        font_name = "Arial"
    else:
        font_name = "Helvetica"  # Font bulunmazsa Helvetica'ya düş

    # ✅ Tablo Başlıkları
    data = [
        ["Tarih", "Ürün", "Müşteri", "Adet", "Birim Fiyat", "Toplam Tutar"]
    ]

    genel_toplam = 0  # Genel toplam hesaplamak için değişken

    for satis in satislar:
        toplam_tutar = satis.get("satis_adedi", 0) * satis.get("satis_fiyati", 0)
        genel_toplam += toplam_tutar  # Genel toplama ekle

        data.append([
            satis.get("satis_tarihi", "Bilinmiyor"),
            satis.get("urun_ad", "Bilinmeyen Ürün"),
            satis.get("musteri_ad", "Bilinmeyen Müşteri"),
            str(satis.get("satis_adedi", "0")),
            f"{satis.get('satis_fiyati', '0'):.2f} ₺",
            f"{toplam_tutar:.2f} ₺"
        ])

    # ✅ Genel Toplam Satırını Ekleyelim
    data.append(["", "", "", "", "Genel Toplam", f"{genel_toplam:.2f} ₺"])

    table = Table(data)
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), font_name),  # ✅ Fontu uygula
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('TEXTCOLOR', (-2, -1), (-1, -1), colors.red),  # Genel Toplam kırmızı olsun
    ]))

    elements.append(table)
    doc.build(elements)

    return response



#excel aktarımı 
import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from .models import Urun  # Ürün modelini içe aktar


@login_required
def excelden_urun_ekle(request):
    print("📂 Dosya alındı, pandas okumaya başladı...")

    if request.method == "POST":
        print("✅ POST Metodu Geldi")
        if request.FILES.get("file"):
            print("✅ Dosya Yükleme Başladı")

            try:
                df = pd.read_excel(request.FILES["file"])

                if df.empty:
                    print("🚨 HATA: Excel dosyası boş veya sütun isimleri hatalı!")
                    messages.error(request, "Excel dosyasında veri bulunamadı!")
                    return redirect("urun_yukle")

                print("📜 Excel İçeriği:\n", df.to_string(index=False))

                kullanici = request.user
                kullanici_firma = kullanici.userprofile.firma if hasattr(kullanici, 'userprofile') else None

                if not kullanici or not kullanici_firma:
                    print("🚨 Kullanıcı veya firma bilgisi eksik, işlem iptal ediliyor!")
                    messages.error(request, "Firma veya kullanıcı bilgisi bulunamadı!")
                    return redirect("urun_yukle")

                print(f"👤 Kullanıcı: {kullanici}, 🏢 Firma: {kullanici_firma}")

                yeni_urun_sayisi = 0
                guncellenen_urun_sayisi = 0

                print("🔄 **Döngü Başlıyor...**")

                with transaction.atomic():
                    for index, row in df.iterrows():
                        print(f"➡ **İşlenen Satır {index}:** {row.to_dict()}")

                        ad = str(row["ad"]).strip()
                        kategori = str(row["kategori"]).strip()
                        birim = str(row["birim"]).strip()
                        fiyat = float(row["fiyat"])
                        yeni_stok = int(row["stok_miktari"])
                        kritik_stok = int(row["kritik_stok"])

                        # ✅ **Barkod Kolonunu Kontrol Et**
                        barkod = str(row["barkod"]).strip() if "barkod" in row and pd.notna(row["barkod"]) else None

                        if barkod:
                            # 🔍 Aynı barkod zaten varsa hata ver!
                            if Urun.objects.filter(barkod=barkod, firma=kullanici_firma).exists():
                                print(f"🚨 HATA: {barkod} barkodu zaten mevcut!")
                                messages.error(request, f"Barkod çakışması: {barkod}")
                                continue
                        else:
                            # 🔄 Barkod yoksa, **random** 12 haneli barkod oluştur
                            barkod = str(uuid.uuid4().int)[:12]
                            while Urun.objects.filter(barkod=barkod).exists():
                                barkod = str(uuid.uuid4().int)[:12]
                            print(f"🔄 Yeni barkod oluşturuldu: {barkod}")

                        mevcut_urun = Urun.objects.filter(
                            ad__iexact=ad,
                            kategori__iexact=kategori,
                            birim__iexact=birim,
                            fiyat=fiyat,
                            firma=kullanici_firma
                        ).first()

                        if mevcut_urun:
                            mevcut_urun.stok_miktari += yeni_stok
                            mevcut_urun.save()
                            guncellenen_urun_sayisi += 1
                        else:
                            Urun.objects.create(
                                ad=ad,
                                kategori=kategori,
                                stok_miktari=yeni_stok,
                                birim=birim,
                                fiyat=fiyat,
                                kritik_stok=kritik_stok,
                                barkod=barkod,  # ✅ Barkodu ekledik!
                                firma=kullanici_firma,
                                kullanici=kullanici
                            )
                            yeni_urun_sayisi += 1

                        # LOG EKLEME
                        print(f"📌 LOG EKLENİYOR: Kullanıcı -> {kullanici}, Firma -> {kullanici_firma}")

                        Log.objects.create(
                            kullanici=kullanici,
                            firma=kullanici_firma,
                            kategori="ÜRÜN",
                            mesaj=f"Yeni ürün eklendi: {ad} (Stok: {yeni_stok}) - Barkod: {barkod}",
                            tarih=now()
                        )

                print("✅ **Döngü tamamlandı.**")
                messages.success(request, f"✅ {yeni_urun_sayisi} yeni ürün eklendi, {guncellenen_urun_sayisi} ürün güncellendi.")

            except Exception as e:
                print(f"❌ **Hata Detayı:** {e}")
                messages.error(request, f"Hata oluştu: {e}")

            return redirect("urun_yukle")

        else:
            print("🚨 Dosya yüklenmedi veya request.FILES['file'] verisi boş!")
            messages.error(request, "Lütfen dosya seçin!")
            return redirect("urun_yukle")

    print("❌ POST Metodu Gelmedi - Sayfa Normal Yüklendi")
    return render(request, "urun_yukle.html")






#örnek excel
from io import BytesIO

import pandas as pd
from io import BytesIO
from django.http import HttpResponse

def ornek_excel_indir(request):
    # 📌 Örnek verileri içeren DataFrame
    data = {
        "ad": ["Örnek Ürün"],
        "kategori": ["Örnek Kategori"],
        "stok_miktari": [100],
        "birim": ["Adet"],
        "fiyat": [50.0],
        "kritik_stok": [10],
        "barkod": ["Opsiyonel - Elle Girilebilir"]  # ✅ Barkod Alanı Eklendi
    }
    
    df = pd.DataFrame(data)

    # 📝 Excel dosyasını hafızaya yaz
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Ürün Şablonu")

    # 📥 HTTP yanıtı olarak Excel dosyasını döndür
    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="urun_sablonu.xlsx"'
    return response



#loglar Kayıtları

@login_required
def log_list(request):
    user = request.user
    try:
        kullanici_firma = user.userprofile.firma
    except:
        messages.error(request, "⚠ Kullanıcı profili bulunamadı!")
        return redirect("dashboard")

    # 🔥 Kullanıcı sadece kendi firmasına ait logları görebilsin
    loglar = Log.objects.filter(firma=kullanici_firma).order_by("-tarih")

    return render(request, "log_list.html", {"loglar": loglar})




def robots_txt(request):
    robots_path = os.path.join(settings.BASE_DIR, 'robots.txt')
    with open(robots_path, 'r') as f:
        content = f.read()
    return HttpResponse(content, content_type="text/plain")


























