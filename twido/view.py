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
from django.http import JsonResponse, HttpResponseNotFound, HttpResponseBadRequest, HttpResponseRedirect, HttpResponse, \
    HttpResponseNotAllowed
from django.urls import reverse
from django.views.generic import TemplateView, View
from django.views.generic import ListView, DetailView
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib.auth import login
from django.utils.translation import ugettext as _
from django.utils import timezone
from django.db.models import Q

from .models import RawStatus
from .models import Config
from .models import Todo, Wish, UserProfile
from .models import TodoList, WishList
from .models import SocialAccount
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

from tweepy import TweepError
from .utils import TwitterClientManager
from .models import SocialPlatform
import simplejson as json


from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy

import logging
log = logging.getLogger(__name__)


# to render full template path
def t(template):
    return 'twido/' + template


# test view for some test purpose
if __debug__ and settings.DEBUG:
    def test(request):
        return render(request, t('test.html'))


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


@method_decorator(login_required, 'dispatch')
class ProfileView(TemplateView):

    def get_context_data(self, **kwargs):
        context = super(ProfileView, self).get_context_data(**kwargs)
        context['profile'] = self.request.user.profile
        if 'errors' not in context:
            context['errors'] = {}
        if 'messages' not in context:
            context['messages'] = []
        return context

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        user = self.request.user
        profile = user.profile

        # TODO: clean/escape data (better use Django form for field validation)
        req = request.POST
        profile.username = req.get('username', profile.username)
        profile.name = req.get('name', profile.name)
        gender = req.get('gender', profile.gender)
        profile.gender = bool(gender)
        profile.timezone = req.get('timezone', profile.timezone)
        profile.location = req.get('location', profile.location)
        profile.lang = req.get('lang', profile.lang)
        profile.img_url = req.get('img_url', profile.img_url)

        profile.save()
        # TODO: user.username = profile.username. transaction with user.save()

        kwargs['messages'] = [_('Profile is saved successfully.')]
        return self.get(request, *args, **kwargs)


#TODO: temp json view
@method_decorator(login_required, 'dispatch')
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


# @method_decorator(login_required, 'dispatch')
class SettingView(TemplateView):

    def get_context_data(self, **kwargs):
        context = super(SettingView, self).get_context_data(**kwargs)
        p = self.request.user.profile
        context['profile'] = p

        # TODO: optimization required
        # context['x'] = sorted(Config.objects.filter(profile=p).values('name', 'value'), key=lambda x:x['name'])
        conf = {}
        for opt in Config.objects.filter(profile=p):
            conf[opt.name] = opt
        context['conf'] = conf

        # social account linking
        context['social_platforms'] = SocialPlatform
        social_accounts = {}
        for acc in SocialAccount.objects.filter(profile=p).iterator():
            social_accounts[acc.platform] = acc
        context['social_accounts'] = social_accounts
        print(social_accounts)

        if 'errors' not in context:
            context['errors'] = {}
        if 'messages' not in context:
            context['messages'] = []
        return context

    def post(self, request, *args, **kwargs):
        # ONLY ajax call

        profile = self.request.user.profile

        # TODO: clean/escape data (better use Django form for field validation)
        req = request.POST

        # config setting request
        name = req.get('name', None)
        value = req.get('value', None)

        if name and value:
            Config.set_user_conf(profile=profile, name=name, value=value)

        return HttpResponse('')


