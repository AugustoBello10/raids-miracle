import discord
import requests
import pytz
import time
import os  # Biblioteca para ler as variáveis de ambiente (Segurança)
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread
from discord import app_commands, ui
from calculadora import calcular_crafting_detalhado
from itens import RECEITAS

# ==========================================
# 🔑 CONFIGURAÇÕES DE SEGURANÇA (LEIA COM ATENÇÃO)
# ==========================================
# O código agora busca essas chaves nas configurações do Render/PC
# Se você tentar rodar sem configurar, ele vai avisar o erro.
TOKEN = os.environ.get('DISCORD_TOKEN') 
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')

# Configurações do Site e Fuso Horário
URL_RAIDS = "https://miracle74.com/?subtopic=raids"
FUSO_BRASILIA = pytz.timezone('America/Sao_Paulo')

# ==========================================
# 🌐 1. SERVIDOR WEB (FLASK)
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "Bot Bellão (Raids + Calc) está ONLINE!"

def run_web_server():
    app.run(host='0.0.0.0', port=8080)

# ==========================================
# ⚔️ 2. MONITORAMENTO DE RAIDS
# ==========================================
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
                    try:
                        ultima_exec = datetime.strptime(ultima_exec_str, '%Y-%m-%d %H:%M:%S')
                        ultima_exec = FUSO_BRASILIA.localize(ultima_exec) if ultima_exec.tzinfo is None else ultima_exec
                        proxima_raid = ultima_exec + timedelta(hours=intervalo_horas)
                        raids_info.append({"nome": nome, "proxima": proxima_raid})
                    except ValueError:
                        continue
        return raids_info
    except Exception as e:
        print(f"Erro ao ler site: {e}")
        return []

def loop_monitoramento():
    print("👀 Monitor de Raids iniciado...")
    if not WEBHOOK_URL:
        print("⚠️ AVISO: Webhook não configurado!")
        return

    while True:
        try:
            agora_br = datetime.now(FUSO_BRASILIA)
            raids = carregar_raids()
            for raid in raids:
                diff = (raid['proxima'] - agora_br).total_seconds() / 60
                if 14.5 < diff <= 15.5: 
                    msg = f"⚠️ **RAID EM 15 MIN:** {raid['nome']} às {raid['proxima'].strftime('%H:%M')} (Brasília)"
                    requests.post(WEBHOOK_URL, json={"content": msg})
                    print(f"Alerta enviado: {raid['nome']}")
            time.sleep(60)
        except Exception as e:
            print(f"Erro no loop: {e}")
            time.sleep(60)

# ==========================================
# 🧮 3. CALCULADORA (DISCORD BOT)
# ==========================================
class DynamicCraftingModal(ui.Modal):
    def __init__(self, item_name, receita_data):
        super().__init__(title=f"Calcular: {item_name}")
        self.item_name = item_name
        self.receita_data = receita_data
        
        resumo = " | ".join([f"{q}x {m[:8]}" for m, q in receita_data['ingredientes'].items()])
        
        self.add_item(ui.TextInput(
            label="Seu Skill de Crafting",
            placeholder=f"Receita 1un: {resumo}", 
            custom_id="skill", min_length=1, max_length=3
        ))
        
        self.add_item(ui.TextInput(
            label="Quantas unidades quer produzir?",
            placeholder="Ex: 10", default="1", custom_id="qtd", min_length=1
        ))
        
        self.materiais_na_janela = list(receita_data['ingredientes'].items())[:3]
        for material, qtd_base in self.materiais_na_janela:
            perde = "Sim" if material not in receita_data.get('nao_perde', []) else "Não"
            self.add_item(ui.TextInput(
                label=f"Preço {material} (Usa {qtd_base} p/ un.)",
                placeholder=f"Perde na falha: {perde}",
                custom_id=f"price_{material}"
            ))

    async def on_submit(self, interaction: discord.Interaction):
        try:
            skill = int(self.children[0].value)
            qtd_desejada = int(self.children[1].value)
            
            ingredientes_calculo = {}
            for i, (material, qtd_base) in enumerate(self.materiais_na_janela):
                preco = float(self.children[i+2].value)
                consome = material not in self.receita_data.get('nao_perde', [])
                ingredientes_calculo[material] = {"qtd": qtd_base, "preco": preco, "consome_na_falha": consome}

            res = calcular_crafting_detalhado(skill, self.receita_data['multiplicador'], ingredientes_calculo, qtd_desejada)

            embed = discord.Embed(title=f"⚒️ Resultado: {qtd_desejada}x {self.item_name}", color=discord.Color.blue())
            embed.add_field(name="🎯 Chance Sucesso", value=f"{res['chance_sucesso']}%", inline=True)
            embed.add_field(name="💰 Custo Total", value=f"{res['custo_total']:,} gp", inline=True)
            
            mat_txt = "\n".join([f"• **{m}**: {q}" for m, q in res['materiais_necessarios'].items()])
            embed.add_field(name="📦 Lista de Compras", value=mat_txt, inline=False)
            embed.set_footer(text=f"Calculado para {interaction.user.display_name} | Manaus: {datetime.now().strftime('%H:%M')}")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro: Use apenas números. {e}", ephemeral=True)

class CraftingDropdown(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=nome, description=f"Multiplicador: {data['multiplicador']}") 
            for nome, data in RECEITAS.items()
        ]
        super().__init__(placeholder="Selecione o item para calcular...", options=options)

    async def callback(self, interaction: discord.Interaction):
        item_escolhido = self.values[0]
        await interaction.response.send_modal(DynamicCraftingModal(item_escolhido, RECEITAS[item_escolhido]))

class PersistentControlView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="🧮 Abrir Calculadora", style=discord.ButtonStyle.green, custom_id="btn_abrir_calc")
    async def abrir_calc(self, interaction: discord.Interaction, button: ui.Button):
        view = ui.View()
        view.add_item(CraftingDropdown())
        await interaction.response.send_message("Escolha o item na lista abaixo:", view=view, ephemeral=True)

class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.add_view(PersistentControlView())
        await self.tree.sync()

bot = MyBot()

@bot.tree.command(name="setup_calculadora", description="Ativa o botão fixo")
async def setup_calculadora(interaction: discord.Interaction):
    embed = discord.Embed(title="⚒️ Central de Crafting - Miracle 7.4", description="Clique abaixo para calcular.", color=discord.Color.gold())
    await interaction.response.send_message(embed=embed, view=PersistentControlView())

if __name__ == "__main__":
    if not TOKEN:
        print("ERRO CRÍTICO: Token não encontrado. Configure no Render!")
    else:
        t_flask = Thread(target=run_web_server)
        t_flask.daemon = True
        t_flask.start()
        
        t_raids = Thread(target=loop_monitoramento)
        t_raids.daemon = True
        t_raids.start()

        bot.run(TOKEN)
