from  django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^f3x/get_filed_report_types$', views.get_filed_report_types, name='get_filed_report_types')
]
