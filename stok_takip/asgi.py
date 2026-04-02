"""
ASGI config for stok_takip project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
#from whitenoise import WhiteNoise

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stok_takip.settings")

application = get_asgi_application()
#application = WhiteNoise(application)
