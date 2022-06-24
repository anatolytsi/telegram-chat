import json
import os
from typing import Callable

import redis
from dotenv import load_dotenv

from communication.base import BusPrototype, BusDir

load_dotenv()

# Specific buses configurations
REDIS_HOST = os.environ.get('REDIS_HOST')
REDIS_PORT = int(os.environ.get('REDIS_PORT'))


class RedisBus(BusPrototype):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._redis = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0)
        self._pubsub = self._redis.pubsub()

    def _get_message(self) -> any:
        message = self._pubsub.get_message()
        if not message or message['type'] == 'subscribe':
            return {}
        for key, value in message.items():
            try:
                message[key] = value.decode()
            except (UnicodeDecodeError, AttributeError):
                pass
        return message

    def publish(self, channel: str, direction: BusDir, data: any) -> bool:
        try:
            self._redis.publish(f'{direction.value}: {channel}', json.dumps(data))
            return True
        except Exception as e:
            print(e)
            return False

    def subscribe(self, channel: str, direction: BusDir, listener: Callable[[any], any]) -> bool:
        try:
            if channel not in self.channels:
                self._pubsub.subscribe(f'{direction.value}: {channel}')
                self.channels.append(f'{direction.value}: {channel}')
                self._listeners[f'{direction.value}: {channel}'] = listener
            self._start_thread()
            return True
        except Exception as e:
            print(e)
            return False

    def unsubscribe(self, channel: str, direction: BusDir) -> bool:
        try:
            if channel in self.channels:
                self._pubsub.unsubscribe(f'{direction.value}: {channel}')
                del self._listeners[f'{direction.value}: {channel}']
            return True
        except Exception as e:
            print(e)
            return False
