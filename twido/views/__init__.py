#!/usr/bin/env python
# coding: utf-8


from .common import paginate, register, test
from .base import BaseViewMixin
from .index import IndexView
from .home import HomeView
from .profile import ProfileView, ProfileUsernamesJsonView
from .setting import SettingView
from .social import SocialView
from .todo import TodoListView, TodoView
from .wish import WishListView
