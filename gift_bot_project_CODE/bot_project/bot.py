"""
Gift Advisor Bot - main entry point.
Telegram bot that uses Grok LLM for personalized gift recommendations.
"""

import asyncio
import json
import logging
import os
import time
from typing import Optional

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    CallbackQuery,
)
from dotenv import load_dotenv

from database import init_db, save_user, save_session, save_feedback, get_user_sessions
from grok_client import call_grok
from prompts.builder import build_prompt, STRATEGIES

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DEFAULT_STRATEGY = os.getenv("DEFAULT_STRATEGY", "cot")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ---------------------------------------------------------------------------
# Finite-State Machine for the questionnaire
# ---------------------------------------------------------------------------

class GiftForm(StatesGroup):
    relation = State()
    gender = State()
    age_group = State()
    occasion = State()
    budget = State()
    interests = State()
    free_text = State()
    rating_relevance = State()
    rating_creativity = State()
    rating_specificity = State()
    comment = State()


# ---------------------------------------------------------------------------
# Helpers for inline keyboards
# ---------------------------------------------------------------------------

def kb(options: list[tuple[str, str]], row_width: int = 2) -> InlineKeyboardMarkup:
    """Build an inline keyboard from (label, callback_data) tuples."""
    buttons = [InlineKeyboardButton(text=text, callback_data=data) for text, data in options]
    rows = [buttons[i:i + row_width] for i in range(0, len(buttons), row_width)]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_multi(options: list[tuple[str, str]], selected: list[str], row_width: int = 2) -> InlineKeyboardMarkup:
    """Build a multi-select keyboard with a Done button."""
    buttons = []
    for text, data in options:
        mark = "✅ " if data in selected else ""
        buttons.append(InlineKeyboardButton(text=mark + text, callback_data=f"i:{data}"))
    rows = [buttons[i:i + row_width] for i in range(0, len(buttons), row_width)]
    rows.append([InlineKeyboardButton(text="✔ Done", callback_data="i:done")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ---------------------------------------------------------------------------
# /start
# ---------------------------------------------------------------------------

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    save_user(message.from_user.id, message.from_user.username or "")
    await message.answer(
        "🎁 <b>Welcome to Gift Advisor Bot!</b>\n\n"
        "I help you choose a personalized gift in less than a minute.\n"
        "I will ask 6 short questions, then suggest 3 gift ideas.\n\n"
        "Privacy: I do not store names of real people. "
        "Only the structured profile is saved for research.\n\n"
        "Tap the button below to start.",
        parse_mode="HTML",
        reply_markup=kb([("🚀 Start", "go:new")]),
    )


@dp.callback_query(F.data == "go:new")
async def cb_new(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    await start_questionnaire(call.message, state)


@dp.message(Command("new"))
async def cmd_new(message: Message, state: FSMContext) -> None:
    await start_questionnaire(message, state)


async def start_questionnaire(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.update_data(interests=[])
    await state.set_state(GiftForm.relation)
    await message.answer(
        "<b>Question 1 of 6</b>\nFor whom is the gift?",
        parse_mode="HTML",
        reply_markup=kb([
            ("Friend", "r:friend"),
            ("Family", "r:family"),
            ("Partner", "r:partner"),
            ("Colleague", "r:colleague"),
        ]),
    )


# ---------------------------------------------------------------------------
# Questionnaire steps
# ---------------------------------------------------------------------------

@dp.callback_query(F.data.startswith("r:"), GiftForm.relation)
async def step_relation(call: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(relation=call.data.split(":", 1)[1])
    await state.set_state(GiftForm.gender)
    await call.answer()
    await call.message.answer(
        "<b>Question 2 of 6</b>\nGender of the receiver?",
        parse_mode="HTML",
        reply_markup=kb([
            ("Male", "g:male"),
            ("Female", "g:female"),
            ("Prefer not to say", "g:any"),
        ]),
    )


@dp.callback_query(F.data.startswith("g:"), GiftForm.gender)
async def step_gender(call: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(gender=call.data.split(":", 1)[1])
    await state.set_state(GiftForm.age_group)
    await call.answer()
    await call.message.answer(
        "<b>Question 3 of 6</b>\nAge group?",
        parse_mode="HTML",
        reply_markup=kb([
            ("18-25", "a:18-25"),
            ("26-35", "a:26-35"),
            ("36-50", "a:36-50"),
            ("50+", "a:50+"),
        ]),
    )


@dp.callback_query(F.data.startswith("a:"), GiftForm.age_group)
async def step_age(call: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(age_group=call.data.split(":", 1)[1])
    await state.set_state(GiftForm.occasion)
    await call.answer()
    await call.message.answer(
        "<b>Question 4 of 6</b>\nOccasion?",
        parse_mode="HTML",
        reply_markup=kb([
            ("Birthday", "o:birthday"),
            ("Anniversary", "o:anniversary"),
            ("Holiday", "o:holiday"),
            ("No reason", "o:none"),
        ]),
    )


@dp.callback_query(F.data.startswith("o:"), GiftForm.occasion)
async def step_occasion(call: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(occasion=call.data.split(":", 1)[1])
    await state.set_state(GiftForm.budget)
    await call.answer()
    await call.message.answer(
        "<b>Question 5 of 6</b>\nBudget?",
        parse_mode="HTML",
        reply_markup=kb([
            ("$ (low)", "b:low"),
            ("$$ (medium)", "b:medium"),
            ("$$$ (high)", "b:high"),
        ]),
    )


INTEREST_OPTIONS = [
    ("Books", "books"),
    ("Sports", "sports"),
    ("Tech", "tech"),
    ("Cooking", "cooking"),
    ("Travel", "travel"),
    ("Music", "music"),
    ("Art", "art"),
    ("Games", "games"),
    ("Coffee", "coffee"),
    ("Fashion", "fashion"),
]


@dp.callback_query(F.data.startswith("b:"), GiftForm.budget)
async def step_budget(call: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(budget=call.data.split(":", 1)[1])
    await state.set_state(GiftForm.interests)
    await call.answer()
    await call.message.answer(
        "<b>Question 6 of 6</b>\nInterests (tap several, then Done):",
        parse_mode="HTML",
        reply_markup=kb_multi(INTEREST_OPTIONS, []),
    )


@dp.callback_query(F.data.startswith("i:"), GiftForm.interests)
async def step_interests(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    selected = data.get("interests", [])
    value = call.data.split(":", 1)[1]

    if value == "done":
        if not selected:
            await call.answer("Please select at least one interest.", show_alert=True)
            return
        await state.set_state(GiftForm.free_text)
        await call.answer()
        await call.message.answer(
            "Want to add anything in your own words? (or send /skip)",
        )
        return

    if value in selected:
        selected.remove(value)
    else:
        selected.append(value)
    await state.update_data(interests=selected)
    await call.answer()
    await call.message.edit_reply_markup(reply_markup=kb_multi(INTEREST_OPTIONS, selected))


@dp.message(Command("skip"), GiftForm.free_text)
async def free_text_skip(message: Message, state: FSMContext) -> None:
    await state.update_data(free_text="")
    await generate_recommendation(message, state)


@dp.message(GiftForm.free_text)
async def free_text(message: Message, state: FSMContext) -> None:
    await state.update_data(free_text=message.text or "")
    await generate_recommendation(message, state)


# ---------------------------------------------------------------------------
# Generate recommendation
# ---------------------------------------------------------------------------

async def generate_recommendation(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    profile = {
        "relation": data["relation"],
        "gender": data["gender"],
        "age_group": data["age_group"],
        "occasion": data["occasion"],
        "budget": data["budget"],
        "interests": data["interests"],
        "free_text": data.get("free_text", ""),
    }

    strategy = data.get("strategy") or DEFAULT_STRATEGY
    prompt = build_prompt(strategy, profile)

    await message.answer("🤖 Thinking... please wait a few seconds.")

    t0 = time.time()
    try:
        answer = await call_grok(prompt)
    except Exception as exc:
        logger.exception("Grok call failed")
        await message.answer(f"❌ Sorry, an error happened: {exc}")
        await state.clear()
        return
    elapsed = time.time() - t0

    response_data = {"strategy": strategy, "answer": answer, "elapsed": elapsed}
    session_id = save_session(
        telegram_id=message.from_user.id,
        profile=profile,
        strategy=strategy,
        response=response_data,
    )

    await message.answer(
        f"🎁 <b>3 gift ideas (strategy: {strategy}):</b>\n\n{answer}\n\n"
        f"⏱ Response time: {elapsed:.1f} s",
        parse_mode="HTML",
    )

    await state.update_data(session_id=session_id)
    await ask_rating(message, state, "relevance", GiftForm.rating_relevance)


# ---------------------------------------------------------------------------
# Feedback (3 ratings + comment)
# ---------------------------------------------------------------------------

RATING_KB = kb([(str(i), f"rate:{i}") for i in range(1, 6)], row_width=5)


async def ask_rating(message: Message, state: FSMContext, name: str, next_state) -> None:
    await state.set_state(next_state)
    await message.answer(f"Please rate <b>{name}</b> (1 = bad, 5 = great):",
                         parse_mode="HTML", reply_markup=RATING_KB)


@dp.callback_query(F.data.startswith("rate:"), GiftForm.rating_relevance)
async def rate_relevance(call: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(rating_relevance=int(call.data.split(":")[1]))
    await call.answer()
    await ask_rating(call.message, state, "creativity", GiftForm.rating_creativity)


@dp.callback_query(F.data.startswith("rate:"), GiftForm.rating_creativity)
async def rate_creativity(call: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(rating_creativity=int(call.data.split(":")[1]))
    await call.answer()
    await ask_rating(call.message, state, "specificity", GiftForm.rating_specificity)


@dp.callback_query(F.data.startswith("rate:"), GiftForm.rating_specificity)
async def rate_specificity(call: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(rating_specificity=int(call.data.split(":")[1]))
    await state.set_state(GiftForm.comment)
    await call.answer()
    await call.message.answer("Any short comment? (or send /skip)")


@dp.message(Command("skip"), GiftForm.comment)
async def comment_skip(message: Message, state: FSMContext) -> None:
    await save_feedback_and_finish(message, state, comment="")


@dp.message(GiftForm.comment)
async def comment(message: Message, state: FSMContext) -> None:
    await save_feedback_and_finish(message, state, comment=message.text or "")


async def save_feedback_and_finish(message: Message, state: FSMContext, comment: str) -> None:
    data = await state.get_data()
    save_feedback(
        session_id=data["session_id"],
        rating_relevance=data.get("rating_relevance"),
        rating_creativity=data.get("rating_creativity"),
        rating_specificity=data.get("rating_specificity"),
        comment=comment,
    )
    await state.clear()
    await message.answer(
        "✅ Thank you! Your feedback is saved.\n\n"
        "Send /new to get another gift idea, or /my to see your previous sessions.",
    )


# ---------------------------------------------------------------------------
# Other commands
# ---------------------------------------------------------------------------

@dp.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "<b>Commands:</b>\n"
        "/start — welcome and start\n"
        "/new — get a new gift idea\n"
        "/my — show your previous sessions\n"
        "/cancel — cancel current questionnaire\n"
        "/help — this message\n\n"
        "<i>Example: tap /new, answer 6 questions, get 3 ideas.</i>",
        parse_mode="HTML",
    )


@dp.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Cancelled. Send /new to start again.")


@dp.message(Command("my"))
async def cmd_my(message: Message) -> None:
    rows = get_user_sessions(message.from_user.id, limit=5)
    if not rows:
        await message.answer("You have no sessions yet. Send /new to start.")
        return
    text = "<b>Your last sessions:</b>\n\n"
    for s in rows:
        profile = json.loads(s["profile_data_json"])
        text += (
            f"• {s['timestamp']} — {profile['relation']}, "
            f"{profile['occasion']}, budget {profile['budget']} "
            f"(strategy: {s['strategy_used']})\n"
        )
    await message.answer(text, parse_mode="HTML")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing. Set it in .env file.")
    init_db()
    logger.info("Bot is starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
