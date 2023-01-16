import random
from datetime import datetime, timedelta

import pytz
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from main.models import ShiritalkMatch, ShiritalkPlayer, ShiritalkWord, User
from main.utils import dueum, get_words, is_hanbang


class Command(BaseCommand):

    help = 'Updates Shiritalk objects'

    def handle(self, *args, **options):
        bot_user = User.get_or_create('shiritalk')
        if not bot_user.user_name:
            bot_user.set_name("끝말톡봇")

        one_minute_ago = timezone.now() - timedelta(minutes=1)
        print(ShiritalkPlayer.objects.filter(
            last_played__lt=one_minute_ago).update(match=None))

        if ShiritalkPlayer.objects.exclude(Q(match__isnull=True) | Q(user=bot_user)).count() <= 1:
            try:
                bot_player = ShiritalkPlayer.objects.get(user=bot_user)
            except ShiritalkPlayer.DoesNotExist:
                bot_player = ShiritalkPlayer(user=bot_user)
                bot_player.save()

            match = ShiritalkMatch.objects.all().first()
            if match is None:
                match = ShiritalkMatch()
                match.save()

            bot_player.match = match
            bot_player.save(update_fields=['match', 'last_played'])
            first_letter = match.last_word.word[-1]
            if first_letter != dueum(first_letter):
                words = get_words(first_letter, method='start')|get_words(dueum(first_letter), method='start')
            else:
                words = get_words(first_letter, method='start')
            if match.last_word is None or bot_player != match.last_word.player:
                next_words = sorted(filter(lambda x: not ShiritalkWord.objects.filter(match=match, word=x).exists() and not is_hanbang(x), words), key=lambda x: -len(x))[:random.randint(20, 50)]
                word = ShiritalkWord(match=match, word=next_words[random.randint(
                    0, random.randrange(0, len(next_words)))], player=bot_player)
                word.save()
                match.last_word = word
                match.save(update_fields=['last_word'])
                bot_player.score += len(word.word)
                bot_player.save(update_fields=['score', 'last_played'])
