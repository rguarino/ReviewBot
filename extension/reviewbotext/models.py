from django.db import models
from django.utils.translation import ugettext as _
from djblets.util.fields import JSONField
from django.utils import timezone
from reviewboard.reviews.models import ReviewRequest 

class ReviewBotTool(models.Model):
    """Information about a tool installed on a worker."""
    name = models.CharField(max_length=128, blank=False)
    entry_point = models.CharField(max_length=128, blank=False)
    version = models.CharField(max_length=128, blank=False)
    description = models.CharField(max_length=512, default="", blank=True)
    enabled = models.BooleanField(default=True)
    run_automatically = models.BooleanField(
        default=False,
        help_text=_("Run automatically when a review request is updated."))
    allow_run_manually = models.BooleanField(default=False)
    in_last_update = models.BooleanField()
    ship_it = models.BooleanField(
        default=False,
        help_text=_("Ship it! If no issues raised."))
    open_issues = models.BooleanField(default=False)
    comment_unmodified = models.BooleanField(
        default=False,
        verbose_name=_("Comment on unmodified code"))
    tool_options = JSONField()
    tool_settings = JSONField()

    def __unicode__(self):
        return "%s - v%s" % (self.name, self.version)

    class Meta:
        unique_together = ('entry_point', 'version')


class Run(models.Model):
    """A group of tools ran simaltaniously """
    reviewrequest = models.ForeignKey(ReviewRequest)
    name = models.CharField(max_length=128, blank=False)
    finished = models.BooleanField(default=False)
    time_started = models.DateTimeField(default=timezone.now)
    time_finished = models.DateTimeField(blank=True, null=True)
    ran_manually = models.BooleanField(default=False)

    def __unicode__(self):
        ended = (str(self.time_finished) if self.finished else "The Furute")
        print ended
        return "%s :%s - %s"% (self.name, str(self.time_started), ended)

    def isfinished(self):
        results = True
        for tool in self.toolstatus_set.all():
            if tool.queued() or tool.running():
                results = False
        return results

class ToolStatus(models.Model):
    """A instance of a tool that has been ran. It will keep
    track of the status of the tool during this run."""
    name = models.CharField(max_length=128, blank=False)
    tool = models.ForeignKey(ReviewBotTool)
    run = models.ForeignKey(Run)

    queued_time = models.DateTimeField(blank=True, null=True)
    running_time = models.DateTimeField(blank=True, null=True)
    suceeded_time = models.DateTimeField(blank=True, null=True)
    failed_time = models.DateTimeField(blank=True, null=True)
    time_out_time = models.DateTimeField(blank=True, null=True)
    location = models.CharField(max_length=128, blank=True)
    message = models.CharField(max_length=256, blank=True)

    def current(self):
        if(self.queued() == True and self.running() == False):
            return 1
        elif(self.running() and not self.suceed() ):
            return 2
        elif(self.failed()):
            return 3
        elif(self.suceed()):
            return 4
        elif(self.timeout()):
            return 5

    def current_str(self, id = 0):
        if(id == 0):
            id = self.current()
        if(id == 1):
            return "Queued"
        if(id == 2):
            return "Running"
        if(id == 3):
            return "Failed"
        if(id == 4):
            return "Success"
        if(id == 5):
            return "Timeout"

    def queued(self):
        if queued_time != None & running_time == None:
            return True
        else:
            return False

    def running(self):
        if running_time != None & suceeded_time == None:
            return True
        else:
            return False

    def suceed(self):
        if suceeded_time != None & failed_time == None & time_out_time == None:
            return True
        else:
            return False

    def error(self, locoation, error):
        if failed_time != None:
            failed_time = timezone.now()
        self.location = location
        self.messgae = error

    def failed(self):
        if failed_time != None:
            return True
        else:
            return False

    def timeout(self):
        if time_out_time != None:
            return True
        else:
            return False

    def __unicode__(self):
        return "%s (%s)"% (self.tool, self.queued_time)
