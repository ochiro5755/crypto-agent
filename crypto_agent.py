import os
import requests
import threading
import time
from flask import Flask
from langchain.agents import initialize_agent, Tool, AgentType
from langchain_openai import ChatOpenAI

# 1. ТАНЫ НУУЦ ТҮЛХҮҮРҮҮД
os.environ["OPENAI_API_KEY"] = "ТА_OPENAI_API_KEY_ЭНД_ХУУЛНА"
TELEGRAM_BOT_TOKEN = "BOTFATHER_ААС_АВСАН_ТОКЕНЫГ_ЭНД_ХУУЛНА"
TELEGRAM_CHAT_ID = "IDBOT_ООС_АВСАН_ӨӨРИЙН_ID_ЭНД_ХУУЛНА"

# 2. FLASK ВЕБ СЕРВЕР (Render-т амьд гэдгээ мэдэгдэх зорилготой)
app = Flask(__name__)

@app.route('/')
def home():
    return "Крипто Агент 24/7 хэвийн ажиллаж байна!"

def keep_alive():
    # Render нь 10000 гэх мэт порт шаарддаг
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 3. АГЕНТЫН ҮНДСЭН КОД
def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram алдаа: {e}")

def get_coingecko_price(coin_id: str) -> str:
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id.lower()}&vs_currencies=usd&include_24hr_change=true"
    try:
        response = requests.get(url)
        data = response.json()
        if coin_id.lower() not in data: return "Олдсонгүй."
        price = data[coin_id.lower()]['usd']
        change = data[coin_id.lower()]['usd_24h_change']
        return f"{coin_id.upper()} Үнэ: ${price}, Өөрчлөлт: {change:.2f}%"
    except Exception as e:
        return f"Алдаа: {str(e)}"

tools = [Tool(name="Crypto_Price_Checker", func=get_coingecko_price, description="Крипто үнэ шалгана.")]

def run_agent():
    llm = ChatOpenAI(temperature=0.2, model_name="gpt-4")
    agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)
    
    while True:
        try:
            print("🤖 Сигнал хайж байна...")
            user_query = "SUI болон Bitcoin-ийн үнийг шалгаад, яг одоо авах эсвэл зарах эсэхээ богинохон зөвлө."
            signal_result = agent.run(user_query)
            send_telegram_message(f"🚨 **СИГНАЛ** 🚨\n\n{signal_result}")
        except Exception as e:
            print(f"Алдаа: {e}")
        
        # 12 цаг тутамд нэг удаа ажиллана (секундээр тооцов: 12 * 60 * 60)
        time.sleep(43200) 

# 4. ВЕБ СЕРВЕР БОЛОН АГЕНТЫГ ЗЭРЭГ АЖИЛЛУУЛАХ
if __name__ == "__main__":
    # Flask веб серверийг тусдаа Thread дээр ажиллуулах
    server = threading.Thread(target=keep_alive)
    server.start()
    
    # Үндсэн Агентыг ажиллуулах
    run_agent()
