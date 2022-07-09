import re

REPLY_TXT = 'Reply from @'
HOST_TXT = ''
TOKEN_TXT = 'WSID: '
SESSION_TXT = 'ID: '
USER_TXT = 'User: '
TEXT_TXT = '\n'


def format_host(host: str) -> str:
    return f'{HOST_TXT}<b>{host}</b>'


def format_session(session: str) -> str:
    return f'{SESSION_TXT}{session}'


def format_user(user: str) -> str:
    return f'{USER_TXT}<b>{user if user else "Unknown"}</b>'


def format_text(text: str) -> str:
    return f'{TEXT_TXT}<b>{text}</b>'


def format_reply_username(username: str) -> str:
    return f'{REPLY_TXT}{username}'


def get_host_from_msg(text: str) -> str:
    return text.split('\n')[0]


def get_session_end_from_msg(text: str) -> str:
    return re.search(f'^{SESSION_TXT}([^\n]+)', text, re.M).group(1)


def get_user_from_msg(text: str) -> str:
    return re.search(f'^{USER_TXT}([^\n]+)', text, re.M).group(1)


def get_user_txt_from_msg(text: str) -> str:
    return re.search(f'^{USER_TXT}[^\n]+\\s+(.+)', text, re.M).group(1)


def create_formatted_user_text(host, session_id, user, text) -> str:
    host = format_host(host)
    session_id = format_session(session_id)
    user = format_user(user)
    text = format_text(text)
    return '\n'.join([host, session_id, user, text])


def create_formatted_reply_text(from_user, from_user_txt,
                                host, session_key_end,
                                to_user, to_user_txt) -> str:
    return f'{format_reply_username(from_user)}' \
           f'{format_text(from_user_txt)}\n\nto\n' \
           f'{format_host(host)}\n{format_session(session_key_end)}\n' \
           f'{format_user(to_user)}\n{to_user_txt}'
