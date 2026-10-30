"""
Django settings for bloodbank project.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# SECRET_KEY, DEBUG and ALLOWED_HOSTS now come from the environment so the
# same settings module works for every teammate's machine and for CI without
# anyone editing this file or committing a real secret. The literals below
# are development-only fallbacks (the key is the original Sprint 1 dev key,
# publicly visible in git history already, so rotating it is not treated as
# a security fix -- see .env.example and README.md "Environment setup").
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-q4sadma(88nk8kjx*s#_@1us)t83n41y9=hbnl$^6b*!v6n!a0",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"

ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",") if h.strip()
]


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'inventory',
    'requests',
    'authentication',
    'donors',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'bloodbank.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Project-level templates/ holds the shared design system (base.html)
        # that every app's templates extend, so the nav, logout control and
        # styling are defined once instead of separately per app.
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'bloodbank.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


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


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


STATIC_URL = 'static/'


MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}


# Authentication (BBMS-F-001, BBMS-F-002, BBMS-SR-001)
# Django's built-in session authentication; unauthenticated requests to
# @login_required views are redirected to LOGIN_URL.
LOGIN_URL = 'authentication:login'
LOGIN_REDIRECT_URL = 'authentication:home'
LOGOUT_REDIRECT_URL = 'authentication:login'


# BBMS-52 / BBMS-SR-003: HTTPS security settings, enabled when DEBUG=False
# in the deployment environment. Restored here -- these were added to main
# in e61fdc6 ("Add HTTPS security settings") but did not survive the
# Sprint 2 donor-management merge (PR #10), which replaced this file
# wholesale with a version branched before e61fdc6 existed. See
# docs/KNOWN_ISSUES.md for how that happened.
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
