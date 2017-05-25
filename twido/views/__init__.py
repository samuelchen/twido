#!/usr/bin/env python
# coding: utf-8


from .common import paginate, test
from .base import BaseViewMixin
from .index import IndexView
from .home import HomeView
from .profile import ProfileView, ProfileUsernamesJsonView
from .setting import SettingView
from .social import SocialView
from .list import ListView
from .task import TaskView
from .account import RegisterView, LoginView
