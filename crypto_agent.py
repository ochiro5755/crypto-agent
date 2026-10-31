import os
import requests
import threading
import time
from flask import Flask

# Шинэчлэгдсэн импортууд (Шинэ LangChain стандартаар)
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain_core.prompts import PromptTemplate

# ==========================================
# 1. ТАНЫ НУУЦ ТҮЛХҮҮРҮҮД
# ==========================================
# os.environ["OPENAI_API_KEY"] = ... (Энэ мөрийг бүр устгана, учир нь Render автоматаар оруулна)

# Системээс нууц түлхүүрүүдийг дуудаж авах
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("АЛДАА: Telegram токен олдсонгүй!")

# ==========================================
# 2. FLASK ВЕБ СЕРВЕР (Render-т амьд гэдгээ мэдэгдэх)
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "Крипто Агент 24/7 хэвийн ажиллаж байна!"

def keep_alive():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# ==========================================
# 3. АГЕНТЫН ҮНДСЭН КОД
# ==========================================
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

# Багажаа бүртгэх
tools = [
    Tool(
        name="Crypto_Price_Checker",
        func=get_coingecko_price,
        description="Крипто валютын үнэ болон өөрчлөлтийг шалгана. Оролт нь койны англи нэр (жишээ нь: sui) байна."
    )
]

def run_agent():
    # 1. Тархи (LLM) бэлтгэх
    llm = ChatOpenAI(temperature=0.2, model="gpt-4")
    
    # 2. Шинэ загварын Prompt бэлтгэх
    template = '''Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}'''
    
    prompt = PromptTemplate.from_template(template)

    # 3. Агентыг угсрах (Шинэ стандартаар)
    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    # 4. Байнгын давтамжтай ажиллуулах
    while True:
        try:
            print("🤖 Сигнал хайж байна...")
            user_query = "SUI болон Bitcoin-ийн үнийг шалгаад, яг одоо авах эсвэл зарах эсэхээ богинохон зөвлө."
            
            # Агентаар бодуулах
            result = agent_executor.invoke({"input": user_query})
            signal_result = result['output']
            
            # Telegram руу илгээх
            send_telegram_message(f"🚨 **СИГНАЛ** 🚨\n\n{signal_result}")
        except Exception as e:
            print(f"Алдаа: {e}")
        
        # 12 цаг тутамд нэг удаа ажиллана (43200 секунд)
        time.sleep(43200) 

# ==========================================
# 4. ПРОГРАММЫГ ЭХЛҮҮЛЭХ
# ==========================================
if __name__ == "__main__":
    server = threading.Thread(target=keep_alive)
    server.start()
    run_agent()
