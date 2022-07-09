import re

HOST_CLEAN_PATTERNS = (re.compile(r'(https://)?'),
                       re.compile(r'(http://)?'),
                       re.compile(r'(www\.)?'),
                       re.compile(r'(/$)?'))


def extract_host(host: str):
    for pattern in HOST_CLEAN_PATTERNS:
        host = pattern.sub('', host)
    return host
