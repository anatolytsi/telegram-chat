import os
import time
from abc import ABC

from dotenv import load_dotenv

from communication.base import BusPrototype
from communication.com_redis import RedisBus
from communication.com_internal import InternalBus

load_dotenv()

REDIS_BUS = 'redis'
INTERNAL_BUS = 'internal'
BUS_LIST = [REDIS_BUS, INTERNAL_BUS]

USED_BUS = os.environ.get('USED_BUS')
if USED_BUS not in BUS_LIST:
    raise NotImplementedError(f'Bus {USED_BUS} is not supported')


class Bus(BusPrototype, ABC):
    _instance = None
    _registry = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()
        cls._registry[kwargs['prefix']] = cls

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = cls.__new__(cls._registry[USED_BUS])
        return cls._instance


class BusFactory(ABC):
    def __new__(cls, *args, bus_class, **kwargs):
        obj = object.__new__(bus_class)
        obj.__init__(*args, **kwargs)
        return obj


class InternalBusFactory(BusFactory, Bus, ABC, prefix=INTERNAL_BUS):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, bus_class=InternalBus)


class RedisBusFactory(BusFactory, Bus, ABC, prefix=REDIS_BUS):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, bus_class=RedisBus)


if __name__ == '__main__':
    def test_listener(message: any):
        print(message)


    bus = Bus()
    bus.subscribe('testChannel', test_listener)
    time.sleep(1)
    bus.publish('testChannel', 'Hello world')
    time.sleep(10)
