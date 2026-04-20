DEBUG = False
LOG_FILE = "/var/log/yizumi/molding.log"

# mysql 数据库
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "HOST": "127.0.0.1",
        "NAME": "yizumi_molding",
        "USER": "debian-sys-maint",
        "PASSWORD": "jL6YRbWTAbncGDgI",
    }
}

# mongo 数据库
MONGO_HOST = "127.0.0.1"
MONGO_PORT = 27017
MONGO_DB_HSMOLDING = "yizumi_molding"

# 文件存储位置
FILE_STORAGE_PATH = "/opt/yizumi/storage/"
