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

# Headers reforçados para evitar bloqueio do site
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,pt;q=0.8',
    'Referer': 'https://miracle74.com/'
}

app = Flask('')
@app.route('/')
def home(): return "Bot Bellão V30 Stable Online"
def run_web_server(): app.run(host='0.0.0.0', port=8080)

# --- MEMÓRIA DOS ITENS ---
ITEM_ID_MAP = {}

def indexar_itens_miracle():
    """Tenta indexar itens. Se falhar, imprime erro no log do Render."""
    global ITEM_ID_MAP
    print(">>> INICIANDO INDEXAÇÃO DE ITENS MIRACLE...")
    try:
        cats = ["helmets", "armors", "legs", "boots", "shields", "swords", "axes", "clubs", "distance", "wands", "rods", "amulets", "rings", "runes", "tools"]
        total = 0
        for cat in cats:
            url = f"{MIRACLE_ITEMS_URL}&category={cat}"
            try:
                # verify=False ajuda caso o SSL do site seja antigo
                resp = requests.get(url, headers=HEADERS, timeout=15, verify=False)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    # Busca links que tenham id=NUMERO
                    for link in soup.find_all('a', href=True):
                        m = re.search(r'id=(\d+)', link['href'])
                        if m:
                            nome_limpo = link.text.strip().lower()
                            if nome_limpo:
                                ITEM_ID_MAP[nome_limpo] = m.group(1)
                                total += 1
            except Exception as e_cat:
                print(f"Erro ao ler categoria {cat}: {e_cat}")
        
        # Adiciona manualmente alguns itens essenciais caso a indexação falhe
        if "fire sword" not in ITEM_ID_MAP: ITEM_ID_MAP["fire sword"] = "2392"
        if "dragon shield" not in ITEM_ID_MAP: ITEM_ID_MAP["dragon shield"] = "2516"
        
        print(f">>> INDEXAÇÃO CONCLUÍDA: {total} itens encontrados.")
    except Exception as e: 
        print(f"Erro fatal indexação: {e}")

class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.tree = app_commands.CommandTree(self)
    async def setup_hook(self):
        self.add_view(PersistentControlView())
        Thread(target=indexar_itens_miracle, daemon=True).start()
        await self.tree.sync()

bot = MyBot()

# --- SCRAPERS ---
def buscar_wiki_monster(nome):
    try:
        url = f"{WIKI_MONSTER_URL}{nome.replace(' ', '_').title()}"
        resp = requests.get(url, headers=HEADERS, timeout=5)
        if resp.status_code != 200: return None
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text()
        
        info = {"hp": "?", "exp": "?", "loot": {}, "url": url}
        
        # 1. Regex Robusta para HP e XP
        # Busca "1000 HP" ou "1,000 HP" ou "1.000 HP"
        m_hp = re.search(r'([\d\.,]+)\s*HP', text)
        if m_hp: info['hp'] = m_hp.group(1)
        
        m_exp = re.search(r'([\d\.,]+)\s*XP', text)
        if m_exp: info['exp'] = m_exp.group(1)

        # 2. Loot Parser V2 (Mais inteligente)
        # Procura as seções exatas
        loot_sections = [
            ("Muito Raro:", ["Durante", "História", "Notas"]),
            ("Raro:", ["Muito Raro:", "Durante"]),
            ("Semi-Raro:", ["Raro:", "Muito Raro:"]),
            ("Incomum:", ["Semi-Raro:", "Raro:"]),
            ("Comum:", ["Incomum:", "Semi-Raro:"])
        ]
        
        # Faz a busca inversa (do mais raro pro comum) para garantir limites
        full_text = soup.get_text(" ", strip=True) # Remove quebras de linha estranhas
        
        # Procura a string "Loot:" para começar a busca dali pra frente
        start_loot = full_text.find("Loot:")
        if start_loot != -1:
            loot_text = full_text[start_loot:]
            
            # Extrai cada categoria
            cats_to_find = ["Comum:", "Incomum:", "Semi-Raro:", "Raro:", "Muito Raro:"]
            for i, cat in enumerate(cats_to_find):
                if cat in loot_text:
                    # Onde começa esta categoria
                    idx_start = loot_text.find(cat) + len(cat)
                    
                    # Onde termina? No inicio da proxima categoria existente
                    idx_end = len(loot_text)
                    for next_cat in cats_to_find[i+1:] + ["Durante", "Eventos"]:
                        tmp_idx = loot_text.find(next_cat, idx_start)
                        if tmp_idx != -1 and tmp_idx < idx_end:
                            idx_end = tmp_idx
                    
                    items = loot_text[idx_start:idx_end].strip().strip(".,")
                    if items: info['loot'][cat.replace(":", "")] = items

        return info
    except Exception as e:
        print(f"Erro Monster: {e}")
        return None

