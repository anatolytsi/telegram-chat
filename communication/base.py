import asyncio
from typing import Callable

MSG_UPD_INTERVAL = 0.01

CHANNEL_KEY = 'channel'
DATA_KEY = 'data'


class BusPrototype:

    def __init__(self, *args, **kwargs):
        self.channels = []
        self._listeners = {}
        self._loop = None

    def _get_message(self) -> any:
        raise NotImplementedError

    async def _worker(self):
        while True:
            message = self._get_message()
            if message and (channel := message[CHANNEL_KEY]) in self.channels:
                await self._listeners[channel](message)
            else:
                await asyncio.sleep(MSG_UPD_INTERVAL)

    def _start_thread(self):
        if not self._loop:
            self._loop = asyncio.get_event_loop()
            self._loop.create_task(self._worker())

    def publish(self, channel: str, data: any) -> bool:
        raise NotImplementedError

    def subscribe(self, channel: str, listener: Callable[[any], any]) -> bool:
        raise NotImplementedError

    def unsubscribe(self, channel: str) -> bool:
        raise NotImplementedError
