import calendar
import logging
from collections import defaultdict
from datetime import date, time

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from src.config import config
from src.services.booking import Booking, Session, SessionAdd
from src.utils.tools import MONTHS, WEEKDAYS

from .desp import Keyboard as K
from .desp import Message as M

logger = logging.getLogger(__name__)


async def cmd_start(message: Message):
    await message.answer(M.menu(), reply_markup=K.menu())


async def cb_menu(cb: CallbackQuery):
    await cb.answer()

    await cb.message.edit_text(M.menu(), reply_markup=K.menu())


async def cb_edit_or_add_months(cb: CallbackQuery):
    await cb.answer()

    exists = await Booking.get_active_month()

    await cb.message.edit_text(
        "Для добавления месяца кликните на кнопку 'Добавить новый месяц'\n"
        "Для внесения правок в расписание кликните на название месяца",
        reply_markup=K.edit_or_add_months(exists)
    )


async def cb_add_new_month(cb: CallbackQuery):
    open_monhts = await Booking.get_active_month()
    if len(open_monhts) >= 6:
        await cb.answer(
            "Возможно добавление только на 6 месяцев вперед!",
            show_alert=True,
        )
        return

    await cb.answer()

    date = await Booking.open_new_month()

    rows = await Booking.get_month_by_date(date)

    await cb.message.edit_text(
        'Вы добавили новый месяц, проваливайтесь в конкретные дни для правки рабочих часов',
        reply_markup=K.edit_month(date, rows),
    )


async def cb_edit_month(cb: CallbackQuery):
    await cb.answer()

    date_str, *_ = cb.data.split('~')
    parsed_date = date.fromisoformat(date_str)

    rows = await Booking.get_month_by_date(parsed_date)

    await cb.message.edit_text(
        'Проваливайтесь в даты и правьте рабочие часы\n'
        "Неактивные дни помечены синим цветом",
        reply_markup=K.edit_month(parsed_date, rows),
    )


async def cb_edit_day(cb: CallbackQuery):
    await cb.answer()

    date_str, *_ = cb.data.split('~')
    d = date.fromisoformat(date_str)

    rows = await Booking.get_by_day(d)
    await cb.message.edit_text(
        f"Количество активных часов: {len(rows)}\n\n"
        f"<i>Примечание:\n"
        " * При удалении записи с пометкой 👩🏼 пользователю придет уведомление "
        "о том, что сеанс отменен;"
        " * Зеленый цвет показывает, что сеанс активирован</i>",
        reply_markup=K.edit_day(d, rows),
        parse_mode='HTML'
    )


async def cb_edit_times(cb: CallbackQuery):
    await cb.answer()

    date_str, hour, row_id, *_ = cb.data.split('~')
    d = date.fromisoformat(date_str)

    row_id = int(row_id) if row_id and row_id != '0' else None
    if row_id:
        session = await Booking.get(row_id)
        if session and session.user.id:
            await cb.bot.send_message(
                session.user.id,
                "❗️ Внимание!\n"
                f"Сеанс {session.date:%d.%m.%Y} {session.time:%H:%M} был отменен модератором",
            )
        is_ok = await Booking.delete(row_id)
    else:
        await Booking.add(SessionAdd(
            date=d,
            time=time(int(hour)),
        ))

    rows = await Booking.get_by_day(d)
    await cb.message.edit_text(
        f"Количество активных часов: {len(rows)}\n\n"
        f"<i>Примечание:\n"
        " * При удалении записи с пометкой 👩🏼 пользователю придет уведомление "
        "о том, что сеанс отменен;"
        " * Зеленый цвет показывает, что сеанс активирован</i>",
        reply_markup=K.edit_day(d, rows),
        parse_mode='HTML'
    )


