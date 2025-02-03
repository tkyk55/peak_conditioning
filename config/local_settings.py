# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-2rw_v7drbp023as4m*8lj6^q50ldszis@qe$988+j@eduoo7wg'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

EMAIL_HOST = 'mail.mgtk.net'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'tanaka@mgtk.net'
EMAIL_HOST_PASSWORD = '156278921!'
EMAIL_USE_TLS = True

DATABASES = {
    #'default': {
    #    'ENGINE': 'django.db.backends.sqlite3',
    #    'NAME': BASE_DIR / 'db.sqlite3',
    #}

    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'mgtk_peak_dev',
        'USER': 'peak_dev',
        'PASSWORD': 'zxasqw21!!',
        'HOST': '124.147.10.133',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}
