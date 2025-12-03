import os
import logging
import html
import re
from collections import deque
from datetime import datetime
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, Defaults

# --- AYARLAR ---
from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_GEMINI_KEY = os.getenv("GOOGLE_GEMINI_KEY")
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME")
SHEET_CREDENTIALS_FILE = "credentials.json" # dowloand JSON dosyasının adı

# --- KURULUMLAR ---
# Loglama
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Gemini AI Kurulumu
genai.configure(api_key=GOOGLE_GEMINI_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# Google Sheets Bağlantısı
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(SHEET_CREDENTIALS_FILE, scope)
client = gspread.authorize(creds)
sheet = client.open(SPREADSHEET_NAME).sheet1 # İlk sayfayı alır
codes_sheet = client.open(SPREADSHEET_NAME).worksheet("Codes") # "Codes" isimli sayfayı alır
logs_sheet = client.open(SPREADSHEET_NAME).worksheet("Logs") # "Logs" sayfasını alır

# basic chat memeory
MEMORY_LIMIT = 5
TEXT_SNIPPET_LIMIT = 180
conversation_history = {}


def _get_history(user_id):
    return conversation_history.setdefault(user_id, deque(maxlen=MEMORY_LIMIT))


def append_history(user_id, role, content, entry_type="text"):
    if not content:
        return
    history = _get_history(user_id)
    history.append({"role": role, "content": content, "type": entry_type})


def get_history_text(user_id):
    history = conversation_history.get(user_id)
    if not history:
        return ""
    lines = []
    for entry in history:
        text = entry['content']
        if entry.get('type') != 'photo' and len(text) > TEXT_SNIPPET_LIMIT:
            text = text[:TEXT_SNIPPET_LIMIT - 3].rstrip() + "..."
        lines.append(f"{entry['role']}: {text}")
    return "\n".join(lines)


BOLD_PATTERN = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)


def format_for_telegram(text: str) -> str:
    """Escape HTML chars but render **kalın** bloklarını <b> etiketiyle."""
    if not text:
        return ""

    parts = []
    last = 0
    for match in BOLD_PATTERN.finditer(text):
        parts.append(html.escape(text[last:match.start()]))
        parts.append(f"<b>{html.escape(match.group(1))}</b>")
        last = match.end()
    parts.append(html.escape(text[last:]))
    return "".join(parts)

# --- YARDIMCI FONKSİYONLAR ---

def get_user_data(user_id):
    """Kullanıcı verisini Sheet'ten çeker, yoksa oluşturur."""
    try:
        cell = sheet.find(str(user_id))
        if cell:
            row_data = sheet.row_values(cell.row)
            # Yapı: [user_id, message_count, max_limit]
            return {"row": cell.row, "count": int(row_data[1]), "limit": int(row_data[2])}
        else:
            # Yeni kullanıcı oluştur
            sheet.append_row([str(user_id), 0, 10]) # Başlangıç limiti 10
            return {"row": sheet.row_count, "count": 0, "limit": 10}
    except Exception as e:
        logging.error(f"Sheet hatası: {e}")
        return None

def update_usage(row, current_count):
    """Kullanım sayısını artırır."""
    try:
        sheet.update_cell(row, 2, current_count + 1)
    except Exception as e:
        logging.error(f"Güncelleme hatası: {e}")

def add_quota(user_id, amount=10):
    """Kullanıcıya ek kota tanımlar (/kod komutu için)."""
    data = get_user_data(user_id)
    if data:
        new_limit = data['limit'] + amount
        sheet.update_cell(data['row'], 3, new_limit)
        return True
    return False

def check_code_validity(code_text):
    """Kodun geçerli olup olmadığını kontrol eder."""
    try:
        # Codes sayfasındaki A sütununda kodları arar
        codes = codes_sheet.col_values(1)
        if code_text in codes:
            return True
        return False
    except:
        return False

