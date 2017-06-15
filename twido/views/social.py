#!/usr/bin/env python
# coding: utf-8
from datetime import timedelta
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse, HttpResponseNotFound
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_variables
from django.views.generic import TemplateView
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
import simplejson as json
from .base import BaseViewMixin
from ..models import UserProfile, SocialPlatform, SocialAccount
from ..models import replace_profile
from ..utils import load_config
from social.twitter import TwitterClientManager

import logging

log = logging.getLogger(__name__)
cfg = load_config(settings.CONFIG_FILE)


class I18N_MSGS(object):
    denied = _('Denied!'),
    social_fail_to_link = _('Fail to link social account.'),
    social_conflict_link = _('Conflict. This social account is linked with another user.')
    too_frequent = _('Too frequent (3 hours). Last time was at %s.')
    social_link_first = _('You need to link your social account first.')
    social_link_success = _('You are successfully linked to your social account.')
    social_profile_updated = _('Your social profile is updated.')
    social_fail_to_get_token = _('Error! Failed to get access token.')


class SocialView(TemplateView, BaseViewMixin):

    def get_context_data(self, **kwargs):
        context = super(SocialView, self).get_context_data(**kwargs)
        # p = self.request.user.profile
        # context['profile'] = p
        context['social_platforms'] = SocialPlatform
        # social_accounts = {}
        # map(lambda x: social_accounts.setdefault(x.platform, x), SocialAccount.objects.filter(profile=p).iterator())
        # context['social_account'] = social_accounts

        return context

    def get(self, request, *args, **kwargs):

        profile = self.get_profile()

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
                self.warn(I18N_MSGS.denied)
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


                    acc = self.update_twitter_account(tokens=tokens, profile=profile, commit=True)

                    if acc:
                        profile = self.combine_profile_with_twitter_account(request, profile=profile, social_account=acc)
                        log.debug('Social account %s is updated.' % acc)
                    else:
                        # TODO: change response and text
                        return HttpResponseNotAllowed(I18N_MSGS.social_fail_to_link)

                    self.success(I18N_MSGS.social_link_success)
            elif action == 'login':
                data = self.get_twitter_oauth_url(request)
                return redirect(data['auth_url'])

        elif platform == SocialPlatform.FACEBOOK:
            raise NotImplementedError
        elif platform == SocialPlatform.WEIBO:
            raise NotImplementedError
        else:
            raise ValueError('%s is not a supported social platform' % platform)

        return super(SocialView, self).get(request, *args, **kwargs)


    @sensitive_variables()
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
                        resp = HttpResponse(I18N_MSGS.too_frequent % acc.timestamp, status=406)
                        return resp
                    self.update_twitter_account(json.loads(acc.tokens), acc.profile, commit=True)
                    data = {'name': acc.name}
                    self.success(I18N_MSGS.social_profile_updated)
                    return JsonResponse(data)
                except SocialAccount.DoesNotExist:
                    return HttpResponseNotFound(I18N_MSGS.social_link_first)
            elif action == 'login':
                pass
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
        auth = TwitterClientManager.create_oauth_handler(consumer_key=cfg.twitter.consumer_key,
                                                         consumer_secret=cfg.twitter.consumer_secret,
                                                         callback=callback_url, proxy=cfg.common.proxy)
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
        auth = TwitterClientManager.create_oauth_handler(consumer_key=cfg.twitter.consumer_key,
                                                         consumer_secret=cfg.twitter.consumer_secret,
                                                         proxy=cfg.common.proxy)

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
        except TwitterClientManager.TweepError as err:
            self.error(I18N_MSGS.social_fail_to_get_token)
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

        user = None
        try:
            oauth = TwitterClientManager.create_oauth_handler(consumer_key=cfg.twitter.consumer_key,
                                                              consumer_secret=cfg.twitter.consumer_secret,
                                                              proxy=cfg.common.proxy)
            api = TwitterClientManager.create_api_client(oauth_handler=oauth, access_token=access_token,
                                                         access_token_secret=access_secret, proxy=cfg.common.proxy)
            user = api.verify_credentials()
        except TwitterClientManager.TweepError as err:
            msg = str(err)
            log.error(msg)
            err_dict = json.loads(msg)
            sb = []
            for code, msg in err_dict:
                sb.append('%s: %s' % (code, msg))
            msg = '</li><li>'.join(sb)
            msg = '<li>' + msg + '</li>'
            msg = _('Twitter service error:') % msg
            self.error(_(msg))
            return None

        if user:
            try:
                acc = SocialAccount.objects.get(account=user.screen_name, platform=SocialPlatform.TWITTER)
            except SocialAccount.DoesNotExist:
                acc = SocialAccount(profile=profile)

            acc.tokens = json.dumps(tokens, indent=2, ensure_ascii=False)
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

            if commit:
                acc.save()

            return acc

    def combine_profile_with_twitter_account(self, request, profile, social_account):

        acc = social_account

        # Complex. Check https://github.com/samuelchen/twido/wiki/Social
        # TODO: relink (or unlink then link)
        if profile.is_sys:
            if acc.profile.is_sys:
                profile, password = UserProfile.register_temp(username=acc.account, platform=SocialPlatform.TWITTER,
                                                              img_url=acc.img_url)
                acc.profile = profile
                acc.save()
                self.info(_('Your user profile is created. <br>Password is "%s". Please remember and change it.') % password)
            login(request, acc.profile.user)
            profile = self.get_profile()
            log.info('Login with twitter.')

        else:
            if profile != acc.profile and not acc.profile.is_sys:
                # already linked to another profile (should be you)
                if acc.profile.is_temp:
                    # temp account, relink.
                    log.info('Auto combine profile "%s" and "%s"' % (profile, acc.profile))
                    replace_profile(origin_profile=acc.profile, new_profile=profile,
                                    social_platform=SocialPlatform.TWITTER)
                else:
                    # TODO: change profile ?
                    log.warn('Conflict. Social account "%s" was linked to "%s" already.'
                             % (acc, acc.profile))
                    return HttpResponse(I18N_MSGS.social_conflict_link, status=409)

        return profile