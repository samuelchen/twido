"""
Django settings for twido project.

Generated by 'django-admin startproject' using Django 1.10.6.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'yh$&9t4@dq_6d7n@ey!dsl_t@b14*^rpbn^(=+*+^wi-e(x09e'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True if __debug__ else False
# DEBUG = False
if DEBUG:
    print('--- DEBUG MODE ---')


ALLOWED_HOSTS = [] if not DEBUG else ['192.168.0.*', 'localhost', '127.0.0.1', 'mwl2.com']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'bootstrap_themes',
    # 'bootstrapform',
    'twido',
    # 'user',
    # 'simple_email_confirmation',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'twido.middleware.RequestProfileMiddleWare',
]

ROOT_URLCONF = 'twido.urls'

CONTEXT_PROCESSORS = [
    'django.template.context_processors.debug',
    'django.template.context_processors.request',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': CONTEXT_PROCESSORS,
        },
    },

    # {
    #     # 'BACKEND': 'django.template.backends.django.DjangoTemplates',
    #     'BACKEND': 'django.template.backends.jinja2.Jinja2',
    #     'DIRS': [],
    #     'APP_DIRS': True,
    #     'OPTIONS': {
    #         'environment': 'twido.jinja2env.environment',
    #         'context_processors': CONTEXT_PROCESSORS,
    #     },
    # },
]

WSGI_APPLICATION = 'twido.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = '/static/'


# ----- added settings -----

LOGIN_URL = '/login/'
LOGOUT_REDIRECT_URL = '/'


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


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)-8s [%(asctime)s] [%(process)-6d] [%(threadName)-8s] %(name)-30s [%(lineno)d] %(message)s'
        },
        'simple': {
            'format': '%(levelname)-8s [%(asctime)s] %(name)-30s [%(lineno)d] %(message)s'
        },
        # 'colored': {
        #     'format': '%(levelname)-8s [%(asctime)s] %(name)s.%(funcName)s [%(lineno)d] %(message)s',
        #     # color reference: https://pypi.python.org/pypi/termcolor
        #     # 'LEVEL': ('fg-color', 'bg-color', ['attr1', 'attr2', ...])
        #     '()': 'pyutils.logger.ColorFormatter',
        #     'colors': {
        #         'TRACE': ('grey', None, []),
        #         'DEBUG': ('grey', None, ['bold']),
        #         'INFO': (None, None, []),
        #         'WARNING': ('yellow', None, []),
        #         'ERROR': ('red', None, []),
        #         'CRITICAL': ('red', 'white', []),
        #
        #     }
        # },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'twido': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'WARNING',
        },
        'services': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'WARNING',
        },
        'tweepy': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'WARNING',
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'ERROR',
        },
    },
}


CONFIG_FILE = os.getenv('CONFIG_FILE', 'config.ini')