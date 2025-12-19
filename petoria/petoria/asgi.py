import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "petoria.settings")
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from chat.routing import websocket_urlpatterns
from chat.middleware import JWTAuthMiddleware

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    # JWTAuthMiddleware provides token auth; AuthMiddlewareStack keeps session fallback.
    "websocket": JWTAuthMiddleware(
        AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
    ),
})