def buscar_vendas_miracle(query):
    query = query.lower().strip()
    item_id = ITEM_ID_MAP.get(query)
    
    # Se não achou pelo nome, verifica se o usuário digitou o ID direto (ex: "2392")
    if not item_id and query.isdigit():
        item_id = query
        
    if not item_id: return None
    
    try:
        url = f"{MIRACLE_ITEM_ID_URL}{item_id}"
        # verify=False para evitar erro de certificado SSL
        resp = requests.get(url, headers=HEADERS, timeout=8, verify=False) 
        soup = BeautifulSoup(resp.text, 'html.parser')
        res = {"buy": [], "sell": [], "url": url, "name": query.title()}
        
        # Tenta pegar o nome real da pagina
        page_title = soup.find('div', class_='BoxContent')
        if page_title: res['name'] = page_title.get_text().split('\n')[0].strip()

        # Busca Tabelas
        tables = soup.find_all('table')
        for table in tables:
            # Verifica cabeçalho da tabela
            header = table.find_previous('h2') or table.find_previous('div', class_='TableTitle')
            if not header: continue
            header_txt = header.get_text().lower()
            
            if "buy from" in header_txt:
                for row in table.find_all('tr')[1:]:
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        res['buy'].append(f"👤 {cols[0].text.strip()} ({cols[1].text.strip()}) 💰 {cols[2].text.strip()}")
            
            elif "sell to" in header_txt:
                for row in table.find_all('tr')[1:]:
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        res['sell'].append(f"🛒 {cols[0].text.strip()} ({cols[1].text.strip()}) 💰 {cols[2].text.strip()}")
                        
        return res
    except Exception as e:
        print(f"Erro Miracle Item: {e}")
        return None

# ==========================================
# 🔄 INTERFACES
# ==========================================

class WikiModal(ui.Modal):
    def __init__(self, tipo, lang):
        self.lang = lang; self.tipo = tipo; t = TEXTOS[lang]
        super().__init__(title=t['btn_wiki'])
        self.add_item(ui.TextInput(label=t['wiki_label'], placeholder=t['wiki_ph']))

    async def on_submit(self, interaction: discord.Interaction):
        q = self.children[0].value.strip(); t = TEXTOS[self.lang]
        
        # Mensagem Efêmera (Só você vê e some)
        await interaction.response.defer(ephemeral=True)
        
        if self.tipo == "monster":
            data = buscar_wiki_monster(q)
            if not data: 
                await interaction.followup.send(t['wiki_error'].format(q), ephemeral=True)
            else:
                emb = discord.Embed(title=f"🐲 {q.title()}", url=data['url'], color=discord.Color.red())
                emb.add_field(name="❤️ HP", value=f"**{data['hp']}**", inline=True)
                emb.add_field(name="🔮 XP", value=f"**{data['exp']}**", inline=True)
                
                if not data['loot']:
                    emb.add_field(name="📦 Loot", value="Nenhum ou erro ao ler.", inline=False)
                else:
                    for cat, items in data['loot'].items():
                        emb.add_field(name=f"📦 {cat}", value=items[:1000], inline=False)
                
                await interaction.followup.send(embed=emb, view=WikiSelect(self.lang), ephemeral=True)
        else:
            data = buscar_vendas_miracle(q)
            if not data: 
                await interaction.followup.send(t['wiki_error'].format(q), ephemeral=True)
            else:
                emb = discord.Embed(title=f"🛡️ {data.get('name', q.title())}", url=data['url'], color=discord.Color.blue())
                
                if data['buy']: 
                    chunk = "\n".join(data['buy'][:10])
                    emb.add_field(name=t['wiki_buy_title'], value=chunk, inline=False)
                
                if data['sell']: 
                    chunk = "\n".join(data['sell'][:10])
                    emb.add_field(name=t['wiki_sell_title'], value=chunk, inline=False)
                
                if not data['buy'] and not data['sell']:
                    emb.description = "⚠️ Item não encontrado em NPCs (ou erro de leitura do site)."
                
                await interaction.followup.send(embed=emb, view=WikiSelect(self.lang), ephemeral=True)

