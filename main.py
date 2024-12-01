import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, html, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, CallbackQuery, \
    ChatMemberUpdated
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import bot_token, group_id_1, group_id_2
from form import LessonsQuestion
from models import create_table, Answer, Question

TOKEN = bot_token
dp = Dispatcher()


@dp.message(F.chat.id == group_id_1 or F.chat.id == group_id_2)
async def kjhbgv(message: Message, bot: Bot):
    q = await Question.filter(Question.question == message.reply_to_message.text.split('\n\n')[-1])
    q = [i for i in q][0]
    await Question.delete(q[0])
    chat_id = message.chat.id
    await bot.send_message(chat_id=q[-1], text=message.text)
    ikb = InlineKeyboardBuilder().add(
        InlineKeyboardButton(text=f"Profilga o'tish", url=f"tg://user?id={q[-1]}"))
    await bot.edit_message_text(text=f'<tg-spoiler>{message.reply_to_message.text}</tg-spoiler>',
                                chat_id=chat_id,
                                message_id=message.reply_to_message.message_id, reply_markup=ikb.as_markup())


# with engine.connect() as conn:
#     query = Select(Book.name, Book.price, Book.id, Basket.count).join(Book).filter(Book.id == Basket.book_id)
#     res = conn.execute(query)
#     conn.commit()
@dp.my_chat_member()
async def on_chat_member_update(event: ChatMemberUpdated, bot: Bot):
    if event.new_chat_member.status == "member":
        chat = event.chat
        await bot.send_message(
            chat_id=chat.id,
            text=f"{chat.id}"
        )


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    kb = [
        [KeyboardButton(text="Dars bo'yicha savol")]
    ]
    rkb = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer(f"Salom, {html.bold(message.from_user.full_name)}!, Buttonlardan birini tanlang",
                         reply_markup=rkb)


@dp.message(F.text == "Ko'p so'raladigan savollar")
async def frequently_asked_question(message: Message, state: FSMContext):
    data = await state.get_data()
    questions = await Answer.filter(Answer.modul == data['modul'], Answer.lesson == data['lesson'])
    ikb = InlineKeyboardBuilder()
    for i in questions:
        ikb.row(InlineKeyboardButton(text=i[3], callback_data=f"{i[1]}*{i[2]}*{i[4]}* question"))
    await message.answer('Savolin tanlang', reply_markup=ikb.as_markup())


# @dp.callback_query(F.data.endswith(' answer'))
# async def inline_echo(callback: CallbackQuery, bot: Bot):
#     a = InlineQueryResultArticle()
#     i = InputTextMessageContent(message_text='kjhg')
#     await bot.send_message(chat_id=callback.data.split('*')[0], text=i.message_text)


@dp.callback_query(F.data.endswith('tushunarli'))
async def inline_echo(callback: CallbackQuery, bot: Bot):
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)


@dp.callback_query(F.data.endswith(' question'))
async def answer_to_question(callback: CallbackQuery, bot: Bot):
    data = callback.data.split('*')
    answer = await Answer.filter(Answer.modul == data[0], Answer.lesson == data[1],
                                 Answer.question_number == data[2])
    ans = [i for i in answer][0]
    ikb = InlineKeyboardBuilder().add(InlineKeyboardButton(text='Tushunarli✔️', callback_data='tushunarli'))
    await callback.message.answer(text=f"{ans[3]}\n\n{ans[-1]}", reply_markup=ikb.as_markup())


@dp.message(F.text == "O'zimni savolimni berish")
async def another_question(message: Message, state: FSMContext):
    await message.answer('Savolingizni yozishingiz mumkun')
    await state.set_state(LessonsQuestion.answer)


@dp.message(F.text == "Dars bo'yicha savol")
async def button_lesson_question(message: Message, state: FSMContext):
    res = await Answer.select()
    l = set()
    for i in res:
        l.add(i[1])
    l = sorted(list(l))

    kb = []
    for i in range(1, len(l) + 1):
        kb.append([KeyboardButton(text=f"{i}-Modul")])
    rkb = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer('Modul tanlang', reply_markup=rkb)
    await state.update_data(user_id=message.chat.id)
    await state.set_state(LessonsQuestion.modul)


@dp.message(LessonsQuestion.answer)
async def send_question_group(message: Message, state: FSMContext, bot: Bot):
    if message.from_user.id % 2 == 0:
        group_id = group_id_1
    else:
        group_id = group_id_2
    await state.update_data(answer=message.text)
    await Question.create(question=message.text, user_id=message.from_user.id)
    ikb = InlineKeyboardBuilder().add(
        InlineKeyboardButton(text=f"Profilga o'tish", url=f"tg://user?id={message.from_user.id}"))
    await bot.send_message(chat_id=group_id, text=f"{message.from_user.full_name}\n\n{message.text}",
                           reply_markup=ikb.as_markup())


@dp.message(LessonsQuestion.modul)
async def form_modul(message: Message, state: FSMContext):
    modul = message.text[0]
    await state.update_data(modul=modul)
    res = await Answer.filter(Answer.modul == modul)
    _set = set()
    for i in res:
        _set.add(i[2])
    _set = sorted(list(_set))
    kb = [[KeyboardButton(text=f"{i}-Dars")] for i in range(1, len(_set) + 1)]
    rkb = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer('Darsni tanlang', reply_markup=rkb)
    await state.set_state(LessonsQuestion.lesson)


@dp.message(LessonsQuestion.lesson)
async def form_lesson(message: Message, state: FSMContext):
    await state.update_data(lesson=message.text[0])

    kb = [
        [KeyboardButton(text="Ko'p so'raladigan savollar"), KeyboardButton(text="O'zimni savolimni berish")]
    ]
    rkb = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer('Buttonlardan birini tanlang', reply_markup=rkb)


async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    create_table()
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
