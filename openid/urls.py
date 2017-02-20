from django.conf.urls import url

from . import views

app_name = 'openid'
urlpatterns = [
    url(r'^$', views.openid_login, name='openid'),
    url(r'^login/$', views.LoginView.as_view(), name='login'),
    url(r'^logout/$', views.openid_logout, name='logout'),
]
