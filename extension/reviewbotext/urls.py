from django.conf.urls.defaults import patterns

urlpatterns = patterns('reviewbotext.views',
    (r'^$', 'logging_dashboard'),
    (r'^status/(?P<status_id>\d+)/', 'tool_status_details'),
    (r'^runs/(?P<run_id>\d+)/', 'run_status_details')
)