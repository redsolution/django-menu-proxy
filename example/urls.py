from django.conf.urls.defaults import *
from example.models import Page, Catalog, News

urlpatterns = patterns('',
    url(r'^page/(?P<slug>\w+)/$', 'django.views.generic.list_detail.object_detail', {
        'queryset': Page.objects.all(), 'slug_field': 'slug', }, name='page'),
    url(r'^catalog/(?P<object_id>\w+)/$', 'django.views.generic.list_detail.object_detail', {
        'queryset': Catalog.objects.filter(visible=True), }, name='catalog'),
    url(r'^news/$', 'django.views.generic.list_detail.object_list', {
        'queryset': News.objects.all()}, name='archive'),
    url(r'^news/(?P<object_id>\d+)/$', 'django.views.generic.list_detail.object_detail', {
        'queryset': News.objects.all(), 'slug_field': 'slug', }, name='news'),
    url(r'^search/$', 'django.views.generic.simple.direct_to_template', {
        'template': 'search.html'}, name='search'),
    url(r'^result/$', 'django.views.generic.simple.direct_to_template', {
        'template': 'result.html'}, name='result'),
)
