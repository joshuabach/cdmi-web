from django.conf.urls import url

from . import views

app_name = 'cdmi'
urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^browse/(?P<site>[0-9]+)/(?P<path>.*)$', views.BrowserView.as_view(), name='browse'),
    url(r'^browse/(?P<site>[0-9]+)$', views.BrowserView.as_view(), kwargs={'path': ''}, name='browse'),
    url(r'^browse/(?P<path>.*)$', views.BrowserView.as_view(), kwargs={'site': None}, name='browse'),
    url(r'^upload/(?P<site>[0-9]+)/(?P<path>.*)$', views.upload, name='upload'),
    url(r'^mkdir/(?P<site>[0-9]+)/(?P<path>.*)$', views.mkdir, name='mkdir'),
    url(r'^update/(?P<site>[0-9]+)/(?P<path>.*)$', views.update, name='update'),
    url(r'^delete/(?P<site>[0-9]+)/(?P<path>.*)$', views.delete, name='delete'),
    url(r'^info/(?P<site>[0-9]+)/(?P<path>.*)$', views.object_info, name='object_info'),
]
