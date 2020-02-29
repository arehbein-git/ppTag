from threading import Timer
# import time

class OneShotQueueTimer():
    """A one shot Timer class that restarts if you start it before it is run but queues another run if you start it when running."""

    def __init__(self, seconds, target):
        self._should_continue = False
        self._was_started_while_running = False
        self.is_running = False
        self.seconds = seconds
        self.target = target
        self.thread = None

    def _handle_target(self):
        self.is_running = True
        self.target()
        self.is_running = False
        if self._was_started_while_running:
            self._was_started_while_running = False
            self._handle_target()
        else:
            self._should_continue = False

    def _start_timer(self):
        if self._should_continue: # Code could have been running when cancel was called.
            self.thread = Timer(self.seconds, self._handle_target)
            self.thread.start()

    def start(self):
        if not self._should_continue and not self.is_running:
            self._should_continue = True
            self._start_timer()
        elif not self.is_running:
            self.cancel()
            self.start()
        else:
            self._was_started_while_running = True
            #print("Timer already running, please wait if you're restarting.")
            pass
            
    def cancel(self):
        if self.thread is not None:
            self._should_continue = False # Just in case thread is running and cancel fails.
            self.thread.cancel()
        else:
            #print("Timer never started or failed to initialize.")
            pass

# def test():	
#     print("run at %s" % time.ctime())
#     time.sleep(5)
#     print("run till %s" % time.ctime())

# t = OneShotQueueTimer(5, test)
# print("app started at %s" % time.ctime())
# print("timer started at %s" % time.ctime())
# t.start()
# time.sleep(3)
# print("timer started while triggered but not running at %s" % time.ctime())
# t.start()
# time.sleep(6)
# print("timer started while running at %s" % time.ctime())
# t.start()
# time.sleep(11)
# print("timer started after it was running at %s" % time.ctime())
# t.start()