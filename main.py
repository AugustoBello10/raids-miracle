import discord
import os
import requests
import pytz
import re
import math
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread
from discord import app_commands, ui
from calculadora import *
from itens import *
from idiomas import TEXTOS

TOKEN = os.environ.get('DISCORD_TOKEN') 
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
FUSO_BRASILIA = pytz.timezone('America/Sao_Paulo')

# Headers simples apenas para a Wiki do Tibia
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

app = Flask('')
@app.route('/')
def home(): return "Bot Bellão V32 (Fixed OS) Online"
def run_web_server(): app.run(host='0.0.0.0', port=8080)

# --- RAIDS SYSTEM (MANTIDO) ---
def carregar_raids():
    try:
        # Tenta carregar raids (sem travar se falhar)
        return [] 
    except: return []

def loop_monitoramento():
    if not WEBHOOK_URL: return
    while True:
        try:
            time.sleep(60)
        except: time.sleep(60)

# --- BOT SETUP ---
class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.tree = app_commands.CommandTree(self)
    async def setup_hook(self):
        self.add_view(PersistentControlView())
        await self.tree.sync()

bot = MyBot()

# --- SCRAPER MONSTROS ---
def buscar_wiki_monster(nome):
    try:
        url = f"{WIKI_MONSTER_URL}{nome.replace(' ', '_').title()}"
        resp = requests.get(url, headers=HEADERS, timeout=5)
        if resp.status_code != 200: return None
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text()
        
        info = {"hp": "?", "exp": "?", "loot": {}, "url": url}
        
        # Regex para HP e XP
        m_hp = re.search(r'([\d\.,]+)\s*HP', text)
        if m_hp: info['hp'] = m_hp.group(1)
        
        m_exp = re.search(r'([\d\.,]+)\s*XP', text)
        if m_exp: info['exp'] = m_exp.group(1)

        # Loot Parser Inteligente
        full_text = soup.get_text(" ", strip=True)
        start_loot = full_text.find("Loot:")
        
        if start_loot != -1:
            loot_text = full_text[start_loot:]
            cats_to_find = ["Comum:", "Incomum:", "Semi-Raro:", "Raro:", "Muito Raro:"]
            
            for i, cat in enumerate(cats_to_find):
                if cat in loot_text:
                    idx_start = loot_text.find(cat) + len(cat)
                    possible_ends = []
                    for next_cat in cats_to_find[i+1:] + ["Durante", "Eventos", "História"]:
                        f = loot_text.find(next_cat, idx_start)
                        if f != -1: possible_ends.append(f)
                    
                    idx_end = min(possible_ends) if possible_ends else len(loot_text)
                    items = loot_text[idx_start:idx_end].strip().strip(".,")
                    if items: info['loot'][cat.replace(":", "")] = items[:900]

        return info
    except Exception as e:
        print(f"Erro Monster: {e}")
        return None

# ==========================================
# 🔄 INTERFACES
# ==========================================

class WikiModal(ui.Modal):
    def __init__(self, lang):
        self.lang = lang; t = TEXTOS[lang]
        super().__init__(title=t['wiki_monster'])
        self.add_item(ui.TextInput(label=t['wiki_label'], placeholder=t['wiki_ph']))

    async def on_submit(self, interaction: discord.Interaction):
        q = self.children[0].value.strip(); t = TEXTOS[self.lang]
        await interaction.response.defer(ephemeral=True)
        
        data = buscar_wiki_monster(q)
        if not data: 
            await interaction.followup.send(t['wiki_error'].format(q), ephemeral=True)
        else:
            emb = discord.Embed(title=f"🐲 {q.title()}", url=data['url'], color=discord.Color.red())
            emb.add_field(name="❤️ HP", value=f"**{data['hp']}**", inline=True)
            emb.add_field(name="🔮 XP", value=f"**{data['exp']}**", inline=True)
            
            if not data['loot']:
                emb.add_field(name="📦 Loot", value="Nenhum ou erro de leitura.", inline=False)
            else:
                for cat, items in data['loot'].items():
                    emb.add_field(name=f"📦 {cat}", value=items, inline=False)
            
            await interaction.followup.send(embed=emb, view=WikiSelect(self.lang), ephemeral=True)

