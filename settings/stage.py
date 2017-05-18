from twido.settings import *
from django.utils.translation import ugettext_lazy as _

print('stage settings')
DEBUG = False

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Shanghai'

# DATABASES['mysql'] = {
#     'ENGINE': 'django.db.backends.mysql',
#     'NAME': 'twido',
#     'USER': 'twido',
#     'PASSWORD': 'passw0rd',
#     'HOST': '	591a8bac782c1.gz.cdb.myqcloud.com',
#     'PORT': '14948',
# }

INSTALLED_APPS.extend([
    # 'gunicorn',
])

CONFIG_FILE = os.getenv('CONFIG_FILE', 'config.sam.ini')

