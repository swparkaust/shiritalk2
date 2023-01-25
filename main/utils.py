import math
import re

from main.models import Word


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


def get_words(q, start=False):
    pat = re.compile('^[ㄱ-ㅎ가-힣]+$')
    word_set = set()

    for i in sorted([i.word for i in (Word.objects.filter(word__startswith=q) if start else Word.objects.filter(word=q)) if pat.match(i.word) and len(i.word) >= 2], key=lambda x: -len(x)):
        word_set.add(i)

    return word_set


def is_hanbang(q):
    if q[-1] != dueum(q[-1]):
        words = get_words(q[-1], True) | get_words(dueum(q[-1]), True)
    else:
        words = get_words(q[-1], True)
    return not words
