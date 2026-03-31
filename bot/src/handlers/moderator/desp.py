import calendar
from collections import defaultdict
from datetime import date, datetime

from aiogram.types import InlineKeyboardButton as Button
from aiogram.types import InlineKeyboardMarkup
from src.services.booking import Session
from src.utils.tools import month_alias, weekday_alias


class Message:
    @staticmethod
    def menu():
        return (
            "Расписание - записи по неделям и месяцам\n"
            "Править / Добавить расписание - добавление нового месяца и изменение "
            "рабочих дней и часов по каждому из месяцев\n"
        )


class Keyboard:
    @staticmethod
    def menu():
        return InlineKeyboardMarkup(inline_keyboard=[
            [Button(text='Расписание', callback_data='0~0~my_schedule')],
            [Button(text='Править / Добавить расписание', callback_data='~edit_schedule')],
            [Button(text='Удалить все', style='danger', callback_data='~reset_all')],
        ])

    @staticmethod
    def edit_or_add_months(dates: list[date]):
        rows = []
        row = []
        for d in dates:
            row.append(Button(text=month_alias(d.month), callback_data=f'{d}~edit_month'))
            if len(row) >= 2:
                rows.append(row)
                row = []
        else:
            if row:
                rows.append(row)

        return InlineKeyboardMarkup(inline_keyboard=[
            *rows,
            [Button(text='➕ Добавить новый месяц', callback_data='~add_new_month')],
            [Button(text='Назад', callback_data='~menu')]
        ])

    @staticmethod
    def edit_month(current_date: date, records: list[Session] = []):
        def highlight(day: int):
            return day if day != date.today().day else f"[{day}]"

        now = date.today()
        today_month = current_date.year == now.year and current_date.month == now.month

        by_day = defaultdict(int)
        for r in records:
            if r.time.hour != 0:
                by_day[r.date.day] += 1

        rows = []
        for week in calendar.monthcalendar(current_date.year, current_date.month):
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
                if by_day[day] > 0:
                    # text += f" ({by_day[day]})"
                    style = 'success'
                else:
                    style = 'primary'

                row.append(Button(text=text, style=style, callback_data=f"{edit_date}~edit_day"))
            rows.append(row)

        week_alias = []
        for i in range(0, 7):
            week_day = weekday_alias(i)
            if today_month and i == now.weekday():
                week_day = f"[{week_day}]"

            week_alias.append(Button(text=week_day, callback_data="~empty"))

        return InlineKeyboardMarkup(
            inline_keyboard=[
                week_alias,
                *rows,
                [Button(text='Назад', callback_data='~edit_schedule')]
            ]
        )

    @staticmethod
    def edit_day(current_date: date, records: list[Session]):
        is_today = date.today() == current_date
        active_time = defaultdict(bool)
        for r in records:
            active_time[r.time.hour] = True

        has_recoreds = defaultdict(bool)
        for r in records:
            if r.user.id:
                has_recoreds[r.time.hour] = True

        ids = defaultdict(int)
        for r in records:
            ids[r.time.hour] = r.id

        rows = []
        row = []
        for hour in list(range(9, 22)):
            if is_today and hour <= datetime.now().hour:
                continue

            text, style = f"{hour}:00", None

            if active_time[hour]:
                style = 'success'

            if has_recoreds[hour]:
                text += " 👩🏼"

            row.append(
                Button(
                    text=text,
                    style=style,
                    callback_data=f"{current_date}~{hour}~{ids[hour]}~edit_time",
                )
            )

            if len(row) == 4:
                rows.append(row)
                row = []
        else:
            if row:
                rows.append(row)
        return InlineKeyboardMarkup(inline_keyboard=[
            *rows,
            [Button(text="Назад", callback_data=f'{current_date}~edit_month')]
        ])

    @staticmethod
    def slider(
        month_page: int,
        total_month_page: int,
        inner_page: int,
        total_inner_page: int,
    ):
        slider = []
        if inner_page > 0:
            slider.append(
                Button(
                    text="«", callback_data=f"{month_page}~{inner_page-1}~my_schedule"
                )
            )
        if inner_page + 1 < total_inner_page:
            slider.append(
                Button(
                    text="»", callback_data=f"{month_page}~{inner_page+1}~my_schedule"
                )
            )

        month_slider = []
        if month_page > 0:
            month_slider.append(
                Button(text="«", callback_data=f"{month_page - 1}~0~my_schedule")
            )
        month_slider.append(Button(text="Назад", callback_data="~menu"))
        if month_page + 1 < total_month_page:
            month_slider.append(
                Button(text="»", callback_data=f"{month_page + 1}~0~my_schedule")
            )

        return InlineKeyboardMarkup(inline_keyboard=[slider, month_slider])

    @staticmethod
    def reset_db():
        return InlineKeyboardMarkup(inline_keyboard=[
            [Button(text='Да, очистить', style='danger', callback_data='1~reset_all')],
            [Button(text='Назад', callback_data='~menu')],
        ])
