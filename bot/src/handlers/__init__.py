from aiogram import Dispatcher

from . import moderator, user


def attach_handlers(dp: Dispatcher):
    dp.include_routers(moderator.router(), user.router())