async def cb_month_by_weeks(cb: CallbackQuery):
    await cb.answer()

    exists_month = await Booking.get_active_month()
    if not exists_month:
        await cb.answer("Расписания отсутствует", show_alert=True)
        return

    await cb.answer()

    month_page, inner_page, *_ = cb.data.split('~')
    month_page = int(month_page) if month_page else 0
    inner_page = int(inner_page) if inner_page else 0

    now = date.today()
    picked_date = exists_month[month_page]
    month_by_week = calendar.monthcalendar(picked_date.year, picked_date.month)
    if picked_date.year == now.year and picked_date.month == now.month:
        new_month_by_week = []
        for row in month_by_week:
            have_row = []
            for d in row:
                if d < now.day:
                    continue
                have_row.append(d)
            if have_row:
                new_month_by_week.append(have_row)
        month_by_week = new_month_by_week

    rows = await Booking.get_month_by_date(picked_date)

    week_days = month_by_week[inner_page]
    text = f"Расписание на <b>{MONTHS[picked_date.month-1]}</b> с {min(w for w in week_days if w)} по {max(week_days)}"
    current_week = defaultdict(list[Session])
    for r in rows:
        if r.date.day in week_days:
            if r.time.hour != 0:
                current_week[r.date.weekday()].append(r)

    if current_week:
        for r in sorted(current_week):
            day_hours = current_week[r]
            text += f"\n<b>{WEEKDAYS[r]}</b>"
            for s in sorted(day_hours, key=lambda x: x.time):
                if s.user.id:
                    user_link = f'<a href="tg://user?id={s.user.id}">{s.user.fullname}</a>'
                else:
                    user_link = 'Пусто'
                text += f"\n - {s.time.hour}:00 - {user_link}"
    else:
        text += "\n\nДаты приема отсутствуют"

    await cb.message.edit_text(
        text,
        reply_markup=K.slider(month_page, len(exists_month), inner_page, len(month_by_week)),
        parse_mode='HTML',
    )


async def cb_reset_all(cb: CallbackQuery):
    await cb.answer()

    flag, *_ = cb.data.split('~')
    if not flag:
        await cb.message.edit_text(
            "⚠️ Данное действие необратимо. Уверена?",
            reply_markup=K.reset_db(),
        )
        return

    is_ok = False
    for i in (1, 2, 3):
        try:
            await Booking.hide()
        except Exception as e:
            logger.exception(f"Hide db table failed. Attempt {i}")
        else:
            is_ok = True
            logger.info('Hide table success')
            break
    else:
        for i in (1, 2, 3):
            try:
                await Booking.clear_all()
            except Exception as e:
                logging.exception(f"Clear database failed. Attempt {i}")
            else:
                is_ok = True
                logger.info("Clear database, because can't hide table")
                break

    if is_ok:
        text = 'Game over'
    else:
        text = 'База все еще активна, обратитесь к администратору'
    await cb.message.edit_text(text)


async def cb_empty(cb: CallbackQuery):
    await cb.answer()


async def cmd_restart(message: Message):
    _, master_str = message.text.split(maxsplit=1)

    if master_str == config.master_key:
        unhide_ok = False
        for i in (1, 2, 3):
            try:
                await Booking.unhide()
            except Exception as e:
                logger.exception(f"Unhide db table failed. Attempt {i}")
            else:
                unhide_ok = True
                logger.info('Unhide table success')
                break

        if unhide_ok:
            text = 'Жми /start'
        else:
            text = 'Ошибка разблокировки таблицы, обратитесь к администратору'

        await message.answer(text)


def router():
    router = Router()
    router.message.register(cmd_start, Command('start'), F.from_user.id.in_(config.admin_ids))
    router.message.register(cmd_restart, Command('restart'), F.from_user.id.in_(config.admin_ids))
    for handler, filter in (
        (cb_menu, F.data.endswith("~menu")),

        (cb_edit_or_add_months, F.data.endswith("~edit_schedule")),

        (cb_add_new_month, F.data.endswith("~add_new_month")),
        (cb_edit_month, F.data.endswith("~edit_month")),

        (cb_edit_day, F.data.endswith("~edit_day")),
        (cb_edit_times, F.data.endswith("~edit_time")),

        (cb_month_by_weeks, F.data.endswith("~my_schedule")),

        (cb_reset_all, F.data.endswith("~reset_all")),
        (cb_empty, F.data.endswith("~empty")),
    ):
        router.callback_query.register(handler, filter, F.from_user.id.in_(config.admin_ids))
    return router
