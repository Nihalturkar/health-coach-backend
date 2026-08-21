"""
Telegram Bot Router — Health Coach bot for Telegram.

Users can:
  - Log meals: "ate 2 roti dal rice"
  - Log water: "water 500" or "pani 500"
  - Log weight: "weight 72.5"
  - Get summary: "summary" or "today"
  - Get streak: "streak"
  - Get help: "help" or "/start"

Uses Telegram Bot API webhook (set via /telegram/setup-webhook).
Groq LLM parses natural language meals into calories/macros.
"""
import re
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date
import httpx

from app.database import get_db
from app.models.user import User
from app.services import tracking_service
from app.services.progress_service import get_streaks
from app.ai.agent import call_groq_json
from app.config import settings

router = APIRouter(prefix="/telegram", tags=["Telegram Bot"])


async def _send_message(chat_id: int, text: str):
    """Send a message via Telegram Bot API."""
    if not settings.TELEGRAM_BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient() as client:
        await client.post(url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
        })


async def _find_user_by_telegram(db: AsyncSession, telegram_id: str) -> User | None:
    """Find user by telegram_id stored in phone field as 'tg:ID'."""
    result = await db.execute(
        select(User).where(User.phone == f"tg:{telegram_id}")
    )
    return result.scalar_one_or_none()


async def _parse_meal_with_ai(message: str) -> dict | None:
    """Use Groq LLM to parse natural language meal description."""
    try:
        result = call_groq_json(
            system_prompt="You parse food descriptions into nutritional data. Return only valid JSON.",
            user_prompt=f"""Parse this meal description into nutritional data:
"{message}"

Estimate calories and macros for Indian food portions.
Return valid JSON only:
{{
  "meal_name": "short name for the meal",
  "meal_type": "breakfast/lunch/dinner/snack",
  "calories": estimated_total_calories,
  "protein_g": estimated_protein,
  "carbs_g": estimated_carbs,
  "fats_g": estimated_fats
}}

Rules:
- Use common Indian food knowledge for calorie estimates
- 1 roti = ~80 cal, 1 cup rice = ~200 cal, 1 cup dal = ~150 cal
- 1 paratha = ~150 cal, 1 egg = ~70 cal, paneer 100g = ~265 cal
- If meal type is unclear, guess from current time or default to "lunch"
- Return only JSON, no explanation""",
        )
        return result
    except Exception:
        return None


HELP_TEXT = """🏋️ *AI Health Coach Bot*

Here's what I can do:

🍽️ *Log meal:* Just tell me what you ate
  _"ate 2 roti dal rice"_
  _"had oats with banana for breakfast"_
  _"paneer tikka 200g"_

💧 *Log water:* `water 500` (in ml)

⚖️ *Log weight:* `weight 72.5`

📊 *Today's summary:* `summary`

🔥 *Streak:* `streak`

🔗 *Link account:* `link your@email.com`

❓ *Help:* `help`"""


