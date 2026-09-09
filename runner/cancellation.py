import threading

class CancellationToken:
    def __init__(self) -> None:
        self._event = threading.Event()
    
    def __init__(self) -> None:
        self._event.set()
    
    @property
    def is_cancelled(self) -> bool:
        return self._event.is_set()
    
    def raise_if_cancelled(self) -> None:
        if self.is_cancelled:
            raise CancellationRequested()

class CancellationRequested(Exception):
    pass