from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv()

DEBUG = os.getenv("DEBUG", "False") == "True"
SECRET_KEY = os.getenv("SECRET_KEY", "değiştir-bunu")

ALLOWED_HOSTS = ["127.0.0.1", "localhost", "stok-takip-454309.ew.r.appspot.com",'stokapp.tech', 'www.stokapp.tech']
CSRF_TRUSTED_ORIGINS = ["https://stok-takip-454309.ew.r.appspot.com",'https://stokapp.tech', 'https://www.stokapp.tech']

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

if os.getenv("GAE_APPLICATION", None):
    DEBUG = False
    STATICFILES_STORAGE ='django.contrib.staticfiles.storage.StaticFilesStorage' #'storages.backends.gcloud.GoogleCloudStorage'
    GS_BUCKET_NAME = 'stok-takip-454309.appspot.com'
    #DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
else:
    DEBUG = True
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'




CSP_DEFAULT_SRC = (
    "'self'",
    "https://cdn.jsdelivr.net",
    "https://storage.googleapis.com",
    "https://storage.googleapis.com/stok-takip-454309.appspot.com",
)

CSP_STYLE_SRC = [
    "'self'",
    "'unsafe-inline'",
    "https://fonts.googleapis.com",
    "https://cdn.jsdelivr.net",
    "https://cdn.jsdelivr.net/npm/chart.js",
    "https://storage.googleapis.com",
    "https://storage.googleapis.com/stok-takip-454309.appspot.com",
    "https://storage.googleapis.com/stok-takip-454309.appspot.com/static/stok_app/css/",
    "https://storage.googleapis.com/stok-takip-454309.appspot.com/static/admin/css/",
]

CSP_SCRIPT_SRC = [
    "'self'",
    "'unsafe-inline'",
    
    "https://apis.google.com",
    "https://cdn.jsdelivr.net",  # <-- Chart.js gibi kütüphaneler için
    "https://cdn.jsdelivr.net/npm/chart.js",
    "https://storage.googleapis.com",
    "https://storage.googleapis.com/stok-takip-454309.appspot.com",
    "https://storage.googleapis.com/stok-takip-454309.appspot.com/static/stok_app/css/js/",
    "https://storage.googleapis.com/stok-takip-454309.appspot.com/static/admin/js/",
    
]

CSP_IMG_SRC = [
    "'self'",
    "data:",
    "https://storage.googleapis.com",
    "https://storage.googleapis.com/stok-takip-454309.appspot.com",
    "https://storage.googleapis.com/stok-takip-454309.appspot.com/static/stok_app/",
    "https://storage.googleapis.com/stok-takip-454309.appspot.com/static/admin/img/",
]

CSP_FONT_SRC = [
    "'self'",
    "https://fonts.gstatic.com",
]

CSP_CONNECT_SRC = [
    "'self'",
    "https://stok-takip-454309.ew.r.appspot.com",
    "https://stokapp.tech",
    "https://www.stokapp.tech",
]

CSP_SCRIPT_SRC_ELEM = CSP_SCRIPT_SRC
CSP_STYLE_SRC_ELEM = CSP_STYLE_SRC


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'storages',
    'csp',
    'stok_app',
]

MIDDLEWARE = [
    #'stok_takip.middleware.AdminStaticFixMiddleware', 
    'django.middleware.security.SecurityMiddleware',
    'csp.middleware.CSPMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
]

ROOT_URLCONF = 'stok_takip.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'stok_takip.wsgi.application'

if os.getenv("GAE_APPLICATION", None):
    DB_HOST ="/cloudsql/stok-takip-454309:europe-west1:stoktakip-db"
else:
    DB_HOST = os.getenv("DB_HOST")  # local ip

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST':os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'tr-tr'
TIME_ZONE = 'Europe/Istanbul'
USE_I18N = True
USE_TZ = True




STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'stok_app', 'static'),  # Sonunda / olmadan
]



DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'

GS_BUCKET_NAME = 'stok-takip-454309.appspot.com'  # Otomatik oluşan bucket adı
GS_DEFAULT_ACL = 'publicRead'
#STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_REDIRECT_URL = '/dashboard/'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")

MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
