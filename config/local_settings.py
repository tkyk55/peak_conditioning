# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-2rw_v7drbp023as4m*8lj6^q50ldszis@qe$988+j@eduoo7wg'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    #'default': {
    #    'ENGINE': 'django.db.backends.sqlite3',
    #    'NAME': BASE_DIR / 'db.sqlite3',
    #}

    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'mgtk_peakconditioning',
        'USER': 'tkyk55',
        'PASSWORD': 'zxasqw21Z!',
        'HOST': '124.147.10.133',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}
