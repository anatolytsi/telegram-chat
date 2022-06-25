import asyncio
import json
from enum import Enum
from typing import Callable, Dict, Union

MSG_UPD_INTERVAL = 0.01

CHANNEL_KEY = 'channel'
DATA_KEY = 'data'
DIR_KEY = 'direction'


class BusDir(Enum):
    TG = 1
    COM = 2


class BusMessage:
    _channel: str
    _direction: BusDir
    _data: any
    _content: Dict[str, any]

    def __init__(self, encoded_msg: str = '', channel: str = '', direction: BusDir = None, data: any = None):
        if encoded_msg:
            self._decode_msg(encoded_msg)
        elif channel and direction and data:
            self._channel = channel
            self._direction = direction
            self._data = data
        else:
            raise KeyError(f'Either encoded_msg should be provided or channel, direction and data')
        self._content = {CHANNEL_KEY: self._channel, DIR_KEY: self._direction.value, DATA_KEY: self._data}

    @property
    def channel(self):
        return self._channel

    @property
    def dir_channel(self):
        return f'{self._direction.value}: {self._channel}'

    @property
    def direction(self):
        return self._direction

    @property
    def data(self):
        return self._data

    def _decode_msg(self, encoded_msg):
        message = json.loads(encoded_msg)
        self._channel = message[CHANNEL_KEY]
        self._direction = BusDir(message[DIR_KEY])
        self._data = message[DATA_KEY]

    def __str__(self):
        return json.dumps(self._content)


class BusPrototype:

    def __init__(self, *args, **kwargs):
        self.channels = []
        self._listeners = {}
        self._loop = None

    def _get_message(self) -> Union[BusMessage, None]:
        raise NotImplementedError

    async def _worker(self):
        while True:
            message = self._get_message()
            if message and message.dir_channel in self.channels:
                await self._listeners[message.dir_channel](message)
            else:
                await asyncio.sleep(MSG_UPD_INTERVAL)

    def _start_thread(self):
        if not self._loop:
            self._loop = asyncio.get_event_loop()
            self._loop.create_task(self._worker())

    def publish(self, message: BusMessage) -> bool:
        raise NotImplementedError

    def subscribe(self, channel: str, direction: BusDir, listener: Callable[[any], any]) -> bool:
        raise NotImplementedError

    def unsubscribe(self, channel: str, direction: BusDir) -> bool:
        raise NotImplementedError
