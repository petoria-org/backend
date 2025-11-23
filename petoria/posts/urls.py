# posts/urls.py
from rest_framework.routers import DefaultRouter

from .views import LostPostViewSet, FoundPostViewSet, SurrenderCustodyPostViewSet

router = DefaultRouter()
router.register(r"lost-posts", LostPostViewSet, basename="lostpost")
router.register(r"found-posts", FoundPostViewSet, basename="foundpost")
router.register(r"surrender-posts", SurrenderCustodyPostViewSet, basename="surrenderpost")

urlpatterns = router.urls
