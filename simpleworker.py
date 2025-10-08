from rq import Worker


class BaseDeathPenalty(object):
    """A death penalty that does nothing. Used for testing"""
    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self, *args, **kwargs):
        pass

    def __exit__(self, *args, **kwargs):
        pass


class SimpleWorker(Worker):
    """A worker that does not fork, and runs jobs in the same thread/process"""
    death_penalty_class = BaseDeathPenalty

    def main_work_horse(self, *args, **kwargs):
        raise NotImplementedError("Test worker does not implement this method")

    def execute_job(self, *args, **kwargs):
        """Execute job in same thread/process, do not fork()"""
        return self.perform_job(*args, **kwargs)