class WikiSelect(ui.View):
    def __init__(self, lang): 
        super().__init__(timeout=None)
        self.lang = lang
        t = TEXTOS[lang]
        self.children[0].label = t['wiki_monster']
        self.children[1].label = t['wiki_item']
        self.children[2].label = "Menu"

    @ui.button(label="Monster", style=discord.ButtonStyle.danger)
    async def monster(self, i, b): await i.response.send_modal(WikiModal("monster", self.lang))
    @ui.button(label="Item", style=discord.ButtonStyle.primary)
    async def item(self, i, b): await i.response.send_modal(WikiModal("item", self.lang))
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
    async def donate(self, i, b): await i.response.send_message("Pix: `seu_email` / TC: **Obellao**", ephemeral=True)

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
        super().__init__(timeout=None)
        self.lang = lang
        t = TEXTOS[lang]
        self.children[0].label = t['btn_mining']
        self.children[1].label = t['btn_party']
        self.children[2].label = t['btn_ss']

    @ui.button(label="Mining", style=discord.ButtonStyle.secondary)
    async def mining(self, i, b):
        v = ui.View(timeout=None); v.add_item(MiningPickSelect(self.lang))
        await i.response.send_message(TEXTOS[self.lang]['mining_pick_ph'], view=v, ephemeral=True)
    @ui.button(label="Party", style=discord.ButtonStyle.primary)
    async def party(self, i, b): await i.response.send_modal(PartyShareModal(self.lang))
    @ui.button(label="SS", style=discord.ButtonStyle.danger)
    async def ss(self, i, b):
        agora = datetime.now(FUSO_BRASILIA)
        target = agora.replace(hour=5, minute=0, second=0, microsecond=0)
        if agora.hour >= 5: target += timedelta(days=1)
        diff = target - agora
        tempo = f"{int(diff.total_seconds()//3600)}h {int((diff.total_seconds()%3600)//60)}m"
        await i.response.send_message(TEXTOS[self.lang]['ss_msg'].format(tempo), ephemeral=True)

class MiningPickSelect(ui.Select):
    def __init__(self, lang):
        self.lang = lang
        opts = [discord.SelectOption(label=p, value=p) for p in MINING_PICKS.keys()]
        super().__init__(placeholder="Pick...", options=opts)
    async def callback(self, i): await i.response.send_modal(MiningModal(self.values[0], self.lang))

class MiningModal(ui.Modal):
    def __init__(self, pick, lang):
        self.pick = pick; self.lang = lang; t = TEXTOS[lang]
        super().__init__(title=t['mining_title'])
        self.add_item(ui.TextInput(label=t['mining_skill_label']))
    async def on_submit(self, i):
        res = calcular_mining(int(self.children[0].value), self.pick)
        t = TEXTOS[self.lang]
        emb = discord.Embed(title=t['mining_title'], color=discord.Color.greyple())
        emb.add_field(name=t['mining_res_break'], value=f"{res['break_chance']}%")
        emb.add_field(name=t['mining_res_min'], value=f"{res['minerals_chance']}%")
        emb.add_field(name=t['mining_res_frag'], value=f"{res['fragments_chance']}%")
        await i.response.send_message(embed=emb, ephemeral=True)

