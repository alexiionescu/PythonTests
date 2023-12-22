import sys
import time
from enum import Enum, unique
from threading import Event, Thread


class AppThread(Thread):
    @unique
    class SignalType(Enum):
        Continue = 0
        Close = 1
        User = 2

    def __init__(self, loop_time: float = 1):
        Thread.__init__(self, daemon=True)
        self.signal_event = Event()
        self.signal = None
        self.signal_args = None
        self.loop_time = loop_time

    def Signal(self, *args, signal = SignalType.User):
        self.signal = signal
        self.signal_args = args
        self.signal_event.set()

    def run(self):
        if self.OnStart():
            while True:
                if self.signal_event.wait(self.loop_time):
                    if self.signal == AppThread.SignalType.Close:
                        break
                    elif self.signal == AppThread.SignalType.User:
                        if not self.OnSignal(*self.signal_args):
                            break
                    self.signal = None
                    self.signal_event.clear()
                else:
                    if not self.OnLoop():
                        break
            self.OnClose()

    def OnStart(self):
        return True

    def OnClose(self):
        pass

    def OnSignal(self, *args):
        return True

    def OnLoop(self):
        return True


class MainApp:
    __gInstance__ = None
    @unique
    class LoopResult(Enum):
        Continue = 0
        Wait = 1
        Quit = 2


    def __init__(self, close_timeout=3):
        if MainApp.__gInstance__:
            raise Exception("Cannot instantiate a second MainApp")
        MainApp.__gInstance__ = self
        self.threads: list = []
        try:
            loopr = self.OnStart(sys.argv[1:])
            while loopr != MainApp.LoopResult.Quit:
                if loopr == MainApp.LoopResult.Wait or loopr is None:
                    time.sleep(1)
                self.threads = [t for t in self.threads if t.is_alive()]
                loopr = self.OnLoop()

        except KeyboardInterrupt:
            print("Ctrl+C received")
            pass

        for thread in self.threads:
            thread.Signal(signal=AppThread.SignalType.Close)
            thread.join(timeout=close_timeout)
        self.OnClose()

    def AddThread(self, thread: AppThread):
        self.threads.append(thread)
        thread.start()

    def OnStart(self, argv) -> LoopResult:
        pass

    def OnLoop(self) -> LoopResult:
        return MainApp.LoopResult.Wait

    def OnClose(self):
        pass
