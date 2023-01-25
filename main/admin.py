from django.contrib import admin

from .models import (Group, Log, Mail, ShiritalkMatch, ShiritalkPlayer,
                     ShiritalkWord, User, Word)

admin.site.register(Group)
admin.site.register(User)
admin.site.register(Mail)
admin.site.register(Log)
admin.site.register(ShiritalkMatch)
admin.site.register(ShiritalkPlayer)
admin.site.register(ShiritalkWord)
admin.site.register(Word)
