import time
import requests
import logging
import sys
import threading
from datetime import datetime
from flask import Flask

# سيرفر وهمي لإرضاء Render مجاناً
app = Flask(__name__)

@app.route('/')
def home():
    return "Grand Trust Bot is Running Active 24/7!"

# إعداد الـ Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# ==========================================
# الإعدادات والبيانات
# ==========================================
FIREBASE_BASE_URL = "https://osama-tarek-default-rtdb.firebaseio.com"
CLIENTS_URL = f"{FIREBASE_BASE_URL}/clients.json"
SENT_LOGS_URL = f"{FIREBASE_BASE_URL}/sent_notifications"

BOT_TOKEN = "8624450859:AAGBoqjjPlLrTYnBIAgwE7ZJneEa5McJTiI"
CHAT_ID = "-1004488850546"


def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        response = requests.post(url, json=payload, timeout=10)
        res_data = response.json()
        if res_data.get("ok"):
            logging.info("تم إرسال التنبيه إلى الجروب عبر تليجرام بنجاح! ✅")
            return True
        else:
            logging.error(f"فشل إرسال تليجرام: {res_data.get('description')}")
            return False
    except Exception as e:
        logging.error(f"خطأ أثناء الاتصال بتليجرام: {e}")
        return False


def is_already_sent(client_key, today_date):
    url = f"{SENT_LOGS_URL}/{today_date}/{client_key}.json"
    try:
        response = requests.get(url, timeout=10)
        return response.json() is not None
    except Exception as e:
        logging.error(f"خطأ أثناء فحص سجل الإشعارات في Firebase: {e}")
        return False


def mark_as_sent(client_key, today_date):
    url = f"{SENT_LOGS_URL}/{today_date}/{client_key}.json"
    try:
        requests.put(url, json={"sent_at": datetime.now().isoformat()}, timeout=10)
        logging.info(f"تم تسجيل الإشعار كـ 'مرسل' في قاعدة البيانات للعميل {client_key}")
    except Exception as e:
        logging.error(f"خطأ أثناء تسجيل الإشعار في Firebase: {e}")


def check_installments():
    today = datetime.now().strftime('%Y-%m-%d')
    current_time = datetime.now().strftime('%H:%M:%S')

    try:
        headers = {'Cache-Control': 'no-cache'}
        response = requests.get(CLIENTS_URL, headers=headers, timeout=10)
        
        if response.status_code != 200:
            logging.error(f"خطأ في جلب بيانات Firebase: {response.status_code}")
            return

        clients = response.json()

        if not clients:
            logging.info("لا توجد بيانات في قاعدة البيانات.")
            return

        for key, client in clients.items():
            if not isinstance(client, dict):
                continue

            name = client.get('name', 'عميل غير معروف')
            phone = client.get('phone', 'غير متوفر')
            tower_name = client.get('towerName', 'غير متوفر')
            tower_num = client.get('towerNum', 'غير متوفر')
            installment_dates = client.get('installmentDates', {})

            if isinstance(installment_dates, dict):
                dates_list = list(installment_dates.values())
            elif isinstance(installment_dates, list):
                dates_list = installment_dates
            else:
                dates_list = []

            if today in dates_list:
                if not is_already_sent(key, today):
                    msg = (
                        f"▬▬▬▬ GRAND TRUST ▬▬▬▬\n\n"
                        f"👤 العميل: {name}\n"
                        f"📞 الهاتف: {phone}\n"
                        f"🏢 البرج: {tower_name}\n"
                        f"🔢 رقم البرج: {tower_num}\n\n"
                        f"⏱️ الوقت: {current_time}\n"
                        f"📅 التاريخ: {today}\n\n"
                        f"⚠️ تنبيه: عليه سداد دفعة اليوم!"
                    )
                    
                    if send_telegram_message(msg):
                        mark_as_sent(key, today)
                else:
                    logging.info(f"العميل {name} تم إرسال تنبيه له مسبقاً اليوم.")

    except Exception as e:
        logging.error(f"حدث خطأ أثناء فحص قاعدة البيانات: {e}")


def run_bot_loop():
    logging.info("تم تشغيل نظام مراقبة وتنبيهات جراند تراست 24/7 بنجاح 🚀")
    send_telegram_message("🟢 **تم بدء تشغيل سيرفر مراقبة أقساط جراند تراست بنجاح!**")

    while True:
        try:
            check_installments()
            sys.stdout.flush()
            time.sleep(30)
        except Exception as e:
            logging.error(f"خطأ غير متوقع: {e}")
            time.sleep(10)


# تشغيل سكريبت الفحص في الخلفية
threading.Thread(target=run_bot_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
