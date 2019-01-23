from  django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^f3x/get_filed_report_types$', views.get_filed_report_types, name='get_filed_report_types'),
    url(r'^f3x/get_transaction_categories$', views.get_transaction_categories, name='get_transaction_categories'),
    url(r'^f3x/get_report_types$', views.get_report_types, name='get_report_types'),
]
