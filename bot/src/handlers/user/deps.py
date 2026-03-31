import calendar
from collections import defaultdict
from datetime import date, datetime

from aiogram.types import InlineKeyboardButton as Button
from aiogram.types import InlineKeyboardMarkup
from src.services.booking import Session
from src.utils.tools import month_alias_dec, month_alias, weekday_alias


class Keyboard:

    @staticmethod
    def menu(appointment_count: int, free_slots: dict[date, int]):
        months = []
        for d in sorted(free_slots):
            months.append(
                [
                    Button(
                        text=f"{month_alias(d.month)} ({free_slots[d]})",
                        callback_data=f"{d}~explore_month",
                    )
                ]
            )

        return InlineKeyboardMarkup(inline_keyboard=[
            [Button(text=f'Мои записи ({appointment_count})', callback_data='~my_appointment')],
            *months
        ])

    @staticmethod
    def appointments(appointments: list[Session]):
        rows = []
        for a in sorted(appointments, key=lambda x: (x.date, x.time)):
            rows.append(
                [
                    Button(
                        text=f"{a.date.day} {month_alias_dec(a.date.month)} {a.time.hour}:00",
                        callback_data=f"{a.id}~delete_my_appointment",
                    )
                ]
            )

        return InlineKeyboardMarkup(inline_keyboard=[
            *rows,
            [Button(text='Назад', callback_data='~user_menu')]
        ])

    @staticmethod
    def month(current_date: date, records: list[Session] = []):
        def highlight(day: int):
            return day if day != date.today().day else f"[{day}]"

        now = date.today()
        today_month = current_date.year == now.year and current_date.month == now.month

        by_day = defaultdict(int)
        for r in records:
            if r.time.hour != 0 and not r.user.id:
                by_day[r.date.day] += 1

        month_by_week = calendar.monthcalendar(current_date.year, current_date.month)
        rows = []
        for week in month_by_week:
            row = []
            for day in week:
                if day == 0:
                    row.append(Button(text=" ", callback_data="~empty"))
                    continue

                if today_month and day < now.day:
                    row.append(Button(text="x", callback_data="~empty"))
                    continue

                edit_date = current_date.replace(day=day)
                text = f"{highlight(day) if today_month else day}"
                row.append(
                    Button(
                        text=text,
                        style="success" if by_day[day] > 0 else None,
                        callback_data=f"{edit_date}~explore_day",
                    ),
                )
            rows.append(row)

        week_alias = []
        for number in range(0, 7):
            week_day = f"{weekday_alias(number)}"
            if today_month and number == now.weekday():
                week_day = f"[{weekday_alias(number)}]"

            week_alias.append(Button(text=week_day, callback_data="~empty"))

        return InlineKeyboardMarkup(
            inline_keyboard=[
                week_alias,
                *rows,
                [Button(text='Назад', callback_data='~user_menu')]
            ]
        )

    @staticmethod
    def day(current_date: date, records: list[Session]):
        is_today = date.today() == current_date

        free_slots = defaultdict(bool)
        ids = defaultdict(int)
        for r in records:
            if not r.user.id:
                free_slots[r.time.hour] = True
            ids[r.time.hour] = r.id

        rows = []
        row = []
        for s in sorted(records, key=lambda x: x.time):
            hour = s.time.hour
            if is_today and hour <= datetime.now().hour:
                continue

            row.append(
                Button(
                    text=f"{hour}:00",
                    style='success' if free_slots[hour] else None,
                    callback_data=f"{ids[hour]}~make_appointment" if free_slots[hour] else '~empty',
                ),
            )

            if len(row) == 4:
                rows.append(row)
                row = []
        else:
            if row:
                rows.append(row)
        return InlineKeyboardMarkup(inline_keyboard=[
            *rows,
            [Button(text="Назад", callback_data=f'{current_date}~explore_month')]
        ])
