from django.urls import re_path
from playcentre import views

urlpatterns = [
    re_path(r'^$', views.dashboard, name='playcentre-dashboard'),
]
