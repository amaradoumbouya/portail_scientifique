from pathlib import Path
import os
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-+&5yqc!(q^il$#523z#01w=w!vosyjzoxy_lb4(h-)*a5!qn76'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["portailscientifique.crict.edu.gn","127.0.0.1","localhost",]

CSRF_TRUSTED_ORIGINS = [
    "http://portailscientifique.crict.edu.gn",
    "https://portailscientifique.crict.edu.gn",
]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'crispy_forms',
    'crispy_bootstrap5',

    'accounts',
    'auteurs',
    'indexations',
    'institutions',
    'portail_site',
    'publications',
    'statistiques',
    'types_document',
    'notifications',
    'newsletters',
    'contact_us',
    'encadreurs',
    'partenaires',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Middleware ci-dessous a été ajouté par Amara DOUMBOUYA
    'middlewares.portail_middleware.PortailMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR/'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        "NAME": os.getenv("DB_NAME", "portail_db"),
        "USER": os.getenv("DB_USER", "portail_user"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
	"HOST": os.getenv("DB_HOST", "db"),
	"PORT": os.getenv("DB_PORT", "3306"),
	"OPTIONS": {"init_command": "SET sql_mode='STRICT_TRANS_TABLES'"},
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'fr-fr'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR/'static'
#STATICFILES_DIRS = [BASE_DIR/'static']
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR/'media/'
LOGIN_REDIRECT_URL = 'accounts:profil_user'
LOGOUT_REDIRECT_URL ='portail_site:connexion'
AUTH_USER_MODEL = 'accounts.CustumerUser'
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CONFIGURATION SUPREMECLUSTER POUR NOTRE DOMAINE
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.supremecluster.com'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False
EMAIL_HOST_USER = "contact@portailscientifique.crict.edu.gn"
EMAIL_HOST_PASSWORD = "ozm763GIB#"
DEFAULT_FROM_EMAIL = f"CRICT<{EMAIL_HOST_USER}>"
SERVER_EMAIL = EMAIL_HOST_USER
EMAIL_TIMEOUT = 10
