from aiogram.fsm.state import StatesGroup, State


class LessonsQuestion(StatesGroup):
    user_id = State()
    modul = State()
    lesson = State()
    answer = State()