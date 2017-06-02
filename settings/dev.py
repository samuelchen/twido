from twido.settings import *
from django.utils.translation import ugettext_lazy as _

print('dev settings')
DEBUG = True if __debug__ and os.getenv('TWIDO_DEBUG') else False

# STATIC_ROOT = '/home/samuel/static'
MEDIA_ROOT = './media'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Shanghai'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

INSTALLED_APPS.extend([
    # 'gunicorn',
    'account'
])

# AUTH_USER_MODEL = 'account.User'

WEBSITE_NAME = _('MWL')

CONFIG_FILE = os.getenv('CONFIG_FILE', 'config.sam.ini')

INTERNAL_IPS = ['127.0.0.1', 'localhost', '192.168.0.*']
# TEMPLATE_DEBUG = False
# if DEBUG:
#     INSTALLED_APPS.append('debug_toolbar')
#     MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')
#     # TEMPLATE_DEBUG = True
#     INTERNAL_IPS = ['127.0.0.1', 'localhost', '192.168.0.*']
#
# DEBUG_TOOLBAR_PANELS = [
#     'debug_toolbar.panels.versions.VersionsPanel',
#     'debug_toolbar.panels.timer.TimerPanel',
#     'debug_toolbar.panels.settings.SettingsPanel',
#     'debug_toolbar.panels.headers.HeadersPanel',
#     'debug_toolbar.panels.request.RequestPanel',
#     'debug_toolbar.panels.sql.SQLPanel',
#     'debug_toolbar.panels.staticfiles.StaticFilesPanel',
#     'debug_toolbar.panels.templates.TemplatesPanel',
#     'debug_toolbar.panels.cache.CachePanel',
#     'debug_toolbar.panels.signals.SignalsPanel',
#     'debug_toolbar.panels.logging.LoggingPanel',
#     'debug_toolbar.panels.redirects.RedirectsPanel',
# ]
