from django.conf.urls import url

from . import views

app_name = 'cdmi'
urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^browse', views.browse, name='browse'),
    url(r'^upload', views.upload, name='upload'),
    url(r'^mkdir', views.mkdir, name='mkdir'),
    url(r'^update', views.update, name='update'),
    url(r'^delete', views.delete, name='delete'),
    url(r'^sites', views.sites, name='sites'),
]
