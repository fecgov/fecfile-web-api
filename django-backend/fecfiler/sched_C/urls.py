from django.conf.urls import url
from . import views


urlpatterns = [

    url(r'^sa/schedC$', views.schedC, name='schedC'),
    # url(r'^sa/aggregate_amount$', views.aggregate_amount, name='aggregate_amount'),
    # url(r'^sa/create_transaction$',
    # views.create_transaction, name='create_transaction'),
]
