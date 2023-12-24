from abc import abstractmethod
from typing import Dict

from communication.base import BusMessage
from communication.manager import Bus
from db.website import get_website_hosts, TOKEN_KEY, HOST_KEY, get_website_tokens_hosts
from helpers.parsing import extract_host


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

    def _unsubscribe_bus(self, token: str):
        del self._bus_websites[token]
        self._bus.unsubscribe(token, self._sub_dir)

    async def _on_bus_message(self, message: BusMessage):
        # if self.verify_bus_sender(message[DATA_KEY][HOST_KEY], message[CHANNEL_KEY]):
        #     # TODO: send an error message?
        #     return await self.on_bus_message(message)
        return await self.on_bus_message(message)

    def _update_websites(self):
        tokens_hosts = get_website_tokens_hosts()
        db_tokens = [th[TOKEN_KEY] for th in tokens_hosts]
        for bus_token in self._bus_websites:
            if bus_token not in db_tokens:
                self._unsubscribe_bus(bus_token)
        for token_host in tokens_hosts:
            if token_host[TOKEN_KEY] not in self._bus_websites:
                self._subscribe_bus(token_host[HOST_KEY], token_host[TOKEN_KEY])

    def verify_bus_sender(self, host: str, token: str):
        if token not in self._bus_websites:
            self._update_websites()
        # Clean host string from http, www, etc.
        host = extract_host(host)
        if token in self._bus_websites and self._bus_websites[token] == host:
            return True
        print(f'Token ({token}) and/or host ({host}) are incorrect! Websites = {self._bus_websites}')
        return False

    @abstractmethod
    async def on_bus_message(self, message: BusMessage):
        if message.data[TOKEN_KEY] not in self._bus_websites:
            self._update_websites()

    def send_bus_message(self, token: str, data: any):
        message = BusMessage(channel=token, direction=self._pub_dir, data=data)
        return self._bus.publish(message)
