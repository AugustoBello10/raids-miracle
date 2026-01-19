import discord
import requests
import pytz
import time
import os
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread
from discord import app_commands, ui
from calculadora import calcular_crafting_detalhado
from itens import RECEITAS, CATEGORIAS
from idiomas import TEXTOS # Importa as traduções

# ==========================================
# 🔑 CONFIGURAÇÕES
# ==========================================
TOKEN = os.environ.get('DISCORD_TOKEN') 
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')

URL_RAIDS = "https://miracle74.com/?subtopic=raids"
FUSO_BRASILIA = pytz.timezone('America/Sao_Paulo')

# ==========================================
# 🌐 FLASK & RAIDS (CÓDIGO PADRÃO)
# ==========================================
app = Flask('')

@app.route('/')
def home(): return "Bot Bellão Global Online!"

def run_web_server(): app.run(host='0.0.0.0', port=8080)

def carregar_raids():
    # ... (mesmo código de antes, omitido para economizar espaço visual) ...
    # Copie a função carregar_raids do seu código anterior ou mantenha se não mudou
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
                    except ValueError: continue
        return raids_info
    except: return []

def loop_monitoramento():
    if not WEBHOOK_URL: return
    while True:
        try:
            agora_br = datetime.now(FUSO_BRASILIA)
            raids = carregar_raids()
            for raid in raids:
                diff = (raid['proxima'] - agora_br).total_seconds() / 60
                if 14.5 < diff <= 15.5: 
                    msg = f"⚠️ **RAID:** {raid['nome']} @ {raid['proxima'].strftime('%H:%M')} (BRT)"
                    requests.post(WEBHOOK_URL, json={"content": msg})
            time.sleep(60)
        except: time.sleep(60)

# ==========================================
# 🧮 CALCULADORA MULTILÍNGUE
# ==========================================

# 4. MODAL DE CÁLCULO (Agora recebe o idioma 'lang')
class DynamicCraftingModal(ui.Modal):
    def __init__(self, item_name, receita_data, lang):
        self.lang = lang
        t = TEXTOS[lang] # Carrega os textos do idioma escolhido
        
        super().__init__(title=t['modal_title'].format(item_name))
        self.item_name = item_name
        self.receita_data = receita_data
        
        resumo = " | ".join([f"{q}x {m[:8]}" for m, q in receita_data['ingredientes'].items()])
        
        self.add_item(ui.TextInput(
            label=t['label_skill'],
            placeholder=t['placeholder_skill'].format(resumo), 
            custom_id="skill", min_length=1, max_length=3
        ))
        
        self.add_item(ui.TextInput(
            label=t['label_qtd'],
            placeholder=t['placeholder_qtd'], default="1", custom_id="qtd"
        ))
        
        self.materiais_na_janela = list(receita_data['ingredientes'].items())[:3]
        for material, qtd_base in self.materiais_na_janela:
            perde = t['yes'] if material not in receita_data.get('nao_perde', []) else t['no']
            self.add_item(ui.TextInput(
                label=t['label_price'].format(material, qtd_base),
                placeholder=t['placeholder_price'].format(perde),
                custom_id=f"price_{material}"
            ))

    async def on_submit(self, interaction: discord.Interaction):
        t = TEXTOS[self.lang]
        try:
            skill = int(self.children[0].value)
            qtd_desejada = int(self.children[1].value)
            
            ingredientes_calculo = {}
            for i, (material, qtd_base) in enumerate(self.materiais_na_janela):
                preco = float(self.children[i+2].value)
                consome = material not in self.receita_data.get('nao_perde', [])
                ingredientes_calculo[material] = {"qtd": qtd_base, "preco": preco, "consome_na_falha": consome}

            res = calcular_crafting_detalhado(skill, self.receita_data['multiplicador'], ingredientes_calculo, qtd_desejada)

            embed = discord.Embed(title=t['result_title'].format(qtd_desejada, self.item_name), color=discord.Color.blue())
            embed.add_field(name=t['chance'], value=f"{res['chance_sucesso']}%", inline=True)
            embed.add_field(name=t['cost'], value=f"{res['custo_total']:,} gp", inline=True)
            
            mat_txt = "\n".join([f"• **{m}**: {q}" for m, q in res['materiais_necessarios'].items()])
            embed.add_field(name=t['list'], value=mat_txt, inline=False)
            embed.set_footer(text=t['footer'].format(interaction.user.display_name))
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except:
            await interaction.response.send_message("❌ Error: Numbers only / Apenas números", ephemeral=True)

