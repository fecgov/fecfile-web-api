from django.conf.urls import url
from . import views


urlpatterns = [

    url(r'^sa/schedA$', views.schedA, name='schedA'),
    url(r'^sa/contribution_aggregate$', views.contribution_aggregate, name='contribution_aggregate'),
    # url(r'^sa/create_transaction$',
    # views.create_transaction, name='create_transaction'),
]
