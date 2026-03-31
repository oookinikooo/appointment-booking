import calendar

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from src.services.booking import Booking, User
from datetime import date

from .deps import Keyboard as K


async def cmd_start(message: Message):
    user_id = message.from_user.id
    appointments = await Booking.user_appointments(user_id)

    free_slots: dict[date, int] = await Booking.get_month_slots_count()
    await message.answer(
        "Привет! Здесь можно записаться на массаж к Ксюше",
        reply_markup=K.menu(len(appointments), free_slots),
    )


async def cb_menu(cb: CallbackQuery):
    await cb.answer()

    user_id = cb.from_user.id
    appointments = await Booking.user_appointments(user_id)

    free_slots: dict[date, int] = await Booking.get_month_slots_count()
    await cb.message.edit_text(
        "Записывайтесь на массаж",
        reply_markup=K.menu(len(appointments), free_slots),
    )


async def cb_my_appointments(cb: CallbackQuery):
    user_id = cb.from_user.id
    appointments = await Booking.user_appointments(user_id)
    if not appointments:
        await cb.answer("У Вас нет записей", show_alert=True)
        return

    await cb.answer()

    await cb.message.edit_text(
        'Для удаления записи на посещение нажмите на нее',
        reply_markup=K.appointments(appointments),
    )


async def cb_empty(cb: CallbackQuery):
    await cb.answer()


async def cb_explore_month(cb: CallbackQuery):
    await cb.answer()

    date_str, *_ = cb.data.split('~')
    d = date.fromisoformat(date_str)

    rows = await Booking.get_month_by_date(d)
    await cb.message.edit_text(
        'Зеленым помечены дни где есть свободные места',
        reply_markup=K.month(d, rows),
    )


async def cb_explore_day(cb: CallbackQuery):
    await cb.answer()

    date_str, *_ = cb.data.split('~')
    d = date.fromisoformat(date_str)

    rows = await Booking.get_by_day(d)
    await cb.message.edit_text(
        'Записаться можно в часы помечанные зеленым цветом',
        reply_markup=K.day(d, rows),
    )


async def cb_make_appointment(cb: CallbackQuery):
    row_id, *_ = cb.data.split('~')

    is_ok = False
    session = await Booking.get(int(row_id))
    if session and not session.user.id:
        is_ok = await Booking.make_appointment(session.id, User(
            id=cb.from_user.id,
            fullname=cb.from_user.full_name,
        ))

    text = 'Уже заняли' if not is_ok else "Вы записались"

    await cb.answer(text, show_alert=True)

    rows = await Booking.get_by_day(session.date)
    await cb.message.edit_text(
        'Записаться можно в часы помечанные зеленым цветом',
        reply_markup=K.day(session.date, rows),
    )


async def cb_delete_my_appointment(cb: CallbackQuery):
    user_id = cb.from_user.id

    session_id, *_ = cb.data.split('~')
    is_ok = await Booking.reset_appointment(int(session_id))

    await cb.answer("Запись отменена!")

    appointments = await Booking.user_appointments(user_id)
    if not appointments:
        text = 'Записей на посещение больше нет'
    else:
        text = 'Для удаления записи на посещение нажмите на нее'
    await cb.message.edit_text(
        text,
        reply_markup=K.appointments(appointments),
    )


def router():
    router = Router()
    router.message.register(cmd_start, Command('start'))
    for cb_func, cb_filter in (
        (cb_menu, F.data.endswith('~user_menu')),
        (cb_empty, F.data.endswith('~empty')),
        (cb_my_appointments, F.data.endswith('~my_appointment')),
        (cb_explore_month, F.data.endswith('~explore_month')),
        (cb_explore_day, F.data.endswith('~explore_day')),
        (cb_make_appointment, F.data.endswith('~make_appointment')),
        (cb_delete_my_appointment, F.data.endswith('~delete_my_appointment')),
    ):
        router.callback_query.register(cb_func, cb_filter)
    return router