# --- TELEGRAM BOT FONKSİYONLARI ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("hi! i am Adil AI. I am here to answer your questions and analyze images.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    stripped_message = user_message.strip() if user_message else ""
    quoted_text = ""
    if update.message.reply_to_message:
        replied = update.message.reply_to_message
        quoted_text = replied.text or replied.caption or ""
    history_text = get_history_text(user_id)
    
    # 1. KOTA KONTROLÜ
    user_data = get_user_data(user_id)
    
    if not user_data:
        await update.message.reply_text("System error: User data could not be retrieved.")
        return

    # Has the quota been used up?
    if user_data['count'] >= user_data['limit']:
        await update.message.reply_text("⚠️ You have run out of message rights. Use the /kod command to earn new rights.")
        return

    # 2. GEMINI'YE SOR
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        
        prompt = "You are a helpful bot. and engilsh answer ."
        if history_text:
            prompt += f"\nSon konuşmalardan alıntılar:\n{history_text}"
        prompt += f"\nKullanıcının yeni sorusu: {user_message}"
        if quoted_text:
            prompt += f"\nKullanıcının alıntıladığı mesaj: {quoted_text}"

        response = model.generate_content(prompt)
        reply_text = response.text

        safe_text = format_for_telegram(reply_text)
        await update.message.reply_text(safe_text)

        # 3. CEVABI GÖNDER VE KOTAYI GÜNCELLE
        update_usage(user_data['row'], user_data['count'])
        append_history(user_id, "Kullanıcı", user_message)
        append_history(user_id, "Bot", reply_text)

        # --- LOGLAMA ---
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_name = update.effective_user.first_name or ""
        logs_sheet.append_row([now, str(user_id), user_name, user_message or "", reply_text or ""])
        
    except Exception as e:
        await update.message.reply_text("An error occurred, please try again.")
        logging.error(f"AI Error: {e}")


async def handle_code_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/kod komutu üzerinden kota ekleyip kullanıcıyı bilgilendirir."""
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)

    if not user_data:
        await update.message.reply_text("System error: User data could not be retrieved.")
        return

    # Argüman yoksa /kod123 gibi birleşik yazımları yakalamak için metnin geri kalanını al
    if context.args:
        code_part = " ".join(context.args).strip()
    else:
        message_text = update.message.text or ""
        code_part = message_text[len("/kod"):].strip()

    if not code_part:
        await update.message.reply_text("❌ Code not found. Please send it as /kod 1234.")
        return

    if check_code_validity(code_part):
        add_quota(user_id, 10)
        await update.message.reply_text("✅ Code is valid! 10 rights have been added to your account.")
    else:
        await update.message.reply_text("❌ Invalid code.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Quota Control
    user_data = get_user_data(user_id)
    if user_data['count'] >= user_data['limit']:
        await update.message.reply_text("⚠️ You have run out of message rights.")
        return

    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='upload_photo')
        
        # Fotoğrafı indir
        photo_file = await update.message.photo[-1].get_file()
        file_path = "temp_image.jpg"
        await photo_file.download_to_drive(file_path)

        # Gemini Vision'a gönder
        import PIL.Image

        caption = update.message.caption.strip() if update.message.caption else ""
        history_text = get_history_text(user_id)
        prompt = "What is in this image? Explain briefly and clearly."
        if history_text:
            prompt = f"Recent chat summary:\n{history_text}\n\n" + prompt
        if caption:
            prompt += f" User caption: {caption}"

        with PIL.Image.open(file_path) as img:
            response = model.generate_content([prompt, img])

        safe_text = format_for_telegram(response.text)
        await update.message.reply_text(safe_text)
        photo_note = "Fotoğraf gönderdi. " + (f"Açıklama: {caption}" if caption else "Açıklama yok.")
        append_history(user_id, "Kullanıcı", photo_note, entry_type="photo")
        append_history(user_id, "Bot", response.text)
        
        # Kotayı düş ve temizlik yap
        update_usage(user_data['row'], user_data['count'])

    except Exception as e:
        await update.message.reply_text("An error occurred while processing the image.")
        logging.error(f"Image Error: {e}")
    finally:
        if os.path.exists("temp_image.jpg"):
            try:
                os.remove("temp_image.jpg")
            except OSError:
                pass

# --- ANA PROGRAM ---
if __name__ == '__main__':
    defaults = Defaults(parse_mode=ParseMode.HTML)
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).defaults(defaults).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('kod', handle_code_command))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("Bot working...")
    application.run_polling()