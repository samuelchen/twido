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
from . import view


# to render full template path
def t(template):
    return 'twido/' + template

urlpatterns = [

    url(r'^admin/', include(admin.site.urls)),
    url(r'', include('django.contrib.auth.urls')),

    # (r'^robots\.txt$', 'django.views.generic.simple.direct_to_template', {'template': 'robots.txt', 'mimetype': 'text/plain'}),
    # (r'^favicon\.ico$', 'django.views.generic.simple.redirect_to', {'url': '/static/img/favicon.ico'}),

    url(r'^register/', view.register, name='register'),
    url(r'^profile/$', view.ProfileView.as_view(template_name='registration/profile.html'), name='profile'),

    url(r'^$', view.IndexView.as_view(template_name=t('index.html')), name='index'),
    url(r'^home/$', view.HomeView.as_view(template_name=t('home.html')), name='home'),
    url(r'^setting/$', view.SettingView.as_view(template_name=t('setting.html')), name='setting'),

    url(r'^social/$', view.SocialView.as_view(template_name=t('social.html')), name='social'),
    url(r'^social/(?P<action>link)/$', view.SocialView.as_view(template_name=t('social.html')), name='social'),
    url(r'^social/(?P<action>update)/$', view.SocialView.as_view(template_name=t('social.html')), name='social'),

    url(r'^todolist/create/$', view.TodoListView.as_view(template_name=t('todolist-create.html')), name='todolist-create'),
    url(r'^todolist/$', view.TodoListView.as_view(template_name=t('todolist.html')), name='todolist'),
    url(r'^todolist/(?P<pk>[0-9]+)/$', view.TodoListView.as_view(template_name=t('todolist.html')), name='todolist'),

    url(r'^todo/create/$', view.TodoCreateView.as_view(template_name=t('todo-create.html')), name='todo-create'),
    url(r'^todo/(?P<pk>[0-9]+)/$', view.TodoView.as_view(template_name=t('todo.html')), name='todo'),

    url(r'^wishlist/$', view.WishListView.as_view(template_name=t('wishlist.html')), name='wishlist'),
    url(r'^wishlist/(?P<pk>[0-9]+)/$', view.WishListView.as_view(template_name=t('wishlist.html')), name='wishlist'),


    url(r'^json/usernames/$', view.ProfileUsernamesJsonView.as_view()),

    # url(r'^', include('user.urls')),

]

# debug & test
if settings.DEBUG:
    import debug_toolbar
    urlpatterns.extend([
        url(r'^test/$', view.test, name='test'),
        url(r'^test/(?P<pk>[0-9]+)/$', view.test, name='test'),
        url(r'^debug/', include(debug_toolbar.urls)),
    ])
