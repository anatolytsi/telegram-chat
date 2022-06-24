import json
import os
from typing import Callable

import redis
from dotenv import load_dotenv

from communication.base import BusPrototype

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

    def publish(self, channel: str, data: any) -> bool:
        try:
            self._redis.publish(channel, json.dumps(data))
            return True
        except Exception as e:
            print(e)
            return False

    def subscribe(self, channel: str, listener: Callable[[any], any]) -> bool:
        try:
            if channel not in self.channels:
                self._pubsub.subscribe(channel)
                self.channels.append(channel)
                self._listeners[channel] = listener
            self._start_thread()
            return True
        except Exception as e:
            print(e)
            return False

    def unsubscribe(self, channel: str) -> bool:
        try:
            if channel in self.channels:
                self._pubsub.unsubscribe(channel)
                self.channels.remove(channel)
                del self._listeners[channel]
            return True
        except Exception as e:
            print(e)
            return False
