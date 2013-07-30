from django.conf import settings
from django.conf.urls.defaults import patterns, include
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpRequest
from django.utils.importlib import import_module

from celery import Celery
from djblets.siteconfig.models import SiteConfiguration
from djblets.webapi.resources import register_resource_for_model, \
                                     unregister_resource_for_model
from reviewboard.extensions.base import Extension
from reviewboard.extensions.hooks import DiffViewerActionHook, \
                                         ReviewRequestActionHook, \
                                         TemplateHook, \
                                         DashboardHook, \
                                         URLHook

from reviewboard.reviews.models import ReviewRequest

from reviewbotext.handlers import SignalHandlers
from reviewbotext.models import ReviewBotTool, Run, ToolStatus
from reviewbotext.resources import review_bot_review_resource, \
                                   review_bot_tool_resource, \
                                   review_bot_trigger_review_resource


class ReviewBotExtension(Extension):
    """An extension for communicating with Review Bot"""
    is_configurable = True
    has_admin_site = True
    default_settings = {
        'ship_it': False,
        'comment_unmodified': False,
        'open_issues': False,
        'BROKER_URL': '',
        'user': None,
        'max_comments': 30,
    }
    resources = [
        review_bot_review_resource,
        review_bot_tool_resource,
        review_bot_trigger_review_resource,
    ]

    def __init__(self, *args, **kwargs):
        super(ReviewBotExtension, self).__init__(*args, **kwargs)
        self.settings.load()
        self.celery = Celery('reviewbot.tasks')
        self.signal_handlers = SignalHandlers(self)
        register_resource_for_model(ReviewBotTool,
                                    review_bot_tool_resource)
        self.add_action_hooks()
        self.template_hook = TemplateHook(self,
                                          'base-scripts-post',
                                          'reviewbot_hook_action.html')

        self.url_hook = URLHook(self, patterns('',
            (r'^logging/', include('reviewbotext.urls'))))

        self.dashboard_hook = DashboardHook(
            self,
            entries = [
                {
                    'label': 'Logging',
                    'url': settings.SITE_ROOT + "logging/",
                }
            ] )

    def add_action_hooks(self):
        actions = [{
            'id': 'reviewbot-link',
            'label': 'Review Bot',
            'url': '#'
        }]
        self.review_action_hook = ReviewRequestActionHook(self,
                                                          actions=actions)
        self.diff_action_hook = DiffViewerActionHook(self, actions=actions)

    def shutdown(self):
        self.signal_handlers.disconnect()
        unregister_resource_for_model(ReviewBotTool)
        super(ReviewBotExtension, self).shutdown()

    def notify(self, request_payload, selected_tools=None, ran_manually=False):
        """Add the request to the queue."""

        self.celery.conf.BROKER_URL = self.settings['BROKER_URL']

        review_settings = {
            'max_comments': self.settings['max_comments'],
        }
        payload = {
            'request': request_payload,
            'review_settings': review_settings,
            'session': self._login_user(self.settings['user']),
            'url': self._rb_url(),
        }

        if (selected_tools is not None):
            tools = []
            for tool in selected_tools:
            # Double-check that the tool can be run manually in case
            # this setting was changed between trigger time and queue time.
                try:
                    tools.append(
                        ReviewBotTool.objects.get(id=tool['id'],
                                                  allow_run_manually=True))
                except ObjectDoesNotExist:
                    pass
        else:
            tools = ReviewBotTool.objects.filter(enabled=True,
                                                 run_automatically=True)


        review = ReviewRequest.objects.get(id=request_payload['review_request_id'])

        run = Run(name="%s [%s]" % ("Review", review.summary), ran_manually=ran_manually,\
            reviewrequest= review)

        run.save()
        for tool in tools:
            review_settings['ship_it'] = tool.ship_it
            review_settings['comment_unmodified'] = tool.comment_unmodified
            review_settings['open_issues'] = tool.open_issues
            payload['review_settings'] = review_settings

            from django.utils import timezone
            toolStatus = ToolStatus(tool=tool, run=run, queued_time=timezone.now())
            toolStatus.status = toolStatus.QUEUED
            toolStatus.save()
            print "%s.%s" % (tool.entry_point, tool.version)
            try:
                self.celery.send_task(
                    "reviewbot.tasks.ProcessReviewRequest",
                    [payload, tool.tool_settings],
                    queue='%s.%s' % (tool.entry_point, tool.version))
            except Exception, e:
                toolStatus.error("Queuing", str(e))
                toolStatus.save()
                raise

    def _login_user(self, user_id):
        """
        Login as specified user, does not depend on auth backend (hopefully).

        This is based on Client.login() with a small hack that does not
        require the call to authenticate().

        Will return the session id of the login.
        """
        user = User.objects.get(id=user_id)
        user.backend = "%s.%s" % ("django.contrib.auth.backends",
                                  "ModelBackend")
        engine = import_module(settings.SESSION_ENGINE)

        # Create a fake request to store login details.
        request = HttpRequest()
        request.session = engine.SessionStore()
        login(request, user)
        request.session.save()
        return request.session.session_key

    def send_refresh_tools(self):
        """Request workers to update tool list."""
        self.celery.conf.BROKER_URL = self.settings['BROKER_URL']
        payload = {
            'session': self._login_user(self.settings['user']),
            'url': self._rb_url(),
        }
        self.celery.control.broadcast('update_tools_list', payload=payload)

    def send_ping(self):
        """Broadcast a ping to all the clients"""
        self.celery.conf.BROKER_URL = self.settings['BROKER_URL']
        self.celery.control.ping(timeout=0.5)

    def _rb_url(self):
        """Returns a valid reviewbot url including http protocol."""
        protocol = SiteConfiguration.objects.get_current().get(
            "site_domain_method")
        domain = Site.objects.get_current().domain
        return '%s://%s%s' % (protocol, domain, settings.SITE_ROOT)
