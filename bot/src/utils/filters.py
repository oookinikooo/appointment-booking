from aiogram import Bot
from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message
from src.config import config


class ModeratorFilter(BaseFilter):
    async def __call__(self, obj: Message | CallbackQuery, bot: Bot) -> bool:
        return True if obj.from_user.id in config.admin_ids else False
