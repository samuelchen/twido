#!/usr/bin/env python
# coding: utf-8

from django.contrib import admin
from django.contrib.auth.models import User
from .models import UserProfile


# Register your models here.
class ProfileInline(admin.StackedInline):
    model = UserProfile
    verbose_name = 'profile'


class UserProfileAdmin(admin.ModelAdmin):
    inlines = (ProfileInline,)


admin.site.unregister(User)
admin.site.register(User, UserProfileAdmin)