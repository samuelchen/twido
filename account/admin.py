#!/usr/bin/env python
# coding: utf-8
from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin  # 从django继承过来后进行定制
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.forms import UserCreationForm, UserChangeForm # admin中涉及到的两个表单
from django.utils import timezone
from .models import UserProfile, UserModel


class ProfileInline(admin.StackedInline):
    model = UserProfile
    verbose_name = 'profile'
    can_delete = False
    verbose_name_plural = 'User Profile'
    # fields = ('name', 'gender', 'timezone', 'location', 'lang', 'img_url')
    fieldsets = (
        (None, {'fields': ('username', 'name', 'gender', 'timezone', 'location', 'lang', 'img_url')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('name', 'gender', 'timezone', 'location', 'lang', 'img_url'),
        }),
    )

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return super(ProfileInline, self).get_fieldsets(request, obj)


# custom user admin
# TODO: still have problem with "add user" in admin
class MyUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = UserModel
        fields = ("email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        # super class's super. NOT incorrect. Skip USERNAME invoking in super.__init__
        super(UserCreationForm, self).__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'autofocus': ''})
        self.fields.keyOrder = ['email', 'password1', 'password2']

    def clean(self):
        """
        Normal cleanup + username generation.
        """
        cleaned_data = super(UserCreationForm, self).clean()
        if 'email' in cleaned_data:
            cleaned_data['username'] = cleaned_data['email']
        return cleaned_data


class MyUserChangeForm(UserChangeForm):

    fields = ('email', )

    def __init__(self, *args, **kwargs):
        super(MyUserChangeForm, self).__init__(*args, **kwargs)
        self.fields['email'].required = True


class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline, )
    # fields = ("email",)
    # field_classes = {'email': forms.EmailField}

    def __init__(self, *args, **kwargs):
        super(CustomUserAdmin, self).__init__(*args, **kwargs)
        self.list_display = ('id', 'email', 'profile_id', 'get_username', 'get_name', 'get_gender',
                             'is_active', 'is_staff', 'is_superuser')
        self.list_display_links = ('id', 'email', 'profile_id', 'get_username')
        self.search_fields = ('email', )
        self.form = MyUserChangeForm
        self.add_form = MyUserCreationForm

    def profile_id(self, obj):
        return obj.profile.id
    profile_id.short_description = 'Profile ID'

    def get_username(self, obj):
        return obj.profile.username
    get_username.short_description = 'Username'

    def get_name(self, obj):
        return obj.profile.name
    get_name.short_description = 'Name'

    def get_gender(self, obj):
        return obj.profile.get_gender_text()
    get_gender.short_description = 'Gender'

    def changelist_view(self, request, extra_context=None):
        if not request.user.is_superuser:
            self.fieldsets = ((None, {'fields': ('email', 'password',)}),
                              # (_('Personal info'), {'fields': ('email',)}),
                              (_('Permissions'), {'fields': ('is_active', 'is_staff', 'groups')}),
                              (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
                              )
            self.add_fieldsets = ((None, {'classes': ('wide',),
                                          'fields': ('email', 'password1', 'password2', 'is_active',
                                                     'is_staff', 'groups'),
                                          }),
                                  )
        else:
            self.fieldsets = ((None, {'fields': ('email', 'password',)}),
                              # (_('Personal info'), {'fields': ('email',)}),
                              (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups')}),
                              (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
                              )
            self.add_fieldsets = ((None, {'classes': ('wide',),
                                          'fields': ('email', 'password1', 'password2', 'is_active',
                                                     'is_staff', 'is_superuser', 'groups'),
                                          }),
                                  )
        return super(CustomUserAdmin, self).changelist_view(request, extra_context)

    def save_form(self, request, form, change):
        """
        Given a ModelForm return an unsaved instance. ``change`` is True if
        the object is being changed, and False if it's being added.
        """
        obj = super(CustomUserAdmin, self).save_form(request, form, change)

        # username should be always same as email for User model.
        obj.username = obj.email
        return obj

    def save_formset(self, request, form, formset, change):
        """
        Given an inline formset save it to the database.
        """
        objs = formset.save()

        # NOTICE: We are sure there is ONLY 1 formset and with 1 object - instance of UserProfile.
        assert len(objs) <= 1
        if len(objs) == 1:
            profile = objs[0]
            assert isinstance(profile, UserProfile)
            user = form.instance
            profile.email = user.email
            name = user.email[:user.email.find('@')]
            if not change:
                profile.username = name + str(int(timezone.now().timestamp()))
            profile.save()
        else:
            # profile should not be changed.
            pass

admin.site.unregister(UserModel)
admin.site.register(UserModel, CustomUserAdmin)