# 3. SELEÇÃO DE ITEM
class ItemSelect(ui.Select):
    def __init__(self, categoria_key, lang):
        self.lang = lang
        itens_nomes = CATEGORIAS[categoria_key]
        itens_nomes.sort()
        
        options = []
        for nome in itens_nomes:
            if nome in RECEITAS:
                data = RECEITAS[nome]
                options.append(discord.SelectOption(label=nome, description=f"Mult: {data['multiplicador']}"))
        
        t = TEXTOS[lang]
        cat_nome_traduzido = t['cats'][categoria_key]
        super().__init__(placeholder=t['ask_item'].format(cat_nome_traduzido), options=options)

    async def callback(self, interaction: discord.Interaction):
        item_escolhido = self.values[0]
        receita = RECEITAS[item_escolhido]
        await interaction.response.send_modal(DynamicCraftingModal(item_escolhido, receita, self.lang))

# 2. SELEÇÃO DE CATEGORIA
class CategorySelect(ui.Select):
    def __init__(self, lang):
        self.lang = lang
        t = TEXTOS[lang]
        
        # Cria as opções traduzidas usando o código da categoria (key) e o texto traduzido (val)
        options = []
        for key, val in t['cats'].items():
            options.append(discord.SelectOption(label=val, value=key))
            
        super().__init__(placeholder=t['select_cat'], options=options)

    async def callback(self, interaction: discord.Interaction):
        cat_key = self.values[0] # Ex: 'relics'
        view = ui.View()
        view.add_item(ItemSelect(cat_key, self.lang))
        
        t = TEXTOS[self.lang]
        cat_traduzida = t['cats'][cat_key]
        await interaction.response.edit_message(content=t['ask_category'], view=view)

# 1. SELEÇÃO DE IDIOMA (NOVO INÍCIO)
class LanguageSelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Português", emoji="🇧🇷", value="pt", description="Calculadora em Português"),
            discord.SelectOption(label="English", emoji="🇺🇸", value="en", description="Calculator in English"),
            discord.SelectOption(label="Polski", emoji="🇵🇱", value="pl", description="Kalkulator po Polsku")
        ]
        super().__init__(placeholder="Select Language / Escolha o Idioma...", options=options)

    async def callback(self, interaction: discord.Interaction):
        lang = self.values[0]
        t = TEXTOS[lang]
        
        view = ui.View()
        view.add_item(CategorySelect(lang))
        await interaction.response.send_message(t['select_lang'], view=view, ephemeral=True)

class PersistentControlView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="🧮 Abrir Calculadora / Open Calc", style=discord.ButtonStyle.green, custom_id="btn_abrir_calc")
    async def abrir_calc(self, interaction: discord.Interaction, button: ui.Button):
        # O botão agora abre o menu de idiomas primeiro
        view = ui.View()
        view.add_item(LanguageSelect())
        await interaction.response.send_message("🇧🇷 🇺🇸 🇵🇱", view=view, ephemeral=True)

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
    embed = discord.Embed(title="⚒️ Miracle 7.4 - Crafting Calculator", description="Click below to start / Clique abaixo", color=discord.Color.gold())
    await interaction.response.send_message(embed=embed, view=PersistentControlView())

if __name__ == "__main__":
    if not TOKEN: print("ERRO: Configure TOKEN")
    else:
        t_flask = Thread(target=run_web_server); t_flask.daemon = True; t_flask.start()
        t_raids = Thread(target=loop_monitoramento); t_raids.daemon = True; t_raids.start()
        bot.run(TOKEN)
