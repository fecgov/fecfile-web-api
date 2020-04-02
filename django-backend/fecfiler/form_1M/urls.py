from django.conf.urls import url
from . import views


urlpatterns = [
    url(r"^f1M/form1M$", views.form1M, name="form1M"),
    
]
