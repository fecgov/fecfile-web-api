from django.conf.urls import url
from . import views

# url's for comm_info and get_default_reasons for filing

urlpatterns = [
    url(r'^f99/comm_info/(?P<pk>[0-9]+)$', views.get_delete_update_comm_info, name='get_delete_update_comm_info' ),
    url(r'^f99/comm_infos/$', views.get_post_comm_info, name='get_post_comm_info'),
    url(r'^f99/get_default_reasons$', views.get_f99_reasons, name='get_f99_reasons')
    
]
