from abc import abstractmethod
from typing import Dict

from communication.base import CHANNEL_KEY
from communication.manager import Bus
from db.website import get_website_hosts, TOKEN_KEY, HOST_KEY


class BusMixin:
    def __init__(self, *args, sub_dir, pub_dir, **kwargs):
        super().__init__(*args, **kwargs)
        self._bus: Bus = Bus()
        self._bus_websites: Dict[str, str] = {}
        self._sub_dir = sub_dir
        self._pub_dir = pub_dir
        self._subscribe_to_all_buses()

    def _subscribe_to_all_buses(self):
        websites = get_website_hosts()

        for website in websites:
            token = website[TOKEN_KEY]
            host = website[HOST_KEY]
            self._subscribe_bus(host, token)

    def _subscribe_bus(self, host: str, token: str):
        self._bus_websites[token] = host
        self._bus.subscribe(token, self._sub_dir, lambda msg: self._on_bus_message(msg))

    async def _on_bus_message(self, message: any):
        # if self.verify_bus_sender(message[DATA_KEY][HOST_KEY], message[CHANNEL_KEY]):
        #     # TODO: send an error message?
        #     return await self.on_bus_message(message)
        return await self.on_bus_message(message)

    def verify_bus_sender(self, host: str, token: str):
        if token in self._bus_websites and self._bus_websites[token] == host:
            return True
        print(f'Token and/or host are incorrect')
        return False

    @abstractmethod
    async def on_bus_message(self, message: any):
        pass

    def send_bus_message(self, token: str, message: any):
        return self._bus.publish(token, self._pub_dir, message)

    @staticmethod
    def get_bus_channel(message: any):
        return message[CHANNEL_KEY]
