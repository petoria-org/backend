import logging
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from rest_framework_simplejwt.authentication import JWTAuthentication

logger = logging.getLogger(__name__)


class JWTAuthMiddleware:
    """
    Populate scope["user"] for WebSocket connections using SimpleJWT access tokens.
    Accepts tokens from the Authorization header (Bearer <token>) or a query param
    (?token=<token> or ?access=<token>) for browser clients that cannot set headers.
    """

    def __init__(self, app):
        self.app = app
        self.jwt_auth = JWTAuthentication()

    async def __call__(self, scope, receive, send):
        close_old_connections()
        token = self._get_token_from_headers(scope) or self._get_token_from_query(scope)

        if token:
            try:
                validated = self.jwt_auth.get_validated_token(token)
                user = await database_sync_to_async(self.jwt_auth.get_user)(validated)
                scope["user"] = user
            except Exception:  # fallback to anonymous if token invalid
                logger.debug("WebSocket JWT auth failed", exc_info=True)
                scope["user"] = AnonymousUser()
        else:
            scope["user"] = AnonymousUser()

        return await self.app(scope, receive, send)

    def _get_token_from_headers(self, scope):
        headers = dict(scope.get("headers") or [])
        if b"authorization" not in headers:
            return None

        parts = headers[b"authorization"].decode().split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]
        return None

    def _get_token_from_query(self, scope):
        raw_qs = scope.get("query_string", b"")
        if isinstance(raw_qs, bytes):
            raw_qs = raw_qs.decode()
        params = parse_qs(raw_qs)
        return (params.get("token") or params.get("access") or [None])[0]