class SocialView(TemplateView):

    def get_context_data(self, **kwargs):
        context = super(SocialView, self).get_context_data(**kwargs)
        # p = self.request.user.profile
        # context['profile'] = p
        context['social_platforms'] = SocialPlatform
        # social_accounts = {}
        # map(lambda x: social_accounts.setdefault(x.platform, x), SocialAccount.objects.filter(profile=p).iterator())
        # context['social_account'] = social_accounts

        if 'errors' not in context:
            context['errors'] = {}
        if 'messages' not in context:
            context['messages'] = []
        return context

    def get(self, request, *args, **kwargs):

        profile = self.request.user.profile

        # TODO: clean/escape data (better use Django form for field validation)
        req = request.GET

        platform = req.get('platform', None)
        action = kwargs['action'] if 'action' in kwargs else None
        log.debug('platform: %s' % platform)
        log.debug('action: %s' % action)

        if not platform:
            pass
        elif platform == SocialPlatform.TWITTER:

            if "denied" in req:
                log.warn("Denied! - Token = %s" % req.get('denied'))
                return redirect(request.path)

            if action == 'link':
                request_token = request.session.get('request_token')
                log.debug('request_token: %s' % request_token)

                access_token, access_secret = self.get_twitter_access_token(request, request_token)
                if access_token is not None:

                    tokens = {
                        "access_token": access_token,
                        "access_secret": access_secret
                    }
                    # tokens.update(request_token)
                    try:
                        acc = self.update_twitter_account(tokens=tokens, profile=profile, commit=True)
                    except AssertionError:
                        resp = HttpResponse(_('Conflict. This social account is linked with another user.'), status=409)
                        return resp

                    if acc:
                        # acc.save()
                        log.debug('Social account %s is saved.' % acc)
                    else:
                        # TODO: change response and text
                        return HttpResponseNotAllowed(_('Fail to link'))
                    # self.combine_profile_with_twitter_account(acc)

        elif platform == SocialPlatform.FACEBOOK:
            raise NotImplementedError
        elif platform == SocialPlatform.WEIBO:
            raise NotImplementedError
        else:
            raise ValueError('%s is not a supported social platform' % platform)

        return super(SocialView, self).get(request, *args, **kwargs)

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        # ONLY ajax call

        # TODO: clean/escape data (better use Django form for field validation)
        req = request.POST

        social_platform = req.get('platform', None)
        action = kwargs['action'] if 'action' in kwargs else None
        log.debug('social_platform: %s' % social_platform)
        log.debug('action: %s' % action)

        if not social_platform:
            pass    # not a social account linking request
        elif social_platform == SocialPlatform.TWITTER:
            if action == 'link':
                data = self.get_twitter_oauth_url(request)
                return JsonResponse(data)
            elif action == 'update':
                p = request.user.profile
                # return JsonResponse({'name': p.get_name() + ' ' + str(timezone.now())})
                try:
                    acc = SocialAccount.objects.get(profile=p, platform=social_platform)
                    if timezone.now() - acc.timestamp < timedelta(hours=3):
                        resp = HttpResponse(_('Too frequent (3 hours). Last update at %s.' % acc.timestamp), status=406)
                        return resp
                    self.update_twitter_account(acc, commit=True)
                    data = {'name': acc.name}
                    return JsonResponse(data)
                except SocialAccount.DoesNotExist:
                    return HttpResponseNotFound(_('You need to link your Twitter account first.'))

        elif social_platform == SocialPlatform.FACEBOOK:
            raise NotImplementedError
        elif social_platform == SocialPlatform.WEIBO:
            raise NotImplementedError
        else:
            raise ValueError('%s is not a supported social platform' % social_platform)

        return HttpResponse('')

    def get_twitter_oauth_url(self, request):
        """
        Obtain twitter oAuth authorization url. (step 1)
        :param request:
        :return:
        """
        callback_url = '%s://%s%s?platform=TW' % ('https' if request.is_secure() else 'http',
                                                request.get_host(), reverse_lazy('social', args=('link',)))
        log.debug('callback url: %s' % callback_url)
        auth = TwitterClientManager.create_oauth_handler(callback=callback_url)
        url = auth.get_authorization_url()
        log.debug('authorization_url: %s' % url)
        request_token = auth.request_token
        log.debug('request_token: %s' % request_token)

        request.session['request_token'] = request_token

        data = {
            'auth_url': url
        }
        return data

    def get_twitter_access_token(self, request, request_token):
        """
        Obtain twitter oAuth access token(s) (Step 2)
        :param request:
        :return: tuple of (access_token, access_secret)
        """
        req = request.GET
        auth = TwitterClientManager.create_oauth_handler()

        oauth_token = req.get('oauth_token', '')
        oauth_verifier = req.get('oauth_verifier', '')
        log.debug('oauth_token: %s' % oauth_token)
        log.debug('verifier: %s' % oauth_verifier)

        access_data = None
        access_token = None
        access_secret = None

        auth.request_token = request_token
        try:
            access_data = auth.get_access_token(oauth_verifier)
        except TweepError as err:
            log.debug(err)
            log.error('Error! Failed to get access token.')

        log.debug('access_data: %s' % str(access_data))
        if access_data is not None:
            access_token = access_data[0]
            access_secret = access_data[1]

        return access_token, access_secret

    def update_twitter_account(self, tokens, profile, commit=True):
        access_token = tokens['access_token']
        access_secret = tokens['access_secret']

        api = TwitterClientManager.create_api_client(access_token, access_secret)
        user = api.verify_credentials()

        if user:
            try:
                acc = SocialAccount.objects.get(account=user.screen_name, platform=SocialPlatform.TWITTER)
                assert acc.profile == profile or acc.profile == UserProfile.get_sys_profile()
            except SocialAccount.DoesNotExist:
                acc = SocialAccount()

            acc.tokens = json.dumps(tokens, indent=2, ensure_ascii=False)
            acc.profile = profile
            acc.platform = SocialPlatform.TWITTER
            acc.account = user.screen_name
            acc.name = user.name
            acc.rawid = user.id_str
            acc.created_at = user.created_at.replace(tzinfo=timezone.utc)

            acc.timezone = user.time_zone
            acc.location = user.location
            acc.lang = user.lang
            acc.utc_offset = user.utc_offset or 0
            acc.img_url = user.profile_image_url

            acc.followers_count = user.followers_count
            # acc.followings_count = user.followings_count
            acc.favorites_count = user.favourites_count
            acc.statuses_count = user.statuses_count
            acc.friends_count = user.friends_count
            acc.listed_count = user.listed_count

                # profile_background_image_url

            if commit:
                acc.save()
            else:
                # error response
                pass

            return acc

    def combine_profile_with_twitter_account(self, profile, account):
        try:
            fake_profile = UserProfile.objects.get(username=account.account)
        except UserProfile.DoesNotExist:
            return

        # TODO: investigate the performance.
        TodoList.objects.filter(profile=fake_profile).update(profile=profile)
        Todo.objects.filter(profile=fake_profile).update(profile=profile)
        WishList.objects.filter(profile=fake_profile).update(profile=profile)
        Wish.objects.filter(profile=fake_profile).update(profile=profile)
        # Appointment.objects.filter(profile=fake_profile).update(profile=profile)
        assert len(Config.objects.filter(profile=fake_profile)) == 0
        assert len(SocialAccount.objects.filter(profile=fake_profile)) == 0

        fake_profile.delete()

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

        profile_max = 10
        context['profiles'] = UserProfile.objects.exclude(
            username=UserProfile.get_sys_profile_username()).order_by('-id')[:profile_max]
        social_account_max = profile_max - len(context['profiles'])
        context['social_accounts'] = SocialAccount.objects.order_by('-id')[:social_account_max]

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

        profile = self.request.user.profile
        accs = SocialAccount.objects.filter(profile=profile).values_list('platform')
        print(accs)

        context['todolists'] = TodoList.objects.filter(profile=profile).all()
        context['wishlists'] = Wish.objects.filter(Q(profile=profile) | Q(social_account__in=accs)).all()

        return context

    # def extend_wishlist(self, wishlist):
    #     # profiles = wishlist.related_users.split(',')
    #     UserProfile.objects.filter(user__username__in=wishlist.related_users)
    #     wishlist.related_users

# @require_http_methods(['GET', ])
# def index(request):
#     context = {}
#     if request.user.is_authenticated:
#         context['user'] = 'authoried'
#     elif request.user.is_staff:
#         context['user'] = 'staff'
#     else:
#         context['user'] = 'forbiden'
#     # context = {
#     #     # "setting_keys": models.SETTING_NAMES,
#     # }
#     return render(request, t('index.html'), context=context)

@sensitive_post_parameters()
@csrf_protect
# @never_cache
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