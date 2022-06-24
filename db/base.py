import os
import pymongo
from passlib.context import CryptContext

from dotenv import load_dotenv

load_dotenv()

MONGODB_HOST = os.environ.get('MONGODB_HOST')
MONGODB_PORT = int(os.environ.get('MONGODB_PORT'))

CRYPT_SCHEMES = ['bcrypt', 'argon2', 'scrypt']
CRYPT_DEFAULT = 'bcrypt'
CRYPT_CFG = {
    'schemes': CRYPT_SCHEMES,
    'default': CRYPT_DEFAULT,
    'bcrypt__rounds': 14
}

DATABASE = 'tgchat'
WEBSITES_COL = 'websites'


class MongoManager:
    class __MongoManager:
        def __init__(self):
            self.client = pymongo.MongoClient(MONGODB_HOST, MONGODB_PORT)

    __instance = None

    def __init__(self):
        if not MongoManager.__instance:
            MongoManager.__instance = MongoManager.__MongoManager()

    def __getattr__(self, item):
        return getattr(self.__instance, item)


class PasswordManager:
    class __PasswordManager:
        def __init__(self):
            self.ctx = CryptContext(**CRYPT_CFG)

    __instance = None

    def __init__(self):
        if not PasswordManager.__instance:
            PasswordManager.__instance = PasswordManager.__PasswordManager()

    def __getattr__(self, item):
        return getattr(self.__instance, item)
