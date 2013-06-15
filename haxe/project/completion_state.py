from haxe.log import log
from haxe.tools.cache import Cache


class ProjectCompletionState:

    def __init__(self):
        
        self.running = Cache()
        self.trigger = Cache(1000)
        self.current_id = None   
        self.errors = []
        self.async = Cache(1000)
        self.current = {
            "input" : None,
            "output" : None
        }

    def add_completion_result (self, comp_result):
        self.async.insert(comp_result.ctx.view_id, comp_result)

    def is_equivalent_completion_already_running(self, ctx):
        # check if another completion with the same properties is already running
        # in this case we don't need to start a new completion
        complete_offset = ctx.complete_offset
        view_id = ctx.view_id

        last_completion_id = self.current_id
        running_completion = self.running.get_or_default(last_completion_id, None)    
        return running_completion is not None and running_completion[0] == complete_offset and running_completion[1] == view_id

    def run_if_still_up_to_date (self, comp_id, run):
        self.running.delete(comp_id)
        if self.current_id == comp_id:
            run()

    def set_new_completion (self, ctx):
        # store current completion id and properties
        self.running.insert(ctx.id, (ctx.complete_offset, ctx.view_id))
        self.current_id = ctx.id

        self.set_errors([])

    def set_trigger(self, view, options):
        log("SET TRIGGER")
        self.trigger.insert(view.id(), options)

    def clear_completion (self):
        self.current = {
            "input" : None,
            "output" : None
        }

    def set_errors (self, errors):
        self.errors = errors

    def get_and_delete_trigger(self, view):
        return self.trigger.get_and_delete(view.id(), None)

    def get_and_delete_async(self, view):
        return self.async.get_and_delete(view.id(), None)

    def get_async(self, view):
        return self.async.get_or_default(view.id(), )

    def delete_async(self, view):
        return self.async.delete(view.id())