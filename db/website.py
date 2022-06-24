import uuid

from db.base import MongoManager, DATABASE, WEBSITES_COL, PasswordManager

TOKEN_KEY = 'token'
HOST_KEY = 'host'
ALIAS_KEY = 'alias'
CREATOR_KEY = 'creator'
PASSWORD_KEY = 'password'
SUBS_KEY = 'subscribers'
WEBSITES_PROTO = {
    TOKEN_KEY: '',
    HOST_KEY: '',
    ALIAS_KEY: '',
    CREATOR_KEY: '',
    PASSWORD_KEY: '',
    SUBS_KEY: None,
}


def get_websites_col():
    db = MongoManager().client[DATABASE]
    websites = db[WEBSITES_COL]
    if 'search_index' not in websites.index_information():
        websites.create_index(TOKEN_KEY, name='search_index', unique=True)
    return websites


def verify_login(website, password: str) -> bool:
    return website and PasswordManager().ctx.verify(password, website[PASSWORD_KEY])


def get_website(websites, token: str, password: str):
    website = websites.find_one({TOKEN_KEY: token})
    if not website:
        raise Exception('Incorrect token')
    if not verify_login(website, password):
        raise Exception('Incorrect credentials')
    return website


def add_website(username: str, host: str, alias: str, password: str) -> str:
    websites = get_websites_col()
    token = f'{uuid.uuid4()}'
    password_hash = PasswordManager().ctx.hash(password)
    website = {
        TOKEN_KEY: token,
        HOST_KEY: host,
        ALIAS_KEY: alias,
        CREATOR_KEY: username,
        PASSWORD_KEY: password_hash,
        SUBS_KEY: [username]
    }
    websites.insert_one(website)
    return token


def remove_website(username: str, token: str, password: str) -> str:
    try:
        websites = get_websites_col()
        website = get_website(websites, token, password)
        if username != website[CREATOR_KEY]:
            return 'Only creator is allowed to remove a website'
        websites.delete_one(website)
    except Exception as e:
        print(e)
        return str(e)
    return ''


def subscribe_website(username: str, token: str, password: str) -> bool:
    try:
        websites = get_websites_col()
        website = get_website(websites, token, password)
        if username not in website[SUBS_KEY]:
            website[SUBS_KEY].append(username)
            websites.replace_one({TOKEN_KEY: token}, website, upsert=True)
        return True
    except Exception as e:
        print(e)
        return False


def unsubscribe_website(username: str, token: str, password: str) -> bool:
    try:
        websites = get_websites_col()
        website = get_website(websites, token, password)
        if username in website[SUBS_KEY]:
            website[SUBS_KEY].remove(username)
            websites.update_one(website)
        return True
    except Exception as e:
        print(e)
        return False


if __name__ == '__main__':
    token = add_website('test', 'test_website.com', 'Test Website', '12345678')
    status = subscribe_website('test_user', token, '12345678')

