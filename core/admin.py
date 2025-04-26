from django.contrib import admin

from .models import Profile, Letter, LetterLike, Match  # 👈 import your models

admin.site.register(Profile)
admin.site.register(Letter)
admin.site.register(LetterLike)
admin.site.register(Match)