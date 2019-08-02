from django.conf.urls import url
from . import views


urlpatterns = [

    url(r'^sh3/schedH3$', views.schedH3, name='schedH3'),
    
]
