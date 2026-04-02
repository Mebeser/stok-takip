from django.urls import path
from .views import stok_list, urun_ekle, urun_guncelle, urun_sil, kayit_ol,satis_ekrani,urun_satis,satis_list,musteri_ekle,musteri_list,musteri_guncelle,musteri_sil,toplu_satis,log_list
from .views import rapor_sonuc,excel_rapor,pdf_rapor,excelden_urun_ekle,ornek_excel_indir
from stok_app.views import dashboard,dashboard_data  # Dashboard view'ini çağırıyoruz
from django.contrib.auth.views import LogoutView
urlpatterns = [
    path('', stok_list, name='stok_list'),
    path('urun-ekle/', urun_ekle, name='urun_ekle'),
    path('urun-guncelle/<int:urun_id>/', urun_guncelle, name='urun_guncelle'),
    path('urun-sil/<int:urun_id>/', urun_sil, name='urun_sil'),
    path('signup/', kayit_ol, name='signup'),
    path('dashboard/', dashboard, name='dashboard'),  # Yeni URL
    path('satis-ekrani/', satis_ekrani, name='satis_ekrani'),
    path('urun-satis/<int:urun_id>/', urun_satis, name='urun_satis'),
    path('satislar/', satis_list, name='satis_list'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path("musteriler/", musteri_list, name="musteri_list"),
    path("musteri_ekle/", musteri_ekle, name="musteri_ekle"),
    path("musteri-guncelle/<int:musteri_id>/", musteri_guncelle, name="musteri_guncelle"),
    path("musteri-sil/<int:musteri_id>/", musteri_sil, name="musteri_sil"),
    path('toplu-satis/', toplu_satis, name='toplu_satis'),  # Toplu satış için yeni route
    path('raporlama/', rapor_sonuc, name='rapor_sonuc'),
    path('rapor/excel/', excel_rapor, name='excel_rapor'),
    path('rapor/pdf/', pdf_rapor, name='pdf_rapor'),
    path("dashboard-data/", dashboard_data, name="dashboard_data"),
    path('urun-yukle/', excelden_urun_ekle, name='urun_yukle'),
    path("ornek-excel-indir/", ornek_excel_indir, name="ornek_excel_indir"),
    path("loglar/", log_list, name="log_list"),
]