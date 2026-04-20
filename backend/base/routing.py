# mysite/routing.py
from channels.routing import ProtocolTypeRouter, URLRouter

# from channels.auth import AuthMiddlewareStack
import hsmolding.routing


application = ProtocolTypeRouter(
    {
        # (http->django views is added by default)
        "websocket": URLRouter(hsmolding.routing.websocket_urlpatterns)
    }
)
