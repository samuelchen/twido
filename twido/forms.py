#!/usr/bin/env python
# coding: utf-8

from django.forms import ModelForm
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model
from django.db import transaction
import logging
from django.utils import timezone
log = logging.getLogger(__name__)

UserMode = get_user_model()



# class TodoListForm(ModelForm):
#     class Meta:
#         model = TodoList
#         fields = ['name', 'due', 'related_users', 'text']
#         widgets = {
#             'due': forms.SplitDateTimeWidget(),
#         }
#
#
# class TodoForm(forms.ModelForm):
#     class Meta:
#         model = Todo
#         fields = '__all__'
