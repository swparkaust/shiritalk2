import glob
import os
import re
import sys

import xmltodict
from django.conf import settings
from django.core.management.base import BaseCommand
from tqdm import tqdm

from main.models import Word


class Command(BaseCommand):

    help = 'Updates dictionaries'

    def handle(self, *args, **options):
        sys.stdout.write('Clearing dictionaries ... ')
        sys.stdout.flush()
        Word.objects.all().delete()
        sys.stdout.write('done.\n')

        file_path = os.path.join(settings.BASE_DIR, 'dict/ko')
        os.chdir(file_path)
        pbar = tqdm(glob.glob("*.xml"))
        for file in pbar:
            pbar.set_description("Processing %s" % file)
            with open(file) as fd:
                doc = xmltodict.parse(fd.read(), force_list=('pos_info',))
                for word in tqdm(doc['channel']['item']):
                    if word['word_info']['word_unit'] == '단어' and any(p['pos'] == '명사' for p in word['word_info']['pos_info']):
                        pat = re.compile('^[ㄱ-ㅎ가-힣]+$')
                        x = re.sub('\d', '', word['word_info']['word'].strip().replace('-', '').replace(' ',
                                                                                                        '').replace('ㆍ', '').replace('^', ''))
                        if x and pat.match(x):
                            word_obj = Word(language='ko', word=x)
                            word_obj.save()

        sys.stdout.write(self.style.SUCCESS(
            'Successfully updated dictionaries'))
