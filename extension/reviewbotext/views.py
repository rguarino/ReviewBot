from django.shortcuts import render_to_response, get_object_or_404
from reviewboard.extensions.base import get_extension_manager
from reviewbotext.models import Run, ToolStatus


def logging_dashboard(request, template_name='logging/list.html'):

    from reviewbotext.extension import ReviewBotExtension
    extension_manager = get_extension_manager()
    extension = \
        extension_manager.get_enabled_extension(ReviewBotExtension.id)

    workers = extension.celery.control.inspect()
    registered = workers.registered()
    worker_names = []
    for worker in registered:
        worker_names.append(worker)

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
        runs_info.append(run_info)

    return render_to_response(template_name, {'workers': worker_names, 'runs': runs_info})


def run_status_details(request, run_id=1, template_name='logging/run_status.html'):
    run = get_object_or_404(Run, id=run_id)
    info = {}
    info['status'] = ("Finished" if run.isfinished() else "Running")
    info['method'] = ("Manually" if run.ran_manually else "Automatically")
    tools = []
    for tool in run.toolstatus_set.all():
        tool_info = {}
        tool_info['name'] = "%s.%s" % (tool.tool.entry_point, tool.tool.version)
        tool_info['status'] = tool.current_str()
        tools.append(tool_info)
    return render_to_response(template_name, {'run': run, 'info': info, 'tools': tools})


def tool_status_details(request, status_id=1, template_name='logging/tool_status.html'):
    status = get_object_or_404(ToolStatus, id=status_id)
    return render_to_response(template_name, {'status': status})
