from django.conf.urls import url

from .views import translate


urlpatterns = [
    url(r'^(?P<app_label>[\w_]+)/(?P<model_name>[\w_]+)/(?P<pk>.+)/(?P<language>[a-zA-Z_-]+)/$', translate, name='translate'),
]
