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
# from django.contrib import admin
from django.conf import settings
from . import view


# to render full template path
def t(template):
    return 'twido/' + template


urlpatterns = [
    url(r'^admin/', include('django.contrib.auth.urls')),
    url(r'^', include('django.contrib.auth.urls')),
    url(r'^register/', view.register, name='register'),
    url(r'^profile/', view.ProfileView.as_view(template_name='registration/profile.html'), name='profile'),

    url(r'^$', view.IndexView.as_view(template_name=t('index.html')), name='index'),
    url(r'^home/$', view.HomeView.as_view(template_name=t('home.html')), name='home'),

    url(r'^todolist/create/$', view.TodoListView.as_view(template_name=t('todolist-create.html')), name='todolist-create'),
    url(r'^todolist/(?P<pk>[0-9]+)/$', view.TodoListView.as_view(template_name=t('todolist.html')), name='todolist'),

    url(r'^todo/create/$', view.TodoCreateView.as_view(template_name=t('todo-create.html')), name='todo-create'),
    url(r'^todo/(?P<pk>[0-9]+)/$', view.TodoUpdateView.as_view(template_name=t('todo.html')), name='todo'),

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