LINK_INSTRUCTIONS = """To connect your app account, send:
`link your@email.com`

Use the same email you registered with in the Health Coach app."""


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle incoming Telegram updates."""
    data = await request.json()

    # Extract message
    message = data.get("message")
    if not message or not message.get("text"):
        return {"ok": True}

    chat_id = message["chat"]["id"]
    telegram_id = str(message["from"]["id"])
    text = message["text"].strip()
    text_lower = text.lower()
    from_name = message["from"].get("first_name", "")

    # --- /start or help ---
    if text_lower in ("/start", "help", "hi", "hello"):
        await _send_message(chat_id, HELP_TEXT)
        return {"ok": True}

    # --- Link account ---
    if text_lower.startswith("link "):
        email = text[5:].strip().lower()
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        if not user:
            await _send_message(chat_id, f"❌ No account found with email `{email}`.\nMake sure you've registered in the app first.")
            return {"ok": True}

        user.phone = f"tg:{telegram_id}"
        await db.commit()
        await _send_message(chat_id, f"✅ Linked to *{user.name}*!\n\nYou can now log meals, water, weight directly here. Send `help` to see commands.")
        return {"ok": True}

    # --- Find user ---
    user = await _find_user_by_telegram(db, telegram_id)
    if not user:
        await _send_message(chat_id, f"Hey {from_name}! 👋\n\n" + LINK_INSTRUCTIONS)
        return {"ok": True}

    user_id = str(user.id)
    today = date.today()

    # --- Water ---
    if text_lower.startswith("water") or "pani" in text_lower or "paani" in text_lower:
        nums = re.findall(r'\d+', text)
        ml = int(nums[0]) if nums else 250
        await tracking_service.log_water(db, user_id, today, ml)
        await _send_message(chat_id, f"💧 Logged *{ml}ml* water!")
        return {"ok": True}

    # --- Weight ---
    if text_lower.startswith("weight") or text_lower.startswith("wajan"):
        nums = re.findall(r'[\d.]+', text)
        if nums:
            weight = float(nums[0])
            await tracking_service.log_weight(db, user_id, today, weight)
            await _send_message(chat_id, f"⚖️ Weight logged: *{weight} kg*")
        else:
            await _send_message(chat_id, "Send weight with a number, e.g. `weight 72.5`")
        return {"ok": True}

    # --- Summary ---
    if text_lower in ("summary", "today", "aaj", "status"):
        summary = await tracking_service.get_today_summary(db, user_id, today)
        streaks = await get_streaks(db, user_id, today)
        reply = (
            f"📊 *Today's Summary*\n\n"
            f"🔥 Calories: *{summary['total_calories']}* cal\n"
            f"💪 Protein: *{summary['total_protein']}g*\n"
            f"💧 Water: *{summary['total_water_ml']}ml*\n"
            f"🍽️ Meals: {len(summary['meal_logs'])}\n"
            f"🏋️ Workouts: {len(summary['workout_logs'])}\n\n"
            f"🔥 Streak: *{streaks['current_streak']}* days | Best: *{streaks['best_streak']}*"
        )
        await _send_message(chat_id, reply)
        return {"ok": True}

    # --- Streak ---
    if text_lower in ("streak", "streaks"):
        streaks = await get_streaks(db, user_id, today)
        reply = (
            f"🔥 Current streak: *{streaks['current_streak']} days*\n"
            f"🏆 Best streak: *{streaks['best_streak']} days*\n"
            f"📅 Total active days: *{streaks['total_active_days']}*"
        )
        await _send_message(chat_id, reply)
        return {"ok": True}

    # --- Meal (natural language) ---
    parsed = await _parse_meal_with_ai(text)
    if parsed and parsed.get("meal_name"):
        await tracking_service.log_meal(db, user_id, {
            "log_date": today,
            "meal_type": parsed.get("meal_type", "lunch"),
            "meal_name": parsed["meal_name"],
            "calories": parsed.get("calories", 0),
            "protein_g": parsed.get("protein_g", 0),
            "carbs_g": parsed.get("carbs_g", 0),
            "fats_g": parsed.get("fats_g", 0),
        })
        reply = (
            f"🍽️ Logged: *{parsed['meal_name']}*\n"
            f"Calories: ~{parsed.get('calories', '?')} cal\n"
            f"Protein: ~{parsed.get('protein_g', '?')}g\n\n"
            f"_Not right? Log again with correct info._"
        )
        await _send_message(chat_id, reply)
    else:
        await _send_message(chat_id, (
            "🤔 Couldn't understand that. Try:\n\n"
            "🍽️ `ate 2 roti dal rice`\n"
            "💧 `water 500`\n"
            "⚖️ `weight 72`\n"
            "📊 `summary`"
        ))

    return {"ok": True}


@router.get("/setup-webhook")
async def setup_webhook():
    """Set the Telegram webhook URL. Call once after deploying."""
    if not settings.TELEGRAM_BOT_TOKEN:
        return {"error": "TELEGRAM_BOT_TOKEN not set in environment"}

    webhook_url = f"https://health-coach-backend-rw1e.onrender.com/api/v1/telegram/webhook"
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/setWebhook"

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json={"url": webhook_url})
        return resp.json()


@router.get("/webhook-info")
async def webhook_info():
    """Check current webhook status."""
    if not settings.TELEGRAM_BOT_TOKEN:
        return {"error": "TELEGRAM_BOT_TOKEN not set"}

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getWebhookInfo"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        return resp.json()
