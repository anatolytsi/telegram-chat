from threading import Lock
from typing import Callable, Union, List

from communication.base import BusPrototype, BusDir, BusMessage


class InternalBus(BusPrototype):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._message_bus: List[BusMessage] = []
        self._lock = Lock()

    def _get_message(self) -> Union[BusMessage, None]:
        if self._message_bus:
            with self._lock:
                return self._message_bus.pop()
        else:
            return None

    def publish(self, message: BusMessage) -> bool:
        with self._lock:
            self._message_bus.append(message)
        return True

    def subscribe(self, channel: str, direction: BusDir, listener: Callable[[any], any]) -> bool:
        if channel not in self.channels:
            self.channels.append(f'{direction.value}: {channel}')
            self._listeners[f'{direction.value}: {channel}'] = listener
        self._start_thread()
        return True

    def unsubscribe(self, channel: str, direction: BusDir) -> bool:
        if channel in self.channels:
            del self._listeners[f'{direction.value}: {channel}']
        return True
