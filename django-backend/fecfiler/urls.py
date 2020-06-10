from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token
from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_nested import routers
from .authentication.views import AccountViewSet, LoginView, LogoutView
#from .posts.views import AccountPostsViewSet, PostViewSet
from .views import IndexView
from django.views.decorators.csrf import csrf_exempt
from rest_framework_swagger.views import get_swagger_view
#import fecfiler.form3x.urls as f3xurls
schema_view = get_swagger_view(title='FEC-Filer API')

router = routers.SimpleRouter()
router.register(r'accounts', AccountViewSet, basename='Accounts')
#router.register(r'posts', PostViewSet)

accounts_router = routers.NestedSimpleRouter(
    router, r'accounts', lookup='account'
)
#accounts_router.register(r'posts', AccountPostsViewSet)

urlpatterns = [
    #url(r'^admin/', include(admin.site.urls)),
    #url(r'^admin$', include(admin.site.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api/v1/', include(router.urls)),
    url(r'^api/v1/', include(accounts_router.urls)),
    url(r'^api/v1/', include('fecfiler.forms.urls')),
    url(r'^api/v1/', include('fecfiler.core.urls')),

    #url(r'^api/v1/', include('fecfiler.form3x.urls')),
    url(r'^api/v1/', include('fecfiler.sched_A.urls')),
    url(r'^api/v1/', include('fecfiler.sched_B.urls')),
    url(r'^api/v1/', include('fecfiler.sched_C.urls')),
    url(r'^api/v1/', include('fecfiler.sched_D.urls')),
    url(r'^api/v1/', include('fecfiler.sched_E.urls')),
    url(r'^api/v1/', include('fecfiler.sched_F.urls')),
    url(r'^api/v1/', include('fecfiler.sched_H.urls')),
    url(r'^api/v1/', include('fecfiler.sched_L.urls')),
    url(r'^api/v1/', include('fecfiler.form_1M.urls')),
    url(r'^api/v1/', include('fecfiler.authentication.urls')),
    url(r'^api/v1/', include('fecfiler.contacts.urls')),
    #url(r'^api/v1/auth/login$', csrf_exempt(LoginView.as_view()), name='login'),
    #url(r'^api/v1/auth/login$', LoginView.as_view(), name='login'),
    #url(r'^api/docs/', include('rest_framework_swagger.urls')),
    url(r'^api/v1/auth/logout/$', LogoutView.as_view(), name='logout'),
    url(r'^api/docs$', schema_view),
    url(r'^api/v1/token/obtain$', obtain_jwt_token),
    url(r'^api/v1/token/refresh$', refresh_jwt_token),
    url(r'^files/', include('db_file_storage.urls')),
    #url('^.*$', IndexView.as_view(), name='index'),
]

# if settings.DEBUG:
#  urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
