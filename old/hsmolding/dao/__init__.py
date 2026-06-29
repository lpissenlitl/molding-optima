from django.conf import settings
from mongoengine import connect

connect(
  db=settings.MONGO_DB_HSMOLDING,
  host=settings.MONGO_HOST,
  port=settings.MONGO_PORT,
  username=settings.MONGO_USER,
  password=settings.MONGO_PASSWORD,
  authentication_source='admin' 
)

