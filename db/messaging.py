from dataclasses import dataclass
from typing import List

import pymongo
from dataclasses_json import dataclass_json

from db.base import MongoManager, DATABASE
from db.website import get_website_sessions_keys

TIMESTAMP_KEY = 'timestamp'


@dataclass_json
@dataclass(frozen=True)
class ChatMessage:
    token: str
    text: str
    timestamp: int
    session: str = ''
    user: str = ''
    username: str = ''


def get_session_col_name(token: str, session_key: str):
    return f'{token[-12:]}::session: {session_key[-12:]}'


def get_session_col(token: str, session_key: str):
    db = MongoManager().client[DATABASE]
    sessions = get_website_sessions_keys(token)
    if session_key not in sessions:
        raise Exception(f'Invalid session key')
    session = db[get_session_col_name(token, session_key)]
    if 'search_index' not in session.index_information():
        session.create_index(TIMESTAMP_KEY, name='search_index', unique=True)
    return session


def add_message(message: ChatMessage) -> bool:
    try:
        session = get_session_col(message.token, message.session)
        session.insert_one(message.to_dict())
        return True
    except Exception as e:
        print(e)
        return False


def get_messages(token: str, session_key: str, amount: int = 10, full: bool = False) -> List[ChatMessage]:
    session = get_session_col(token, session_key)
    if not list(session.find()):
        return []
    if full:
        messages = session.find().sort(TIMESTAMP_KEY, pymongo.DESCENDING)
    else:
        messages = session.find().limit(amount).sort(TIMESTAMP_KEY, pymongo.DESCENDING)
    return [ChatMessage.from_dict(msg) for msg in messages]
