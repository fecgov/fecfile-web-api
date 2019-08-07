from django.conf.urls import url
from . import views


urlpatterns = [

    url(r'^se/schedE$', views.schedE, name='schedE'),
    
]
