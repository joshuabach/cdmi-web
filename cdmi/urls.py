from django.conf.urls import url

from . import views

app_name = 'cdmi'
urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^browse/(?P<site>[0-9]*)', views.browse, name='browse'),
    url(r'^upload/(?P<site>[0-9]*)', views.upload, name='upload'),
    url(r'^mkdir/(?P<site>[0-9]*)', views.mkdir, name='mkdir'),
    url(r'^update/(?P<site>[0-9]*)', views.update, name='update'),
    url(r'^delete/(?P<site>[0-9]*)', views.delete, name='delete'),
]
