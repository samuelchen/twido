"""twido URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings
from . import views


# to render full template path
def t(template):
    return 'twido/' + template

urlpatterns = [

    url(r'^admin/', include(admin.site.urls)),

    # (r'^robots\.txt$', 'django.views.generic.simple.direct_to_template', {'template': 'robots.txt', 'mimetype': 'text/plain'}),
    # (r'^favicon\.ico$', 'django.views.generic.simple.redirect_to', {'url': '/static/img/favicon.ico'}),

    url(r'^login/$', views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    url(r'', include('django.contrib.auth.urls')),
    url(r'^register/$', views.RegisterView.as_view(template_name='registration/register.html'), name='register'),
    url(r'^profile/$', views.ProfileView.as_view(template_name='registration/profile.html'), name='profile'),

    url(r'^$', views.IndexView.as_view(template_name=t('index.html')), name='index'),
    url(r'^home/$', views.HomeView.as_view(template_name=t('home.html')), name='home'),
    url(r'^setting/$', views.SettingView.as_view(template_name=t('setting.html')), name='setting'),

    url(r'^social/$', views.SocialView.as_view(template_name=t('social.html')), name='social'),
    url(r'^social/(?P<action>link)/$', views.SocialView.as_view(template_name=t('social.html')), name='social'),
    url(r'^social/(?P<action>update)/$', views.SocialView.as_view(template_name=t('social.html')), name='social'),
    url(r'^social/(?P<action>login)/$', views.SocialView.as_view(template_name=t('social.html')), name='social'),

    url(r'^list/$', views.ListView.as_view(template_name=t('list.html')), name='list'),
    url(r'^list/(?P<pk>[0-9]+)/$', views.ListView.as_view(template_name=t('list.html')), name='list'),

    url(r'^task/(?P<pk>[0-9]+)/$', views.TaskView.as_view(template_name=t('task.html')), name='task'),

    url(r'^json/usernames/$', views.ProfileUsernamesJsonView.as_view()),

    # url(r'^', include('user.urls')),

]

# debug & test
if settings.DEBUG:
    import debug_toolbar
    urlpatterns.extend([
        url(r'^test/$', views.test, name='test'),
        url(r'^test/(?P<pk>[0-9]+)/$', views.test, name='test'),
        url(r'^debug/', include(debug_toolbar.urls)),
    ])

