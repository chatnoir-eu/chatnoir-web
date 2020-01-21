from django.contrib import admin

from .models import *

admin.site.register(IssueKey)
admin.site.register(Passcode)
admin.site.register(User)
admin.site.register(PendingUser)
