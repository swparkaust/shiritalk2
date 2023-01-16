import math
import random
import re
import requests
import requests_cache
import xmltodict

from django.conf import settings

requests_cache.install_cache('stdict_cache')


def dueum(s):
    c = ord(s[0]) - 44032
    b = c % 28
    n = chr(math.trunc(c / 28) * 28 + 44032)
    if n == '녀':
        n = '여'
    elif n == '뇨':
        n = '요'
    elif n == '뉴':
        n = '유'
    elif n == '니':
        n = '이'
    elif n == '랴':
        n = '야'
    elif n == '려':
        n = '여'
    elif n == '례':
        n = '예'
    elif n == '료':
        n = '요'
    elif n == '류':
        n = '유'
    elif n == '리':
        n = '이'
    elif n == '라':
        n = '나'
    elif n == '래':
        n = '내'
    elif n == '로':
        n = '노'
    elif n == '뢰':
        n = '뇌'
    elif n == '루':
        n = '누'
    elif n == '르':
        n = '느'
    return chr(ord(n[0]) + b)


def stdict_search(q, **kwargs):
    payload = {
        'key': settings.STDICT_KEY,
        'q': q,
        'advanced': 'y',
        'type1': 'word',
        'pos': 1,
        'letter_s': 2
    }
    for key, value in kwargs.items():
        payload[key] = value

    r = requests.get('https://stdict.korean.go.kr/api/search.do', params=payload)
    data = xmltodict.parse(r.content, force_list=('item',))

    if int(data['channel']['total']) > int(data['channel']['num']) and 'start' not in kwargs:
        result = stdict_search(q, start=random.randint(1, math.ceil(int(data['channel']['total']) / int(data['channel']['num']))), **kwargs)
    else:
        result = [d.get('word') for d in data.get('channel', {}).get('item', {})]
    return result


def get_words(q, **kwargs):
    pat = re.compile('^[ㄱ-ㅎ가-힣]+$')
    word_set = set()

    for i in sorted([i for i in stdict_search(q, **kwargs)], key=lambda x: -len(x)):
        x = i.strip().replace('-', '').replace(' ', '').replace('ㆍ', '').replace('^', '')
        if x and pat.match(x) and len(x) >= 2:
            word_set.add(x)
            
    return word_set


def is_hanbang(q):
    if q[-1] != dueum(q[-1]):
        words = get_words(q[-1], method='start')|get_words(dueum(q[-1]), method='start')
    else:
        words = get_words(q[-1], method='start')
    return not words
