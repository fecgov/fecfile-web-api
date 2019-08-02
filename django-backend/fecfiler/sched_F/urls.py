from django.conf.urls import url
from . import views


urlpatterns = [

    url(r'^sf/schedF$', views.schedF, name='schedF'),
    
]
