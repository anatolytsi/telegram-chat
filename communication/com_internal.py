from threading import Lock
from typing import Callable

from base import BusPrototype
from base import CHANNEL_KEY, DATA_KEY


class InternalBus(BusPrototype):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._message_bus = []
        self._lock = Lock()

    def _get_message(self) -> any:
        if self._message_bus:
            with self._lock:
                return self._message_bus.pop()
        else:
            return {}

    def publish(self, channel: str, data: any) -> bool:
        message = {CHANNEL_KEY: channel, DATA_KEY: data}
        with self._lock:
            self._message_bus.append(message)
        return True

    def subscribe(self, channel: str, listener: Callable[[any], any]) -> bool:
        if channel not in self.channels:
            self.channels.append(channel)
            self._listeners[channel] = listener
        self._start_thread()
        return True

    def unsubscribe(self, channel: str) -> bool:
        if channel in self.channels:
            self.channels.remove(channel)
            del self._listeners[channel]
        return True
