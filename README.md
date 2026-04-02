# StokTakip

**StokTakip**, küçük ve orta ölçekli işletmeler için geliştirilmiş, çok kiracılı (multi-tenant) bir stok ve satış yönetim platformudur. Django ile geliştirilmiş olup Google Cloud App Engine üzerinde production ortamında yayınlanmıştır.

> 🌐 Canlı Demo: [stokapp.tech](https://stokapp.tech)

---

## 🚀 Özellikler

- **Çok Kiracılı Yapı (Multi-Tenant)** — Her firma kendi verisini izole olarak yönetir
- **Ürün & Stok Yönetimi** — Otomatik barkod üretimi, kritik stok uyarıları
- **Satış Yönetimi** — Satış anında stok otomatik düşümü, yetersiz stok validation
- **Müşteri Yönetimi** — Firma bazlı müşteri takibi
- **Granüler Yetki Sistemi** — Kullanıcı bazlı ürün ekleme/düzenleme/silme izinleri
- **Audit Logging** — Tüm işlemler kullanıcı ve kategori bazlı loglanır
- **Dashboard & Grafikler** — Matplotlib ile satış ve stok analizleri
- **PDF & Excel Export** — ReportLab ve openpyxl ile rapor üretimi
- **Mobil Uyumlu** — Responsive tasarım
- **E-posta Bildirimleri** — Kritik stok ve sistem bildirimleri

---

## ⚙️ Teknoloji Stack

| Katman | Teknoloji |
|---|---|
| Framework | Django 4.2 |
| Veritabanı | PostgreSQL (Google Cloud SQL) |
| Dosya Depolama | Google Cloud Storage |
| Deployment | Google Cloud App Engine |
| Raporlama | ReportLab, openpyxl, Matplotlib |
| Veri Analizi | Pandas, NumPy |
| Güvenlik | Django CSP, python-dotenv |
| Production Server | Gunicorn |

---

## 🏗️ Mimari

```
StokTakip/
├── stok_app/
│   ├── models.py       # Firma, Urun, Musteri, Satis, UserProfile, Log
│   ├── views.py        # Dashboard, stok, satış, müşteri, yetki view'ları
│   ├── urls.py
│   ├── templates/      # Mobil uyumlu HTML şablonları
│   └── static/         # CSS, JS
├── stok_takip/
│   ├── settings.py     # Environment variable tabanlı konfigürasyon
│   └── urls.py
├── app.yaml            # Google Cloud App Engine konfigürasyonu
└── requirements.txt
```

---

## 🔑 Domain Modeli

| Model | Açıklama |
|---|---|
| `Firma` | Multi-tenant yapının temel birimi |
| `Urun` | Otomatik barkod, kritik stok seviyesi |
| `Musteri` | Firma bazlı müşteri yönetimi |
| `Satis` | Otomatik stok düşümü, validation |
| `UserProfile` | Granüler yetki yönetimi |
| `Log` | Audit trail — tüm işlemler loglanır |

---

## 🚀 Kurulum

### Gereksinimler
- Python 3.11+
- PostgreSQL

### 1. Repoyu klonla

```bash
git clone https://github.com/Mebeser/stok-takip.git
cd stok-takip
```

### 2. Virtual environment oluştur

```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

### 3. Bağımlılıkları yükle

```bash
pip install -r requirements.txt
```

### 4. `.env` dosyası oluştur

```env
SECRET_KEY=your-secret-key
DB_NAME=stoktakip
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432
```

### 5. Migration'ları uygula

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

---

## ☁️ Production Deploy

Uygulama **Google Cloud App Engine** üzerinde deploy edilmiştir:

```bash
gcloud app deploy
```

- Statik dosyalar: Google Cloud Storage
- Veritabanı: Google Cloud SQL (PostgreSQL)
- Domain: stokapp.tech

---

## 📄 Lisans

MIT
