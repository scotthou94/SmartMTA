from django.conf.urls import url
from . import views

urlpatterns = [
    # Home page /lab
    url(r'^$', views.index, name='index'),

    # Temperature page /show_temp
    url(r'^show_temp/$', views.temperature, name='temp'),

    # Map Page
    url(r'show_map/$', views.showMap, name='showMap'),

    # Edison Temperature
    url(r'edison_temp/$', views.edisonTemp, name='edisonTemp'),

    # Chart endpoint
    url(r'chart/$', views.chart, name='chart')
]