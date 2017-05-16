from .base import *

print('prod settings')
DEBUG = False
SECRET_KEY = 'askojdfpoasdhfu98sdyf792ylJ^*%&%$wdfjj2oie29u3y29'

STATIC_ROOT = '/var/www/static'
MEDIA_ROOT = '/var/www/media'

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Shanghai'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

INSTALLED_APPS.extend([
    'gunicorn',
])

CONFIG_FILE = os.getenv('CONFIG_FILE', 'config.ini')