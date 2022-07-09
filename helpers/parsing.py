import re

HOST_CLEAN_PATTERNS = (re.compile(r'(https://)?'),
                       re.compile(r'(http://)?'),
                       re.compile(r'(www\.)?'),
                       re.compile(r'(/$)?'))


def extract_host(host: str):
    for pattern in HOST_CLEAN_PATTERNS:
        host = pattern.sub('', host)
    host = host if host != 'null' and host != '127.0.0.1' else 'localhost'
    return host
