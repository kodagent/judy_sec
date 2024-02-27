import django_on_heroku

from .base import *

DEBUG = False
ALLOWED_HOSTS = ["*"]


# ================================ DATABASES =======================================
DATABASES = {"default": dj_database_url.parse(config("DATABASE_URL"))}
# # DATABASES["default"]["OPTIONS"] = {"sslmode": "require"}

# DATABASES = {
#     "default": dj_database_url.config(default="sqlite:///db.sqlite3", conn_max_age=600)
# }
# ================================ DATABASES =======================================


# ================================ STORAGES =======================================
# ==> AMAZON S3 SETTINGS
AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME")
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age-86400"}
AWS_LOCATION = "static"
AWS_QUERYSTRING_AUTH = False
AWS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
}

# ==> MEDIA FILE UPLOADS
PUBLIC_MEDIA_LOCATION = "media"
MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/{PUBLIC_MEDIA_LOCATION}/"
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
# DEFAULT_FILE_STORAGE = "chatbackend.storage_backends.MediaStorage"

# ==> STATIC FILE UPLOADS
STATICFILES_STORAGE = "storages.backends.s3boto3.S3StaticStorage"
STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/"
# ================================ STORAGES =======================================


# ================================ PAYSTACK =======================================
# PAYSTACK_PUBLIC_KEY=config("PAYSTACK_LIVE_PUBLIC_KEY")
# PAYSTACK_SECRET_KEY=config("PAYSTACK_LIVE_SECRET_KEY")
# ================================ PAYSTACK =======================================


# ================================ EMAIL =======================================
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# EMAIL_HOST = 'smtp.office365.com'  # 'smtp.outlook.office365.com'
# EMAIL_PORT = 587  # 465  # TLS port
# EMAIL_USE_TLS = True
# # EMAIL_USE_SSL = True
# EMAIL_HOST_USER = config("EMAIL")
# EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
# DEFAULT_FROM_EMAIL = config("EMAIL")
# ================================ EMAIL =======================================


# ================================ REDIS/CHANNELS =======================================
# CACHES = {
#     "default": {
#         "BACKEND": "django_redis.cache.RedisCache",
#         "LOCATION": config("REDIS_URL"),
#         "OPTIONS": {
#             "CLIENT_CLASS": "django_redis.client.DefaultClient",
#         }
#     }
# }
default_channel_layer = {
    "BACKEND": "channels_redis.core.RedisChannelLayer",
    "CONFIG": {
        "hosts": [config("REDIS_URL")],  # , 'redis://127.0.0.1:6379')],
    },
}
CHANNEL_LAYERS = {"default": default_channel_layer}
# ================================ REDIS =======================================


# ================================ HEROKU =======================================
# # ==> HEROKU LOGGING
# DEBUG_PROPAGATE_EXCEPTIONS = True
# LOGGING = {
#     "version": 1,
#     "disable_existing_loggers": False,
#     "formatters": {
#         "verbose": {
#             "format": "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
#             "datefmt": "%d/%b/%Y %H:%M:%S",
#         },
#         "simple": {
#             "format": "[%(asctime)s] %(levelname)s %(message)s",
#         },
#     },
#     "handlers": {
#         "console": {
#             "level": "DEBUG",
#             "class": "logging.StreamHandler"
#         }
#     },
#     "loggers": {
#         "dfxapp": {
#             "handlers": ["console"],
#             "level": "INFO",
#         },
#     },
# }

# # ==> HEROKU DATABASE
# django_on_heroku.settings(locals(), staticfiles=False)
# del DATABASES["default"]["OPTIONS"]["sslmode"]
# ================================ HEROKU =======================================


# ================================ SSL CONFIG =======================================
# # Force SSL redirect if site is live
# if os.getcwd() == '/app':ls

#     SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
#     SECURE_SSL_REDIRECT = True
#     # DEBUG = False
# ================================ SSL CONFIG =======================================
