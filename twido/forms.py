#!/usr/bin/env python
# coding: utf-8

from django.forms import ModelForm
from django import forms
from .models import TodoList, Todo


class TodoListForm(ModelForm):
    class Meta:
        model = TodoList
        fields = ['name', 'reminder', 'related_users', 'text']
        widgets = {
            'reminder': forms.SplitDateTimeWidget(),
        }


class TodoForm(forms.ModelForm):
    class Meta:
        model = Todo
        fields = '__all__'
