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
        if self.finished:
            results = "%s :%s - %s" & (self.name, str(self.time_started), str(self.time_finished))
        else:
            isfinished()
            ended = (str(self.time_finished) if self.finished else "The Furute")
            results = "%s :%s - %s" % (self.name, str(self.time_started), ended)
        return results

    def isfinished(self):
        results = True
        for tool in self.toolstatus_set.all():
            status = tool.status
            if status == ToolStatus.QUEUED or status == ToolStatus.RUNNING:
                results = False
        self.finished = results
        return results

class ToolStatus(models.Model):
    """A instance of a tool that has been ran. It will keep
    track of the status of the tool during this run."""
    QUEUED = "Q"
    RUNNING = "R"
    SUCCEDED = "S"
    FAILED = "F"
    TIMEOUT = "T"

    STATUSES = (
        (QUEUED, 'Queued'),
        (RUNNING, 'Running'),
        (SUCCEDED, 'Succeded'),
        (FAILED, 'Failed'),
        (TIMEOUT, 'Timeout'),
    )

    status = models.CharField(max_length=1,choices=STATUSES,
        db_index=True)
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


    def error(self, locoation, error):
        if self.failed_time != None:
            failed_time = timezone.now()
        self.location = location
        self.messgae = error



    def __unicode__(self):
        return "%s (%s)"% (self.tool, self.queued_time)
