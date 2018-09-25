from django.conf.urls import url
from . import views

# url's for comm_info and get_default_reasons for filing

urlpatterns = [
    url(r'^f99/comm_info/(?P<pk>[0-9]+)$', views.get_comm_info, name='get_comm_info' ),
    #url(r'^f99/comm_info/$', views.get_comm_info, name='get_comm_info' ),
    url(r'^f99/create_comm_info$', views.create_comm_info, name='create_comm_info'),
    url(r'^f99/get_default_reasons$', views.get_f99_reasons, name='get_f99_reasons'),

    url(r'^core/get_comm_details$', views.get_committee, name='get_committee' ),
    url(r'^core/update_comm_details/(?P<cid>[0-9,a-z,A-Z]+)$', views.update_committee, name='update_committee' ),    
    url(r'^core/create_committee$', views.create_committee, name='create_committee')
]
