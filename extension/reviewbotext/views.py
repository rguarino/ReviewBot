from django.shortcuts import render_to_response, get_object_or_404
from reviewboard.extensions.base import get_extension_manager
from reviewbotext.models import Run, ToolStatus


def logging_dashboard(request, template_name='logging/list.html'):

    from reviewbotext.extension import ReviewBotExtension
    extension_manager = get_extension_manager()
    extension = \
        extension_manager.get_enabled_extension(ReviewBotExtension.id)

    runs_info = []
    rawRuns = Run.objects.all()
    for run in rawRuns:
        run_info = {}
        run_info['name'] = run.name
        tools = []
        for tool in run.toolstatus_set.all():
            tools.append("%s.%s" % (tool.tool.entry_point, tool.tool.version))
            print 'Entry Point = [%s.%s]' % (tool.tool.entry_point, tool.tool.version)
        run_info['tools'] = tools
        run_info['id'] = run.id
        runs_info.append(run_info)

    return render_to_response(template_name, { 'runs': runs_info, 'url': extension._rb_url()})


def run_status_details(request, run_id=1, template_name='logging/run_status.html'):
    run = get_object_or_404(Run, id=run_id)
    from reviewbotext.extension import ReviewBotExtension
    extension_manager = get_extension_manager()
    extension = \
        extension_manager.get_enabled_extension(ReviewBotExtension.id)
    info = {}
    info['status'] = ("Finished" if run.finished else "Running")
    info['method'] = ("Manually" if run.ran_manually else "Automatically")
    info['root_url'] = extension._rb_url()
    tools = []
    for tool in run.toolstatus_set.all():
        tool_info = {}
        tool_info['name'] = "%s.%s" % (tool.tool.entry_point, tool.tool.version)
        tool_info['status'] = tool.get_status_display()
        tool_info['id'] = tool.id
        tools.append(tool_info)
    return render_to_response(template_name, {'run': run, 'info': info, 'tools': tools})


def tool_status_details(request, status_id=1, template_name='logging/tool_status.html'):
    status = get_object_or_404(ToolStatus, id=status_id)
    run = status.run
    from reviewbotext.extension import ReviewBotExtension
    extension_manager = get_extension_manager()
    extension = \
        extension_manager.get_enabled_extension(ReviewBotExtension.id)
    info = {}
    info['root_url'] = extension._rb_url()
    info['name'] = "%s.%s" % (status.tool.entry_point, status.tool.version)
    info['status'] = status.get_status_display()
    times = []
    if( status.queued_time != None):
        times.append(('Queued', status.queued_time))
    if( status.running_time != None):
        times.append(('Running', status.running_time))
    if( status.suceeded_time != None):
        times.append(('Suceeded', status.running_time))
    if( status.failed_time != None):
        times.append(('Failed', status.failed_time))
    if( status.time_out_time != None):
        times.append(('Timeout', status.time_out_time))

    return render_to_response(template_name, {'status': status, 'info': info, 'times': times})