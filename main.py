import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import time
from flask import Flask
from threading import Thread

# --- CONFIGURAÇÕES ---
WEBHOOK_URL = "https://discord.com/api/webhooks/1462857369846419571/zgVLwzsS4gAl_y6Wqxt7xawpx9x5Z8MaWkrmw7hLBIdT9DSIATIYTPXaBTKHCIwoQkk4"
URL_RAIDS = "https://miracle74.com/?subtopic=raids"
FUSO_BRASILIA = pytz.timezone('America/Sao_Paulo')

app = Flask('')

@app.route('/')
def home():
    return "Bot de Raids está online!"

def run_web_server():
    app.run(host='0.0.0.0', port=8080)

def carregar_raids():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(URL_RAIDS, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        if not table: return []

        raids_info = []
        rows = table.find_all('tr')[1:] 

        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 3:
                nome = cols[0].text.strip()
                intervalo_txt = ''.join(filter(str.isdigit, cols[1].text))
                intervalo_horas = int(intervalo_txt) if intervalo_txt else 0
                ultima_exec_str = cols[2].text.strip()

                if ultima_exec_str and intervalo_horas > 0:
                    ultima_exec = datetime.strptime(ultima_exec_str, '%Y-%m-%d %H:%M:%S')
                    ultima_exec = FUSO_BRASILIA.localize(ultima_exec)
                    proxima_raid = ultima_exec + timedelta(hours=intervalo_horas)
                    raids_info.append({"nome": nome, "proxima": proxima_raid})
        return raids_info
    except:
        return []

def loop_monitoramento():
    print("Monitor de Raids iniciado...")
    while True:
        agora_br = datetime.now(FUSO_BRASILIA)
        raids = carregar_raids()
        for raid in raids:
            diff = (raid['proxima'] - agora_br).total_seconds() / 60
            if 14.5 < diff <= 15.5: # Aviso de 15 minutos
                msg = f"⚠️ **RAID EM 15 MIN:** {raid['nome']} às {raid['proxima'].strftime('%H:%M')} (Brasília)"
                requests.post(WEBHOOK_URL, json={"content": msg})
        time.sleep(60)

# Inicia o servidor web e o bot juntos
if __name__ == "__main__":
    t = Thread(target=loop_monitoramento)
    t.start()
    run_web_server()