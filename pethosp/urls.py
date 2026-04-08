from django.urls import re_path
from pethosp import views

urlpatterns = [
    re_path(r'^$', views.dashboard, name='pethosp-dashboard'),
]
