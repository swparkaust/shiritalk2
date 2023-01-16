import datetime
import json
import random
import re
import threading
import urllib.parse
from urllib import request

from bs4 import BeautifulSoup
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.templatetags.static import static
from django.views.decorators.csrf import csrf_exempt

from main.models import (Log, ShiritalkMatch, ShiritalkPlayer, ShiritalkWord,
                         User)
from main.utils import dueum, get_words, is_hanbang

version = "1.3"


def keyboard(request):
    if True:
        return JsonResponse({'error': 'Bad Request'}, status=400)

    return JsonResponse({
        'type': 'text'
    })


@csrf_exempt
def answer(request):

    json_str = ((request.body).decode('utf-8'))
    received_json_data = json.loads(json_str)
    datacontent = received_json_data['userRequest']['utterance']
    user_key = received_json_data['userRequest']['user']['properties']['plusfriendUserKey']

    user = User.get_or_create(user_key)

    bot_user = User.get_or_create('shiritalk')
    if not bot_user.user_name:
        bot_user.set_name("끝말톡봇")

    start = datetime.datetime.now()

    cmd = datacontent.split()[0]
    data = re.sub(cmd + " ", "", datacontent)

    if user.state == 'wordchain' and (cmd == '/게임시작' or cmd == '/새로고침'):
        try:
            player = ShiritalkPlayer.objects.get(user=user)
        except ShiritalkPlayer.DoesNotExist:
            player = ShiritalkPlayer(user=user)
            player.save()
        outputs = []
        match = ShiritalkMatch.objects.all().first()
        if match is None:
            match = ShiritalkMatch()
            match.save()
            outputs.append({
                'simpleText': {
                    'text': "[끝말톡]\n %d라운드를 시작합니다.\n현재 점수: %d" % (match.round, player.score)
                }
            })
        player.match = match
        player.save(update_fields=['match', 'last_played'])

        last_ten = ShiritalkWord.objects.filter(
            match=match).order_by('-id')[:10]
        if last_ten.exists():
            items = []
            for w in last_ten:
                item = {
                    'title': w.word,
                    'description': w.player.user.user_name,
                    'buttons': [
                        {
                            'action': 'webLink',
                            'label': '표준국어대사전에서 보기',
                            'webLinkUrl': 'https://stdict.korean.go.kr/search/searchResult.do?pageSize=10&searchKeyword=' + w.word
                        }
                    ]
                }
                items.append(item)
            outputs.append({
                'carousel': {
                    'type': 'basicCard',
                    'items': items
                }
            })
        if match.last_word is None or player != match.last_word.player:
            outputs.append({
                'simpleText': {
                    'text': "[끝말톡]\n단어를 입력하세요."
                }
            })

        response_body = {
            'version': "2.0",
            'template': {
                'outputs': outputs,
                'quickReplies': [
                    {
                        'label': '🔄 새로고침',
                        'action': 'message',
                        'messageText': '/새로고침'
                    },
                    {
                        'label': '/랭킹',
                        'action': 'message',
                        'messageText': '/랭킹'
                    }
                ]
            }

        }

    elif user.state == 'wordchain' and cmd == '/랭킹':
        try:
            player = ShiritalkPlayer.objects.get(user=user)
        except ShiritalkPlayer.DoesNotExist:
            player = ShiritalkPlayer(user=user)
            player.save()

        player_list = ShiritalkPlayer.objects.exclude(user=bot_user).order_by('-score')
        paginator = Paginator(player_list, 5)  # Show 5 players per page

        page = data
        players = paginator.get_page(page)
        items = []
        for idx, p in enumerate(players):
            item = {
                'title': str(players.start_index() + idx) + ". " + p.user.user_name,
                'description': str(p.score) + "점"
            }
            items.append(item)
        quickReplies = [
            {
                'label': '뒤로',
                'action': 'message',
                'messageText': '/시작'
            },
            {
                'label': '/랭킹',
                'action': 'message',
                'messageText': '/랭킹'
            }
        ]
        if players.has_next():
            quickReplies.insert(0, {
                'label': '다음',
                'action': 'message',
                'messageText': '/랭킹 ' + str(players.next_page_number())
            })
        if players.has_previous():
            quickReplies.insert(0, {
                'label': '이전',
                'action': 'message',
                'messageText': '/랭킹 ' + str(players.previous_page_number())
            })
        response_body = {
            'version': "2.0",
            'template': {
                'outputs': [
                    {
                        'listCard': {
                            'header': {
                                'title': '🏆 랭킹'
                            },
                            'items': items
                        }
                    }
                ],
                'quickReplies': quickReplies
            }

        }

    elif user.state == 'wordchain' and not cmd.startswith('/'):
        try:
            player = ShiritalkPlayer.objects.get(user=user)
        except ShiritalkPlayer.DoesNotExist:
            player = ShiritalkPlayer(user=user)
            player.save()
        outputs = []
        match = ShiritalkMatch.objects.all().first()
        if match is None:
            match = ShiritalkMatch()
            match.save()
            outputs.append({
                'simpleText': {
                    'text': "[끝말톡]\n %d라운드를 시작합니다.\n현재 점수: %d" % (match.round, player.score)
                }
            })
        player.match = match
        player.save(update_fields=['match', 'last_played'])
        first_letter = datacontent[0]
        if hasattr(match.last_word, 'word') and dueum(first_letter) != dueum(match.last_word.word[-1]):
            outputs.append({
                'simpleText': {
                    'text': "[끝말톡]\n'" + match.last_word.word[-1] + ("(" + dueum(match.last_word.word[-1]) + ")" if match.last_word.word[-1] != dueum(match.last_word.word[-1]) else '') + "'(으)로 시작하는 단어를 입력하세요."
                }
            })
        elif match.last_word is None and is_hanbang(datacontent):
            outputs.append({
                'simpleText': {
                    'text': "[끝말톡]\n시작 시 한방단어는 사용할 수 없습니다!"
                }
            })
        elif ShiritalkWord.objects.filter(match=match, word=datacontent).exists():
            outputs.append({
                'simpleText': {
                    'text': "[끝말톡]\n이미 나온 단어입니다!"
                }
            })
        elif datacontent not in get_words(datacontent):
            outputs.append({
                'simpleText': {
                    'text': "[끝말톡]\n사전에 없는 단어입니다!"
                }
            })
        elif match.last_word is not None and player == match.last_word.player:
            outputs.append({
                'simpleText': {
                    'text': "[끝말톡]\n이번 순서에 이미 단어를 입력하셨습니다. 다른 플레이어가 단어를 입력할 때까지 계속 🔄 새로고침 버튼을 누르십시오."
                }
            })
        else:
            word = ShiritalkWord(match=match, word=datacontent, player=player)
            word.save()
            match.last_word = word
            match.save(update_fields=['last_word'])
            player.score += len(datacontent)
            outputs.append({
                'simpleText': {
                    'text': "[끝말톡]\n현재 점수: %d (+%d)\n\n팁: 다른 플레이어가 단어를 입력할 때까지 계속 🔄 새로고침 버튼을 누르십시오." % (player.score, len(datacontent))
                }
            })
            player.save(update_fields=['score', 'last_played'])
            if not ShiritalkPlayer.objects.exclude(Q(match__isnull=True) | Q(user=bot_user) | Q(user=user)).exists():
                try:
                    bot_player = ShiritalkPlayer.objects.get(user=bot_user)
                except ShiritalkPlayer.DoesNotExist:
                    bot_player = ShiritalkPlayer(user=bot_user)
                    bot_player.save()

                bot_player.match = match
                bot_player.save(update_fields=['match', 'last_played'])
                first_letter = match.last_word.word[-1]
                if first_letter != dueum(first_letter):
                    words = get_words(first_letter, method='start')|get_words(dueum(first_letter), method='start')
                else:
                    words = get_words(first_letter, method='start')
                if list(filter(lambda x: not ShiritalkWord.objects.filter(match=match, word=x).exists() and not is_hanbang(x), words)):
                    next_words = sorted(filter(lambda x: not ShiritalkWord.objects.filter(match=match, word=x).exists() and not is_hanbang(x), words), key=lambda x: -len(x))[:random.randint(20, 50)]
                    word = ShiritalkWord(match=match, word=next_words[random.randint(
                        0, random.randrange(0, len(next_words)))], player=bot_player)
                    word.save()
                    match.last_word = word
                    match.save(update_fields=['last_word'])
                    bot_player.score += len(word.word)
                    bot_player.save(update_fields=['score', 'last_played'])
                    outputs.append({
                        'simpleText': {
                            'text': "게임 서버에 플레이어가 없으므로 끝말톡봇이 대신 상대해드려요."
                        }
                    })

        last_ten = ShiritalkWord.objects.filter(
            match=match).order_by('-id')[:10]
        if last_ten.exists():
            items = []
            for w in last_ten:
                item = {
                    'title': w.word,
                    'description': w.player.user.user_name,
                    'buttons': [
                        {
                            'action': 'webLink',
                            'label': '표준국어대사전에서 보기',
                            'webLinkUrl': 'https://stdict.korean.go.kr/search/searchResult.do?pageSize=10&searchKeyword=' + w.word
                        }
                    ]
                }
                items.append(item)
            outputs.append({
                'carousel': {
                    'type': 'basicCard',
                    'items': items
                }
            })
        if hasattr(match.last_word, 'word'):
            first_letter = match.last_word.word[-1]
            if first_letter != dueum(first_letter):
                words = get_words(first_letter, method='start')|get_words(dueum(first_letter), method='start')
            else:
                words = get_words(first_letter, method='start')
            if not list(filter(lambda x: not ShiritalkWord.objects.filter(match=match, word=x).exists(), words)):
                # 라운드 종료
                match.last_word.player.win += 1
                match.last_word.player.save(
                    update_fields=['win', 'last_played'])
                match.round += 1
                outputs.append({
                    'simpleText': {
                        'text': "[끝말톡]\n" + match.last_word.player.user.user_name + "님의 승리!\n\n%d라운드를 시작합니다.\n단어를 입력하세요.\n현재 점수: %d" % (match.round, player.score)
                    }
                })
                match.last_word = None
                match.save(update_fields=['round', 'last_word'])
                ShiritalkWord.objects.filter(match=match).delete()

        response_body = {
            'version': "2.0",
            'template': {
                'outputs': outputs,
                'quickReplies': [
                    {
                        'label': '🔄 새로고침',
                        'action': 'message',
                        'messageText': '/새로고침'
                    },
                    {
                        'label': '/랭킹',
                        'action': 'message',
                        'messageText': '/랭킹'
                    }
                ]
            }

        }

    elif user.state == 'setusername' and not cmd.startswith('/'):
        if not User.objects.filter(user_name=datacontent).exists():
            try:
                user.set_name(datacontent)

                user.state = 'home'
                user.save(update_fields=['state'])

                setusername = "안녕하세요 " + user.user_name + "님! 끝말톡에 오신 것을 환영합니다!"

                response_body = {
                    'version': "2.0",
                    'template': {
                        'outputs': [
                            {
                                'simpleText': {
                                    'text': setusername
                                }
                            }
                        ],
                        'quickReplies': [
                            {
                                'label': '/시작',
                                'action': 'message',
                                'messageText': '/시작'
                            },
                            {
                                'label': '/이름변경',
                                'action': 'message',
                                'messageText': '/이름변경'
                            },
                            {
                                'label': '/도움말',
                                'action': 'message',
                                'messageText': '/도움말'
                            }
                        ]
                    }

                }
            except ValidationError as e:
                msg = str(e.message_dict['user_name'][0])
                setusername = msg + "\n다른 사용자 이름을 입력하세요."

                response_body = {
                    'version': "2.0",
                    'template': {
                        'outputs': [
                            {
                                'simpleText': {
                                    'text': setusername
                                }
                            }
                        ]
                    }

                }
        else:
            setusername = "사용자 이름이 이미 존재합니다.\n다른 사용자 이름을 입력하세요."

            response_body = {
                'version': "2.0",
                'template': {
                    'outputs': [
                        {
                            'simpleText': {
                                'text': setusername
                            }
                        }
                    ]
                }

            }

    elif cmd == '/이름변경':
        user.state = 'setusername'
        user.save(update_fields=['state'])

        setusername = "끝말톡에서 사용할 사용자 이름을 입력하세요."

        response_body = {
            'version': "2.0",
            'template': {
                'outputs': [
                    {
                        'simpleText': {
                            'text': setusername
                        }
                    }
                ]
            }

        }

    elif cmd == '/시작':
        user.state = 'wordchain'
        user.save(update_fields=['state'])

        player_count = ShiritalkPlayer.objects.exclude(
            Q(match__isnull=True) | Q(user=bot_user)).count()

        wordchain = "[끝말톡]\n카카오톡 끝말잇기 온라인, 끝말톡 온라인에 오신 것을 환영합니다.\n\n👥 접속자 수 [" + \
            str(player_count) + "명]\n\n한국어 단어에 대한 모든 저작권은 국립국어원에 있습니다."

        response_body = {
            'version': "2.0",
            'template': {
                'outputs': [
                    {
                        'basicCard': {
                            'description': wordchain,
                            'thumbnail': {
                                'imageUrl': request.build_absolute_uri(static('wordchain.png')),
                                'fixedRatio': True
                            },
                            'buttons': [
                                {
                                    'action': 'message',
                                    'label': '게임 시작!',
                                    'messageText': '/게임시작'
                                }
                            ]
                        }
                    }
                ],
                'quickReplies': [
                    {
                        'label': '/랭킹',
                        'action': 'message',
                        'messageText': '/랭킹'
                    }
                ]
            }

        }

    else:
        user.state = 'home'
        user.save(update_fields=['state'])

        help = "봇 이름 : 끝말톡\n버전 : " + version + \
            "\n제작자 : 선우\n\n 시작하려면 /시작을 사용하십시오."

        response_body = {
            'version': "2.0",
            'template': {
                'outputs': [
                    {
                        'simpleText': {
                            'text': help
                        }
                    }
                ],
                'quickReplies': [
                    {
                        'label': '/시작',
                        'action': 'message',
                        'messageText': '/시작'
                    },
                    {
                        'label': '/이름변경',
                        'action': 'message',
                        'messageText': '/이름변경'
                    },
                    {
                        'label': '/도움말',
                        'action': 'message',
                        'messageText': '/도움말'
                    }
                ]
            }

        }

    time_diff = datetime.datetime.now() - start

    if not user.user_name:
        user.state = 'setusername'
        user.save(update_fields=['state'])

        setusername = "사용자 이름이 설정되지 않았습니다.\n끝말톡에서 사용할 사용자 이름을 입력하세요."

        response_body = {
            'version': "2.0",
            'template': {
                'outputs': [
                    {
                        'simpleText': {
                            'text': setusername
                        }
                    }
                ]
            }

        }

    Log.write(user, datacontent, str(response_body), time_diff.total_seconds())

    return JsonResponse(response_body)
