from django.conf.urls import url
from . import views


urlpatterns = [

    url(r'^sL/schedL$', views.schedL, name='schedL'),
    
]