class PartyShareModal(ui.Modal):
    def __init__(self, lang):
        self.lang = lang; t = TEXTOS[lang]
        super().__init__(title=t['party_title'])
        self.add_item(ui.TextInput(label=t['party_label']))
    async def on_submit(self, i):
        mi, ma = calcular_party_range(int(self.children[0].value))
        t = TEXTOS[self.lang]
        await i.response.send_message(t['party_res'].format(self.children[0].value) + f" **{mi} - {ma}**", ephemeral=True)

class AlchemySelect(ui.View):
    def __init__(self, lang): super().__init__(timeout=None); self.lang = lang
    @ui.button(label="💰 Gold Converter", style=discord.ButtonStyle.primary)
    async def gold(self, i, b): await i.response.send_modal(AlchemyGoldModal(self.lang))

class AlchemyGoldModal(ui.Modal):
    def __init__(self, lang):
        self.lang = lang; t = TEXTOS[lang]
        super().__init__(title=t['alch_gold'])
        self.add_item(ui.TextInput(label=t['alch_skill_label']))
        self.add_item(ui.TextInput(label=t['alch_gold_label']))
    async def on_submit(self, i):
        raw = self.children[1].value.lower().replace('k', '000')
        res = calcular_alchemy_gold(int(self.children[0].value), int(raw))
        t = TEXTOS[self.lang]
        await i.response.send_message(f"{t['alch_needs']} {res['converters']}x {t['alch_conv_name']}", ephemeral=True)

class CategorySelect(ui.Select):
    def __init__(self, lang):
        self.lang = lang; cats = ESTRUTURA_MENU['crafting']
        t = TEXTOS[lang]
        opts = [discord.SelectOption(label=t['cats'].get(k, k), value=k) for k in cats.keys()]
        super().__init__(placeholder=t['select_cat'], options=opts)
    async def callback(self, i): await i.response.edit_message(content="Item...", view=ui.View().add_item(ItemSelect(self.values[0], self.lang)))

class ItemSelect(ui.Select):
    def __init__(self, c, l):
        self.l=l; itens = sorted(ESTRUTURA_MENU['crafting'][c])
        opts = [discord.SelectOption(label=it, value=it) for it in itens]
        super().__init__(placeholder="Item...", options=opts)
    async def callback(self, i): await i.response.send_modal(DynamicCraftingModal(self.values[0], RECEITAS[self.values[0]], self.l))

class DynamicCraftingModal(ui.Modal):
    def __init__(self, n, r, l):
        t = TEXTOS[l]; super().__init__(title=n); self.r=r; self.l=l; self.n=n
        self.add_item(ui.TextInput(label=t['label_skill']))
        self.add_item(ui.TextInput(label=t['label_qtd'], default="1"))
    async def on_submit(self, i):
        res = calcular_crafting_detalhado(int(self.children[0].value), self.r['multiplicador'], {}, int(self.children[1].value))
        await i.response.send_message(f"Sucesso: {res['chance_sucesso']}%", ephemeral=True)

class VocationSelect(ui.Select):
    def __init__(self, lang):
        self.lang = lang
        opts = [discord.SelectOption(label="Knight", value="knight"), discord.SelectOption(label="Paladin", value="paladin")]
        super().__init__(placeholder="Vocação...", options=opts)
    async def callback(self, i): await i.response.send_message("Em construção...", ephemeral=True)

@bot.tree.command(name="setup_calculadora")
async def setup(i): await i.response.send_message(embed=discord.Embed(title="⚒️ Miracle Tools", color=discord.Color.gold()), view=PersistentControlView())

if __name__ == "__main__":
    if TOKEN:
        Thread(target=run_web_server, daemon=True).start()
        bot.run(TOKEN)
