from aiogram import Dispatcher

from .moderator import base as moderator
from .user import base as user


def attach(dp: Dispatcher):
    dp.include_routers(moderator.router(), user.router())
