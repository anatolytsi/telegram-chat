import re
import uuid
from typing import List

from db.base import MongoManager, DATABASE, WEBSITES_COL, PasswordManager

TOKEN_KEY = 'token'
USERNAME_KEY = 'username'
USER_CHANNEL_KEY = 'channel'
HOST_KEY = 'host'
ALIAS_KEY = 'alias'
CREATOR_KEY = 'creator'
PASSWORD_KEY = 'password'
SUBS_KEY = 'subscribers'
SESSIONS_KEY = 'sessions'
WEBSITES_PROTO = {
    TOKEN_KEY: '',
    HOST_KEY: '',
    ALIAS_KEY: '',
    CREATOR_KEY: '',
    PASSWORD_KEY: '',
    SUBS_KEY: None,
    SESSIONS_KEY: None,
}


def get_websites_col():
    db = MongoManager().client[DATABASE]
    websites = db[WEBSITES_COL]
    if 'search_index' not in websites.index_information():
        websites.create_index(TOKEN_KEY, name='search_index', unique=True)
    return websites


def verify_login(website, password: str) -> bool:
    return website and PasswordManager().ctx.verify(password, website[PASSWORD_KEY])


def get_website_privileged(websites, token: str, password: str):
    website = websites.find_one({TOKEN_KEY: token})
    if not website:
        raise Exception('Incorrect token')
    if not verify_login(website, password):
        raise Exception('Incorrect credentials')
    return website


def get_website(websites, token: str):
    website = websites.find_one({TOKEN_KEY: token})
    if not website:
        raise Exception('Incorrect token')
    return website


def get_full_token(token_end: str) -> str:
    websites = get_websites_col()
    website = websites.find_one({TOKEN_KEY: {'$regex': f'-{token_end}$'}})
    return website[TOKEN_KEY]


def get_full_session_key(token: str, session_end: str) -> str:
    try:
        websites = get_websites_col()
        website = get_website(websites, token)
        return list(filter(re.compile(f'-{session_end}$').search, website[SESSIONS_KEY]))[0]
    except Exception as e:
        print(e)
        return ''


def delete_db():
    MongoManager().client.drop_database(DATABASE)


def get_all_websites():
    return list(get_websites_col().find({}))


def get_website_hosts():
    exception = {
        ALIAS_KEY: 0,
        CREATOR_KEY: 0,
        PASSWORD_KEY: 0,
        SUBS_KEY: 0,
        SESSIONS_KEY: 0,
    }
    return list(get_websites_col().find({}, exception))


def get_website_subscribers(token: str):
    exception = {
        HOST_KEY: 0,
        ALIAS_KEY: 0,
        CREATOR_KEY: 0,
        PASSWORD_KEY: 0,
        SESSIONS_KEY: 0,
    }
    query = get_websites_col().find_one({TOKEN_KEY: token}, exception)
    if query:
        return query[SUBS_KEY]
    return []


def add_website(username: str, user_channel: int, host: str, alias: str, password: str) -> str:
    websites = get_websites_col()
    token = f'{uuid.uuid4()}'
    password_hash = PasswordManager().ctx.hash(password)
    website = {
        TOKEN_KEY: token,
        HOST_KEY: host,
        ALIAS_KEY: alias,
        CREATOR_KEY: username,
        PASSWORD_KEY: password_hash,
        SUBS_KEY: [{USERNAME_KEY: username, USER_CHANNEL_KEY: user_channel}],
        SESSIONS_KEY: []
    }
    websites.insert_one(website)
    return token


def remove_website(username: str, token: str, password: str) -> str:
    try:
        websites = get_websites_col()
        website = get_website_privileged(websites, token, password)
        alias = website[ALIAS_KEY]
        if username != website[CREATOR_KEY]:
            return 'Only creator is allowed to remove a website'
        websites.delete_one(website)
        return alias
    except Exception as e:
        print(e)
        return str(e)


def create_session_website(token: str) -> str:
    try:
        websites = get_websites_col()
        website = get_website(websites, token)
        session_key = f'{uuid.uuid4()}'
        website[SESSIONS_KEY].append(session_key)
        websites.replace_one({TOKEN_KEY: token}, website, upsert=True)
        return session_key
    except Exception as e:
        print(e)
        return ''


def get_website_sessions(token: str) -> List[str]:
    websites = get_websites_col()
    website = get_website(websites, token)
    return website[SESSIONS_KEY]


def subscribe_website(username: str, user_channel: int, token: str, password: str) -> str:
    try:
        websites = get_websites_col()
        website = get_website_privileged(websites, token, password)
        if username not in website[SUBS_KEY]:
            website[SUBS_KEY].append({USERNAME_KEY: username, USER_CHANNEL_KEY: user_channel})
            websites.replace_one({TOKEN_KEY: token}, website, upsert=True)
        return website[ALIAS_KEY]
    except Exception as e:
        print(e)
        return ''


def unsubscribe_website(username: str, token: str, password: str) -> str:
    try:
        websites = get_websites_col()
        website = get_website_privileged(websites, token, password)
        if username in website[SUBS_KEY]:
            website[SUBS_KEY].remove(username)
            websites.update_one(website)
        return website[ALIAS_KEY]
    except Exception as e:
        print(e)
        return ''


if __name__ == '__main__':
    delete_db()
    # print(get_all_websites())
    token = add_website('test', 299617516, '127.0.0.1', 'Test Website', '12345678')
    print(token)
    # status = subscribe_website('test_user', 299617516, token, '12345678')