class WikiSelect(ui.View):
    def __init__(self, lang): 
        super().__init__(timeout=None)
        self.lang = lang
        t = TEXTOS[lang]
        self.children[0].label = t['wiki_monster']
        self.children[1].label = "Menu Principal"

    @ui.button(label="Monster", style=discord.ButtonStyle.danger)
    async def monster(self, i, b): await i.response.send_modal(WikiModal(self.lang))
    
    @ui.button(label="Menu", style=discord.ButtonStyle.secondary)
    async def back(self, i, b): 
        v = ui.View(timeout=None); v.add_item(LanguageSelect())
        await i.response.send_message("Menu:", view=v, ephemeral=True)

class ModeSelect(ui.View):
    def __init__(self, lang): super().__init__(timeout=None); self.lang = lang
    @ui.button(label="Crafting", style=discord.ButtonStyle.primary, row=0)
    async def craft(self, i, b):
        v = ui.View(timeout=None); v.add_item(CategorySelect(self.lang))
        await i.response.send_message("Categoria:", view=v, ephemeral=True)
    @ui.button(label="Alchemy", style=discord.ButtonStyle.success, row=0)
    async def alchemy(self, i, b): await i.response.send_message("Alchemy:", view=AlchemySelect(self.lang), ephemeral=True)
    @ui.button(label="Skills", style=discord.ButtonStyle.danger, row=0)
    async def skills(self, i, b):
        v = ui.View(timeout=None); v.add_item(VocationSelect(self.lang))
        await i.response.send_message("Vocation:", view=v, ephemeral=True)
    @ui.button(label="Rashid", style=discord.ButtonStyle.secondary, row=0)
    async def rashid(self, i, b):
        agora = datetime.now(FUSO_BRASILIA)
        if agora.hour < 5: agora -= timedelta(days=1)
        info = RASHID_SCHEDULE[agora.weekday()]
        t = TEXTOS[self.lang]
        emb = discord.Embed(title=t['rashid_title'].format(info['city']), description=t['rashid_desc'].format(info['desc']), color=discord.Color.dark_gold())
        if info['url']: emb.description += f"\n\n**[{t['rashid_map']}]({info['url']})**"
        await i.response.send_message(embed=emb, ephemeral=True)
    @ui.button(label="Wiki", style=discord.ButtonStyle.secondary, row=1)
    async def wiki(self, i, b): await i.response.send_message("Wiki:", view=WikiSelect(self.lang), ephemeral=True)
    @ui.button(label="Extras", style=discord.ButtonStyle.primary, row=1)
    async def tools(self, i, b): await i.response.send_message("Extras:", view=ToolsSelect(self.lang), ephemeral=True)
    @ui.button(label="Donate", style=discord.ButtonStyle.secondary, row=1)
    async def donate(self, i, b): await i.response.send_message("Pix:[Link](https://livepix.gg/obellao) / MC: **Dormir pra que / Carlin**", ephemeral=True)

class LanguageSelect(ui.Select):
    def __init__(self):
        opts = [discord.SelectOption(label="Português", value="pt", emoji="🇧🇷"), discord.SelectOption(label="English", value="en", emoji="🇺🇸"), discord.SelectOption(label="Polski", value="pl", emoji="🇵🇱")]
        super().__init__(placeholder="Selecione o Idioma...", options=opts)
    async def callback(self, i):
        t = TEXTOS[self.values[0]]; v = ModeSelect(self.values[0])
        v.children[0].label = t['btn_craft']; v.children[1].label = t['btn_alch']; v.children[2].label = t['btn_skill']
        v.children[3].label = t['btn_rashid']; v.children[4].label = t['btn_wiki']; v.children[5].label = t['btn_tools']
        await i.response.send_message(t['select_lang'], view=v, ephemeral=True)

class PersistentControlView(ui.View):
    def __init__(self): super().__init__(timeout=None)
    @ui.button(label="🌐 Iniciar / Start", style=discord.ButtonStyle.blurple, custom_id="btn_start")
    async def start(self, i, b): 
        v = ui.View(timeout=None); v.add_item(LanguageSelect())
        await i.response.send_message("🇧🇷 🇺🇸 🇵🇱", view=v, ephemeral=True)

# --- VIEWS AUXILIARES ---
class ToolsSelect(ui.View):
    def __init__(self, lang): 
        super().__init__(timeout=None); self.lang = lang; t = TEXTOS[lang]
        self.children[0].label = t['btn_mining']; self.children[1].label = t['btn_party']; self.children[2].label = t['btn_ss']
    @ui.button(label="Mining", style=discord.ButtonStyle.secondary)
    async def mining(self, i, b):
        v = ui.View(timeout=None); v.add_item(MiningPickSelect(self.lang))
        await i
