from twido.settings import *
from django.utils.translation import ugettext_lazy as _

print('prod settings')

DEBUG = False
SECRET_KEY = 'askojdfpoasdhfu98sdyf792ylJ^*%&%$wdfjj2oie29u3y29'

WEBSITE_NAME = _('My Wonderful Life 2')

STATIC_ROOT = '/srv/twido/static'
MEDIA_ROOT = '/srv/twido/media'

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Shanghai'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
