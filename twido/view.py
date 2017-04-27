#!/usr/bin/env python
# coding: utf-8

"""
views
"""

from django.conf import settings
from django.shortcuts import render, get_list_or_404, get_object_or_404
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse, HttpResponseNotFound, HttpResponseBadRequest, HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.views.generic import TemplateView, View
from django.views.generic import ListView, DetailView
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib.auth import login
from django.utils.translation import ugettext as _

from .models import RawStatus
from .models import Todo, Wish, UserProfile
from .models import TodoList, WishList
from pyutils.langutil import MutableEnum
from .utils import parse_datetime
from .forms import TodoListForm, TodoForm
from .forms import UserProfileCreationForm

import dateparser

from datetime import datetime, timedelta

from pygments.lexers.html import XmlLexer
from pygments.formatters.html import HtmlFormatter
from pygments import highlight
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


import logging
log = logging.getLogger(__name__)


# to render full template path
def t(template):
    return 'twido/' + template


# test view for some test purpose
if __debug__ and settings.DEBUG:
    def test(request):
        return render(request, t('test.html'))

from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy


class TodoDetailView(DetailView):
    model = Todo

class TodoCreateView(CreateView):
    model = Todo
    fields = ['title', 'profile', 'labels', 'text', 'list']

class TodoUpdateView(UpdateView):
    model = Todo
    fields = ['title', 'profile', 'labels', 'text', 'list']

class TodoDeleteView(DeleteView):
    model = Todo
    success_url = reverse_lazy('home')


class TodoListView(DetailView):
    model = TodoList
    context_object_name = 'thelist'

    def get_context_data(self, **kwargs):
        context = super(TodoListView, self).get_context_data(**kwargs)
        thelist = context['object']
        p = self.request.GET.get('p')
        context['thelist'] = thelist
        # context['todos'] = Todo.objects.filter(profile__user=self.request.user, list=thelist).all()
        context['page'] = paginate(thelist.todo_set.all(), cur_page=p, entries_per_page=10)
        context['todolists'] = TodoList.objects.filter(profile__user=self.request.user).all()

        context['form'] = TodoListForm()
        return context

    @method_decorator(sensitive_post_parameters)
    def post(self, request, *args, **kwargs):
        req = request.POST
        pk = req.get('pk', None)        # id
        if pk is not None:
            pk = int(pk)
            name = req.get('name', None)
            value = req.get('value', None)
            lst = TodoList.objects.get(id=pk)
            setattr(lst, name, value)
            lst.save(update_fields=[name, ])
        return HttpResponse('')


class ProfileView(TemplateView):

    def get_context_data(self, **kwargs):
        context = super(ProfileView, self).get_context_data(**kwargs)
        context['profile'] = self.request.user.profile
        if 'errors' not in context:
            context['errors'] = []
        if 'messages' not in context:
            context['messages'] = []
        return context

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        user = self.request.user
        profile = user.profile

        # TODO: clean/escape data
        req = request.POST
        profile.username = req.get('username', profile.username)
        profile.name = req.get('name', profile.name)
        gender = req.get('gender', profile.gender)
        profile.gender = bool(gender)
        profile.timezone = req.get('timezone', profile.timezone)
        print(req.get('timezone'), profile.timezone)
        profile.location = req.get('location', profile.location)
        profile.lang = req.get('lang', profile.lang)
        profile.img_url = req.get('img_url', profile.img_url)

        profile.save()
        # TODO: user.username = profile.username. transaction with user.save()

        kwargs['messages'] = [_('Profile is saved successfully.')]
        return self.get(request, *args, **kwargs)


class ProfileUsernamesJsonView(View):

    def get(self, request, *args, **kwargs):
        log.debug('%s %s' % (request, request.POST))
        usernames = []
        for uname in UserProfile.objects.values_list('username', flat=True):
            usernames.append({
                "id": uname,
                "text": uname
            })
        return JsonResponse(usernames, safe=False)


class IndexView(TemplateView):

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect("/home")
        else:
            return super(IndexView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)

        context['todos'] = Todo.objects.all()[:10]
        context['wishes'] = Wish.objects.all()[:10]
        delta = timedelta(days=7)
        dt = datetime.utcnow() - delta
        # context['profiles'] = UserProfile.objects.filter(user__date_joined__gt=dt).order_by('-user__date_joined')[:10]
        context['profiles'] = UserProfile.objects.order_by('-id')[:10]


        formatter = HtmlFormatter(encoding='utf-8', style='emacs', linenos=True)
        lexer = XmlLexer()
        for task in context['todos']:
            task.text = highlight(task.content, lexer, formatter)

            # print(task.title)
            xml = ET.fromstring(task.content)
            task.dates = []
            for node in xml.findall("./TEXT/TIMEX3"):
                dt = MutableEnum()
                dt.text = node.text
                # print(node.text)
                for k, v in node.items():
                    # print('  ', k, v)
                    dt[k] = v
                if dt.type == 'DATE' and dt.text:
                    try:
                        dt.v = dateparser.parse(dt.text)
                        # dt.v = parse_datetime(dt.text)
                    except Exception as err:
                        log.warn(err)
                        dt.v = None
                task.dates.append(dt)
        context['css'] = formatter.get_style_defs()

        return context


class HomeView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)

        context['todolists'] = TodoList.objects.filter(profile__user=self.request.user).all()
        context['wishlists'] = Wish.objects.filter(profile__user=self.request.user).all()

        return context

    # def extend_wishlist(self, wishlist):
    #     # profiles = wishlist.related_users.split(',')
    #     UserProfile.objects.filter(user__username__in=wishlist.related_users)
    #     wishlist.related_users

@require_http_methods(['GET', ])
def index(request):
    context = {}
    if request.user.is_authenticated:
        context['user'] = 'authoried'
    elif request.user.is_staff:
        context['user'] = 'staff'
    else:
        context['user'] = 'forbiden'
    # context = {
    #     # "setting_keys": models.SETTING_NAMES,
    # }
    return render(request, t('index.html'), context=context)

@sensitive_post_parameters()
@csrf_protect
def register(request):
    success = False
    profile = None

    if request.method == "POST":
        form = UserProfileCreationForm(data=request.POST)
        if form.is_valid():
            profile = form.save()
            success = True
    else:
        form = UserProfileCreationForm()

    context = {
        'form': form,
        'success': success
    }

    if success and profile and profile.user and profile.user.is_active:
        login(request, profile.user)
        context['messages'] = [_('Registration succeed.'),
                               _('Please update your <a href="#">profile</a>.')]

    return render(request, 'registration/register.html', context)

@require_http_methods(['GET', ])
def test(request, pk=None):
    log.debug('%s %s %s' % (request, pk, request.POST))
    context = {}
    if request.user.is_authenticated:
        context['user'] = 'authoried'
    elif request.user.is_staff:
        context['user'] = 'staff'
    else:
        context['user'] = 'forbiden'
    # context = {
    #     # "setting_keys": models.SETTING_NAMES,
    # }
    print(dir(request))
    return render(request, 'test/test%s.html' % (pk if pk else ''), context=context)


def paginate(objects, cur_page=1, entries_per_page=15):
    paginator = Paginator(objects, entries_per_page)

    page = None
    try:
        page = paginator.page(cur_page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        page = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        page = paginator.page(paginator.num_pages)

    return page