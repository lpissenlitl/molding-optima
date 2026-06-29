from django.conf import settings

from gis.common.conf import GConfClient

conf_client = GConfClient(**settings.GCONF)
conf_decorator = conf_client.decorator()
