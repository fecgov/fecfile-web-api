from django.conf.urls import patterns, url, include
from django.contrib import admin
from rest_framework_nested import routers
from .authentication.views import AccountViewSet, LoginView, LogoutView
from .posts.views import AccountPostsViewSet, PostViewSet
from .views import IndexView

router = routers.SimpleRouter()
router.register(r'accounts', AccountViewSet)
router.register(r'posts', PostViewSet)

accounts_router = routers.NestedSimpleRouter(
    router, r'accounts', lookup='account'
)
accounts_router.register(r'posts', AccountPostsViewSet)

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    #url(r'^admin$', include(admin.site.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api/v1/', include(router.urls)),
    url(r'^api/v1/', include(accounts_router.urls)),
    url(r'^api/v1/auth/login/$', LoginView.as_view(), name='login'),
    url(r'^api/v1/auth/logout/$', LogoutView.as_view(), name='logout'),
    url(r'^api/docs/', include('rest_framework_swagger.urls')),
    url('^.*$', IndexView.as_view(), name='index'),
)
