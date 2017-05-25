#!/usr/bin/env python
# coding: utf-8

from django.forms import ModelForm
from django import forms
from .models import Task, UserProfile
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model
from django.db import transaction
import logging
from django.utils import timezone
log = logging.getLogger(__name__)

UserMode = get_user_model()


class I18N_MSGS(object):
    email_lable = _("Email")
    email_help = _("Enter the user email.")
    email_exists = _('A user with that email already exists.')
    email_required = _('Email is required.')


class UserProfileCreationForm(UserCreationForm):
    """
    Django User is used for authorization (login/logout/register). User.username will always set to User.email.
    """
    email = forms.EmailField(
        label=I18N_MSGS.email_lable,
        widget=forms.EmailInput,
        strip=True,
        help_text=I18N_MSGS.email_help,
    )

    class Meta:
        model = UserMode
        fields = ("email", "username")
        field_classes = {'email': forms.EmailField, 'username': forms.CharField}

    def __init__(self, *args, **kwargs):
        super(UserProfileCreationForm, self).__init__(*args, **kwargs)
        if 'email' in self.fields:
            self.fields['email'].widget.attrs.update({'autofocus': ''})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError(
                I18N_MSGS.email_required,
                code='email_required'
            )
        try:
            profile = UserProfile.objects.get(email=email)
            if profile and profile.user:
                raise forms.ValidationError(
                    I18N_MSGS.email_exists,
                    code='email_exists'
                )
        except UserProfile.DoesNotExist:
            pass
        return email

    def clean(self):
        cleaned_data = super(UserProfileCreationForm, self).clean()
        email = cleaned_data.get('email')
        username = cleaned_data.get('username')
        if not username:
            cleaned_data['username'] = email

        return cleaned_data

    def save(self, commit=True):
        """

        :param commit: whether save to DB. If False, will only create instance without save to DB.)
        :return: UserProfile instance (not User instance, use profile.user to access user instance)
        """
        user = super(UserProfileCreationForm, self).save(commit=False)
        # user.is_active = False  # need to verify email.
        email = self.cleaned_data['email']
        assert user
        if not user.username:
            user.username = email
        assert user.username
        profile = None
        if commit:
            with transaction.atomic():
                user.save()
                assert user and user.username
                profile, created = UserProfile.objects.get_or_create(user=user)
                profile.email = email
                if created:
                    log.warn('Profile was not created after User created. (%s)' % user.username)
                    profile.name = user.email[:user.email.find('@')]
                    profile.username = profile.name + str(int(timezone.now().timestamp()))
                profile.save()
        return profile



# class TodoListForm(ModelForm):
#     class Meta:
#         model = TodoList
#         fields = ['name', 'reminder', 'related_users', 'text']
#         widgets = {
#             'reminder': forms.SplitDateTimeWidget(),
#         }
#
#
# class TodoForm(forms.ModelForm):
#     class Meta:
#         model = Todo
#         fields = '__all__'
