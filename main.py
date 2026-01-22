import discord
import requests
import pytz
import time
import os
import math
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread
from discord import app_commands, ui
from calculadora import *
from itens import *
from idiomas import TEXTOS

TOKEN = os.environ.get('DISCORD_TOKEN') 
FUSO_BRASILIA = pytz.timezone('America/Sao_Paulo')

app = Flask('')
@app.route('/')
def home(): return "Bot Bellão V25 Fix Wiki Online"
def run_web_server(): app.run(host='0.0.0.0', port=8080)

# --- MEMÓRIA DOS ITENS ---
ITEM_ID_MAP = {}

def indexar_itens_miracle():
    """Busca agressiva de IDs navegando pelas categorias do Miracle."""
    global ITEM_ID_MAP
    try:
        # Categorias comuns do Miracle para garantir que não pule nada
        categorias = ["helmets", "armors", "legs", "boots", "shields", "swords", "axes", "clubs", "distance", "wands", "rods", "amulets", "rings", "runes", "tools"]
        for cat in categorias:
            url = f"{MIRACLE_ITEMS_URL}&category={cat}"
            resp = requests.get(url, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            links = soup.find_all('a', href=re.compile(r'id='))
            for link in links:
                m = re.search(r'id=(\d+)', link['href'])
                if m:
                    nome = link.text.strip().lower()
                    ITEM_ID_MAP[nome] = m.group(1)
        print(f"Indexação concluída: {len(ITEM_ID_MAP)} itens.")
    except Exception as e:
        print(f"Erro indexação: {e}")

# --- BOT SETUP ---
class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.tree = app_commands.CommandTree(self)
    async def setup_hook(self):
        self.add_view(PersistentControlView())
        Thread(target=indexar_itens_miracle, daemon=True).start()
        await self.tree.sync()

bot = MyBot()

# --- FIX SCRAPER WIKI BR ---
def buscar_wiki_monster(nome):
    try:
        # Formata para TibiaWiki.com.br (ex: Dragon_Lord)
        url = f"{WIKI_MONSTER_URL}{nome.replace(' ', '_').title()}"
        resp = requests.get(url, timeout=5)
        if resp.status_code != 200: return None
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Procura por "Pontos de vida" e "Experiência" no texto das células
        hp, exp = "?", "?"
        cells = soup.find_all('td')
        for i, cell in enumerate(cells):
            txt = cell.text.lower()
            if "pontos de vida" in txt:
                hp = cells[i+1].text.strip()
            if "experiência" in txt:
                exp = cells[i+1].text.strip()
                
        return {"hp": hp, "exp": exp, "url": url}
    except: return None

def buscar_vendas_miracle(item_name):
    item_name = item_name.lower()
    item_id = ITEM_ID_MAP.get(item_name)
    if not item_id: return None
    
    try:
        url = f"{MIRACLE_ITEM_ID_URL}{item_id}"
        resp = requests.get(url, timeout=5)
        soup = BeautifulSoup(resp.text, 'html.parser')
        res = {"buy": [], "sell": [], "url": url}
        
        # Procura tabelas após os headers Buy From / Sell To
        for h2 in soup.find_all('h2'):
            txt = h2.text.lower()
            if "buy from" in txt:
                table = h2.find_next('table')
                for row in table.find_all('tr')[1:]:
                    c = row.find_all('td')
                    if len(c) >= 3: res['buy'].append(f"👤 {c[0].text} ({c[1].text}) - {c[2].text}")
            elif "sell to" in txt:
                table = h2.find_next('table')
                for row in table.find_all('tr')[1:]:
                    c = row.find_all('td')
                    if len(c) >= 3: res['sell'].append(f"💰 {c[0].text} ({c[1].text}) - {c[2].text}")
        return res
    except: return None

# ==========================================
# 🔄 INTERFACES
# ==========================================

class WikiModal(ui.Modal):
    def __init__(self, tipo, lang):
        self.lang = lang; self.tipo = tipo; t = TEXTOS[lang]
        super().__init__(title=t['btn_wiki'])
        self.add_item(ui.TextInput(label=t['wiki_label'], placeholder=t['wiki_ph'], custom_id="q"))

    async def on_submit(self, interaction: discord.Interaction):
        query = self.children[0].value.strip()
        t = TEXTOS[self.lang]
        await interaction.response.defer(ephemeral=True)
        
        if self.tipo == "monster":
            data = buscar_wiki_monster(query)
            if not data: await interaction.followup.send(t['wiki_error'].format(query))
            else:
                emb = discord.Embed(title=f"🐲 {query.title()}", url=data['url'], color=discord.Color.red())
                emb.add_field(name="❤️ HP", value=data['hp'], inline=True)
                emb.add_field(name="🔮 EXP", value=data['exp'], inline=True)
                await interaction.followup.send(embed=emb, view=ResultView())
        else:
            data = buscar_vendas_miracle(query)
            if not data: await interaction.followup.send(t['wiki_error'].format(query))
            else:
                emb = discord.Embed(title=f"🛡️ {query.title()} (Miracle)", url=data['url'], color=discord.Color.blue())
                if data['buy']: emb.add_field(name=t['wiki_buy_title'], value="\n".join(data['buy'][:10]), inline=False)
                if data['sell']: emb.add_field(name=t['wiki_sell_title'], value="\n".join(data['sell'][:10]), inline=False)
                await interaction.followup.send(embed=emb, view=ResultView())

class LanguageSelect(ui.Select):
    def __init__(self):
        opts = [
            discord.SelectOption(label="Português", value="pt", emoji="🇧🇷"),
            discord.SelectOption(label="English", value="en", emoji="🇺🇸"),
            discord.SelectOption(label="Polski", value="pl", emoji="🇵🇱") # POLONIA DE VOLTA!
        ]
        super().__init__(placeholder="Selecione o Idioma...", options=opts)
    async def callback(self, i):
        t = TEXTOS[self.values[0]]; v = ModeSelect(self.values[0])
        await i.response.send_message(t['select_lang'], view=v, ephemeral=True)

class ModeSelect(ui.View):
    def __init__(self, lang): super().__init__(timeout=None); self.lang = lang
    @ui.button(label="🔨 Crafting", style=discord.ButtonStyle.primary, row=0)
    async def craft(self, i, b):
        v = ui.View(timeout=None); v.add_item(CategorySelect(self.lang))
        await i.response.send_message("Categoria:", view=v, ephemeral=True)
    @ui.button(label="🧪 Alchemy", style=discord.ButtonStyle.success, row=0)
    async def alchemy(self, i, b): await i.response.send_message("Alchemy:", view=AlchemySelect(self.lang), ephemeral=True)
    @ui.button(label="⚔️ Skills", style=discord.ButtonStyle.danger, row=0)
    async def skills(self, i, b):
        v = ui.View(timeout=None); v.add_item(VocationSelect(self.lang))
        await i.response.send_message("Vocation:", view=v, ephemeral=True)
    @ui.button(label="🕌 Rashid", style=discord.ButtonStyle.secondary, row=0)
    async def rashid(self, i, b):
        agora = datetime.now(FUSO_BRASILIA)
        if agora.hour < 5: agora -= timedelta(days=1)
        info = RASHID_SCHEDULE[agora.weekday()]
        desc = f"📍 {info['desc']}"
        if info['url']: desc += f"\n\n**[Mapa]({info['url']})**"
        await i.response.send_message(embed=discord.Embed(title=f"Rashid: {info['city']}", description=desc), ephemeral=True)
    @ui.button(label="📖 Wiki", style=discord.ButtonStyle.secondary, row=1)
    async def wiki(self, i, b): 
        v = ui.View(timeout=None); v.add_item(WikiCategorySelect(self.lang))
        await i.response.send_message("Wiki:", view=v, ephemeral=True)
    @ui.button(label="🛠️ Extras", style=discord.ButtonStyle.primary, row=1)
    async def tools(self, i, b): await i.response.send_message("Extras:", view=ToolsSelect(self.lang), ephemeral=True)
    @ui.button(label="💰 Donate", style=discord.ButtonStyle.secondary, row=1)
    async def donate(self, i, b):
        emb = discord.Embed(title="Donate", description="Pix: `seu_email` / TC: **Obellao**")
        await i.response.send_message(embed=emb, ephemeral=True)

class WikiCategorySelect(ui.Select):
    def __init__(self, lang):
        self.lang = lang; t = TEXTOS[lang]
        opts = [discord.SelectOption(label=t['wiki_monster'], value="monster"), discord.SelectOption(label=t['wiki_item'], value="item")]
        super().__init__(placeholder="Wiki...", options=opts)
    async def callback(self, i): await i.response.send_modal(WikiModal(self.values[0], self.lang))

# --- VIEWS AUXILIARES ---
class ResultView(ui.View):
    def __init__(self): super().__init__(timeout=None)
    @ui.button(label="🔄 Restart", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def restart(self, i, b):
        v = ui.View(timeout=None); v.add_item(LanguageSelect())
        await i.response.send_message("Menu:", view=v, ephemeral=True)

class ToolsSelect(ui.View):
    def __init__(self, lang): super().__init__(timeout=None); self.lang = lang
    @ui.button(label="⛏️ Mining", style=discord.ButtonStyle.secondary)
    async def mining(self, i, b):
        v = ui.View(timeout=None); v.add_item(MiningPickSelect(self.lang))
        await i.response.send_message("Pick:", view=v, ephemeral=True)
    @ui.button(label="🤝 Party Share", style=discord.ButtonStyle.primary)
    async def party(self, i, b): await i.response.send_modal(PartyShareModal(self.lang))

class MiningPickSelect(ui.Select):
    def __init__(self, lang):
        self.lang = lang
        opts = [discord.SelectOption(label=p, value=p) for p in MINING_PICKS.keys()]
        super().__init__(placeholder="Pick...", options=opts)
    async def callback(self, i): await i.response.send_modal(MiningModal(self.values[0], self.lang))

class MiningModal(ui.Modal):
    def __init__(self, pick, lang):
        super().__init__(title="Mining"); self.pick = pick; self.lang = lang
        self.add_item(ui.TextInput(label="Skill"))
    async def on_submit(self, i):
        res = calcular_mining(int(self.children[0].value), self.pick)
        emb = discord.Embed(title="Mining Result", color=discord.Color.greyple())
        emb.add_field(name="💥 Break", value=f"{res['break_chance']}%")
        emb.add_field(name="💎 Minerals", value=f"{res['minerals_chance']}%")
        await i.response.send_message(embed=emb, ephemeral=True, view=ResultView())

class PartyShareModal(ui.Modal):
    def __init__(self, lang):
        super().__init__(title="Party Share"); self.lang = lang
        self.add_item(ui.TextInput(label="Seu Level"))
    async def on_submit(self, i):
        mi, ma = calcular_party_range(int(self.children[0].value))
        await i.response.send_message(f"Range: {mi} - {ma}", ephemeral=True, view=ResultView())

class AlchemySelect(ui.View):
    def __init__(self, lang): super().__init__(timeout=None); self.lang = lang
    @ui.button(label="💰 Gold", style=discord.ButtonStyle.primary)
    async def gold(self, i, b): await i.response.send_modal(AlchemyGoldModal(self.lang))

class AlchemyGoldModal(ui.Modal):
    def __init__(self, lang):
        super().__init__(title="Gold Converter"); self.lang = lang
        self.add_item(ui.TextInput(label="Skill"))
        self.add_item(ui.TextInput(label="Total Gold"))
    async def on_submit(self, i):
        raw = self.children[1].value.lower().replace('k', '000').replace('m', '000000')
        res = calcular_alchemy_gold(int(self.children[0].value), int(raw))
        await i.response.send_message(f"Precisa de {res['converters']}x Converters", ephemeral=True, view=ResultView())

class CategorySelect(ui.Select):
    def __init__(self, lang):
        self.lang = lang; cats = ESTRUTURA_MENU['crafting']
        opts = [discord.SelectOption(label=k, value=k) for k in cats.keys()]
        super().__init__(placeholder="Categoria...", options=opts)
    async def callback(self, i):
        v = ui.View(timeout=None); v.add_item(ItemSelect(self.values[0], self.lang))
        await i.response.edit_message(view=v)

class ItemSelect(ui.Select):
    def __init__(self, c, l):
        self.l=l; itens = sorted(ESTRUTURA_MENU['crafting'][c])
        opts = [discord.SelectOption(label=it, value=it) for it in itens]
        super().__init__(placeholder="Item...", options=opts)
    async def callback(self, i): await i.response.send_modal(DynamicCraftingModal(self.values[0], RECEITAS[self.values[0]], self.l))

class DynamicCraftingModal(ui.Modal):
    def __init__(self, n, r, l):
        super().__init__(title=n); self.r=r; self.l=l; self.n=n
        self.add_item(ui.TextInput(label="Skill"))
        self.add_item(ui.TextInput(label="Quantidade", default="1"))
    async def on_submit(self, i):
        res = calcular_crafting_detalhado(int(self.children[0].value), self.r['multiplicador'], {}, int(self.children[1].value))
        await i.response.send_message(f"Sucesso: {res['chance_sucesso']}%", ephemeral=True, view=ResultView())

class VocationSelect(ui.Select):
    def __init__(self, lang):
        self.lang = lang
        opts = [discord.SelectOption(label="Knight", value="knight"), discord.SelectOption(label="Paladin", value="paladin")]
        super().__init__(placeholder="Vocação...", options=opts)
    async def callback(self, i): await i.response.send_message("Escolha Skill...", ephemeral=True)

class PersistentControlView(ui.View):
    def __init__(self): super().__init__(timeout=None)
    @ui.button(label="🌐 Iniciar / Start", style=discord.ButtonStyle.blurple, custom_id="btn_start")
    async def start(self, i, b):
        v = ui.View(timeout=None); v.add_item(LanguageSelect())
        await i.response.send_message("🇧🇷 🇺🇸 🇵🇱", view=v, ephemeral=True)

@bot.tree.command(name="setup_calculadora")
async def setup(i): await i.response.send_message(embed=discord.Embed(title="⚒️ Miracle Tools", color=discord.Color.gold()), view=PersistentControlView())

if __name__ == "__main__":
    if TOKEN:
        Thread(target=run_web_server, daemon=True).start()
        bot.run(TOKEN)
