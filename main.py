import discord
import os
import requests
import re
import math
import pytz # <--- O ERRO ESTAVA AQUI (FALTAVA ESSA LINHA)
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
HEADERS = {'User-Agent': 'Mozilla/5.0'}

app = Flask('')
@app.route('/')
def home(): return "Bot Bellão V39 (Fixed Imports) Online"
def run_web_server(): app.run(host='0.0.0.0', port=8080)

class MyBot(discord.Client):
    def __init__(self): super().__init__(intents=discord.Intents.all()); self.tree = app_commands.CommandTree(self)
    async def setup_hook(self): self.add_view(PersistentControlView()); await self.tree.sync()

bot = MyBot()

# --- WIKI (REGEX/V37) ---
def buscar_wiki_monster(nome):
    try:
        url = f"{WIKI_MONSTER_URL}{nome.replace(' ', '_').title()}"
        resp = requests.get(url, headers=HEADERS, timeout=5)
        if resp.status_code != 200: return None
        text = BeautifulSoup(resp.text, 'html.parser').get_text()
        info = {"hp": "?", "exp": "?", "loot": {}, "url": url}
        m_hp = re.search(r'([\d\.,]+)\s*HP', text); 
        if m_hp: info['hp'] = m_hp.group(1)
        m_exp = re.search(r'([\d\.,]+)\s*XP', text); 
        if m_exp: info['exp'] = m_exp.group(1)
        start = text.find("Loot:")
        if start != -1:
            lt = text[start:]
            cats = ["Comum:", "Incomum:", "Semi-Raro:", "Raro:", "Muito Raro:"]
            for i, c in enumerate(cats):
                if c in lt:
                    s = lt.find(c) + len(c)
                    ends = [lt.find(n, s) for n in cats[i+1:] + ["Durante", "Eventos"] if lt.find(n, s) != -1]
                    e = min(ends) if ends else len(lt)
                    info['loot'][c.replace(":","")] = lt[s:e].strip().strip(".,")[:900]
        return info
    except: return None

# --- CRAFTING (V22 - COM INPUT DE PREÇO) ---
class DynamicCraftingModal(ui.Modal):
    def __init__(self, item_name, receita_data, lang):
        self.lang = lang; t = TEXTOS[lang]
        super().__init__(title=t['modal_title'].format(item_name))
        self.item_name = item_name; self.receita_data = receita_data
        
        self.add_item(ui.TextInput(label=t['label_skill'], placeholder="Ex: 50"))
        self.add_item(ui.TextInput(label=t['label_qtd'], placeholder="Ex: 10"))
        
        # Inputs de preço para os 3 primeiros ingredientes (FEATURE V22 PRESERVADA)
        self.materiais_na_janela = list(receita_data['ingredientes'].items())[:3]
        for m, q in self.materiais_na_janela:
            self.add_item(ui.TextInput(label=t['label_price'].format(m, q), placeholder="Ex: 500", required=False))

    async def on_submit(self, interaction: discord.Interaction):
        t = TEXTOS[self.lang]
        try:
            skill = int(self.children[0].value)
            qtd = int(self.children[1].value)
            
            ings = {}
            for i, (m, q) in enumerate(self.materiais_na_janela):
                p_txt = self.children[i+2].value
                price = float(p_txt.replace('.','').replace(',','.')) if p_txt else 0
                ings[m] = {"qtd": q, "preco": price, "consome_na_falha": m not in self.receita_data.get('nao_perde', [])}
            
            res = calcular_crafting_detalhado(skill, self.receita_data['multiplicador'], ings, qtd)
            
            embed = discord.Embed(title=t['result_title'].format(qtd, self.item_name), color=discord.Color.blue())
            embed.add_field(name=t['chance'], value=f"{res['chance_sucesso']}%", inline=True)
            if res['custo_total'] > 0:
                embed.add_field(name=t['cost'], value=f"{res['custo_total']:,.0f} gp", inline=True)
            
            msg_list = ""
            for m, q in res['materiais_necessarios'].items():
                msg_list += f"• **{m}**: {q:.1f}\n"
            embed.add_field(name=t['list'], value=msg_list, inline=False)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e: 
            await interaction.response.send_message(f"❌ Erro: {e}", ephemeral=True)

# --- SKILLS (V22 - COM PREÇO E DETALHES) ---
class SingleSkillModal(ui.Modal):
    def __init__(self, voc, tipo, nome, spd, chg, lang):
        self.lang=lang; self.voc=voc; self.tipo=tipo; self.spd=spd; self.chg=chg; self.nome=nome
        super().__init__(title=f"{voc} - {tipo}")
        self.add_item(ui.TextInput(label="Skill Atual", placeholder="Ex: 10"))
        self.add_item(ui.TextInput(label="% Atual", placeholder="Ex: 50"))
        self.add_item(ui.TextInput(label="Skill Desejado", placeholder="Ex: 80"))
        self.add_item(ui.TextInput(label="Preço da Arma (Opcional)", required=False))

    async def on_submit(self, i):
        try:
            c = int(self.children[0].value); p = float(self.children[1].value.replace(',','.'))
            t = int(self.children[2].value); pr_txt = self.children[3].value
            price = int(pr_txt.replace('.','').replace('k','000')) if pr_txt else 0
            
            res = calcular_tempo_skill(self.voc, self.tipo, c, p, t, self.spd)
            qtd = math.ceil(res['hits']/self.chg) if self.chg < 999999 else 1
            cost = qtd * price
            
            emb = discord.Embed(title=f"⚔️ {self.voc} - {self.tipo}", color=discord.Color.blue())
            emb.add_field(name="Tempo", value=f"{res['dias']}d {res['horas']}h {res['minutos']}m", inline=False)
            desc_rec = f"{qtd}x {self.nome}"
            if cost > 0: desc_rec += f"\n💰 Custo: {cost:,} gp"
            emb.add_field(name="Recursos", value=desc_rec, inline=False)
            
            await i.response.send_message(embed=emb, ephemeral=True)
        except: await i.response.send_message("❌ Erro nos números.", ephemeral=True)

# --- OUTROS MENUS ---
class WikiModal(ui.Modal):
    def __init__(self, lang): super().__init__(title="Wiki"); self.lang=lang; t=TEXTOS[lang]; self.add_item(ui.TextInput(label=t['wiki_label']))
    async def on_submit(self, i):
        data = buscar_wiki_monster(self.children[0].value)
        if not data: await i.response.send_message("❌ Não encontrado.", ephemeral=True)
        else:
            emb = discord.Embed(title=f"🐲 {self.children[0].value}", url=data['url'], color=discord.Color.red())
            emb.add_field(name="HP/XP", value=f"{data['hp']} / {data['exp']}", inline=False)
            for c,v in data['loot'].items(): emb.add_field(name=c, value=v, inline=False)
            await i.response.send_message(embed=emb, ephemeral=True)

class WikiSelect(ui.View):
    def __init__(self, lang): super().__init__(timeout=None); self.lang=lang
    @ui.button(label="Pesquisar Monstro", style=discord.ButtonStyle.danger)
    async def monster(self, i, b): await i.response.send_modal(WikiModal(self.lang))

class ModeSelect(ui.View):
    def __init__(self, lang): 
        super().__init__(timeout=None); self.lang=lang
        t = TEXTOS[lang]
        self.children[0].label=t['btn_craft']; self.children[1].label=t['btn_alch']
        self.children[2].label=t['btn_skill']; self.children[3].label=t['btn_rashid']
        self.children[4].label=t['btn_wiki']; self.children[5].label=t['btn_tools']
        self.children[6].label=t['btn_donate']

    @ui.button(label="Crafting", style=discord.ButtonStyle.primary, row=0)
    async def craft(self, i, b): await i.response.send_message(TEXTOS[self.lang]['select_cat'], view=CategorySelect(self.lang), ephemeral=True)
    @ui.button(label="Alchemy", style=discord.ButtonStyle.success, row=0)
    async def alchemy(self, i, b): await i.response.send_message(TEXTOS[self.lang]['alch_select'], view=AlchemySelect(self.lang), ephemeral=True)
    @ui.button(label="Skills", style=discord.ButtonStyle.danger, row=0)
    async def skills(self, i, b): await i.response.send_message("Vocação:", view=ui.View().add_item(VocationSelect(self.lang)), ephemeral=True)
    @ui.button(label="Rashid", style=discord.ButtonStyle.secondary, row=0)
    async def rashid(self, i, b):
        info = RASHID_SCHEDULE[(datetime.now(FUSO_BRASILIA) - timedelta(hours=5)).weekday()]
        t = TEXTOS[self.lang]
        emb = discord.Embed(title=t['rashid_title'].format(info['city']), description=t['rashid_desc'].format(info['desc']), color=discord.Color.dark_gold())
        if info['url']: emb.description += f"\n\n[Mapa]({info['url']})"
        await i.response.send_message(embed=emb, ephemeral=True)
    @ui.button(label="Wiki", style=discord.ButtonStyle.secondary, row=1)
    async def wiki(self, i, b): await i.response.send_message(TEXTOS[self.lang]['wiki_select'], view=WikiSelect(self.lang), ephemeral=True)
    @ui.button(label="Extras", style=discord.ButtonStyle.primary, row=1)
    async def tools(self, i, b): await i.response.send_message(TEXTOS[self.lang]['tools_select'], view=ToolsSelect(self.lang), ephemeral=True)
    @ui.button(label="Donate", style=discord.ButtonStyle.secondary, row=2, emoji="💰")
    async def donate(self, i, b): 
        t = TEXTOS[self.lang]
        emb = discord.Embed(title=t['donate_title'], description=t['donate_desc'], color=discord.Color.gold())
        emb.add_field(name="Pix", value="[Link](https://livepix.gg/obellao)", inline=True)
        emb.add_field(name="Miracle Coins", value="Parcel: **Dormir pra que / Carlin**", inline=False)
        await i.response.send_message(embed=emb, ephemeral=True)

class CategorySelect(ui.Select):
    def __init__(self, lang):
        self.lang = lang; t = TEXTOS[lang]
        opts = [discord.SelectOption(label=t['cats'].get(k, k), value=k) for k in ESTRUTURA_MENU['crafting'].keys()]
        super().__init__(placeholder=t['select_cat'], options=opts)
    async def callback(self, i): await i.response.edit_message(content="Item:", view=ui.View().add_item(ItemSelect(self.values[0], self.lang)))

class ItemSelect(ui.Select):
    def __init__(self, c, l):
        self.l=l; opts = [discord.SelectOption(label=it) for it in sorted(ESTRUTURA_MENU['crafting'][c])]
        super().__init__(placeholder="Item...", options=opts)
    async def callback(self, i):
        if self.values[0] not in RECEITAS: await i.response.send_message("❌ Receita não existe.", ephemeral=True); return
        await i.response.send_modal(DynamicCraftingModal(self.values[0], RECEITAS[self.values[0]], self.l))

class WeaponSelect(ui.Select):
    def __init__(self, voc, tipo, lang):
        self.voc=voc; self.tipo=tipo; self.lang=lang
        opts=[discord.SelectOption(label=k) for k in ARMAS_TREINO.keys() if "Shield" not in k][:25]
        super().__init__(placeholder="Arma...", options=opts)
    async def callback(self, i):
        st = ARMAS_TREINO[self.values[0]]
        await i.response.send_modal(SingleSkillModal(self.voc, self.tipo, self.values[0], st['speed'], st['charges'], self.lang))

class SkillTypeSelect(ui.Select):
    def __init__(self, voc, lang):
        self.voc=voc; self.lang=lang; opts=[discord.SelectOption(label="Melee", value="melee"), discord.SelectOption(label="Distance", value="distance")]
        super().__init__(placeholder="Tipo...", options=opts)
    async def callback(self, i): await i.response.send_message("Arma:", view=ui.View().add_item(WeaponSelect(self.voc, self.values[0], self.lang)), ephemeral=True)

class VocationSelect(ui.Select):
    def __init__(self, lang):
        self.lang=lang; opts=[discord.SelectOption(label="Knight", value="knight"), discord.SelectOption(label="Paladin", value="paladin")]
        super().__init__(placeholder="Vocação...", options=opts)
    async def callback(self, i): await i.response.send_message("Treino:", view=ui.View().add_item(SkillTypeSelect(self.values[0], self.lang)), ephemeral=True)

class AlchemySelect(ui.View):
    def __init__(self, lang): super().__init__(timeout=None); self.lang=lang
    @ui.button(label="Gold", style=discord.ButtonStyle.primary)
    async def gold(self, i, b): await i.response.send_modal(AlchemyGoldModal(self.lang))
    @ui.button(label="Enchant", style=discord.ButtonStyle.secondary)
    async def ench(self, i, b): await i.response.send_message("Cristal:", view=ui.View().add_item(AlchemyEnchantSelect(self.lang)), ephemeral=True)
    @ui.button(label="Rune", style=discord.ButtonStyle.success)
    async def rune(self, i, b): await i.response.send_message("Runa:", view=ui.View().add_item(AlchemyRuneSelect(self.lang)), ephemeral=True)

class AlchemyGoldModal(ui.Modal):
    def __init__(self, l): super().__init__(title="Gold"); self.add_item(ui.TextInput(label="Skill")); self.add_item(ui.TextInput(label="Total"))
    async def on_submit(self, i):
        res = calcular_alchemy_gold(int(self.children[0].value), int(self.children[1].value.lower().replace('k','000')))
        await i.response.send_message(f"Converters: {res['converters']}", ephemeral=True)

class AlchemyEnchantSelect(ui.Select):
    def __init__(self, l): super().__init__(placeholder="Cristal...", options=[discord.SelectOption(label=n, value=f"{n}|{d['base_chance']}") for n,d in ALCHEMY_DATA['crystals'].items()])
    async def callback(self, i): await i.response.send_modal(AlchemyEnchantModal(self.values[0], i))

class AlchemyEnchantModal(ui.Modal):
    def __init__(self, v, i): super().__init__(title="Enchant"); self.v=v.split('|'); self.add_item(ui.TextInput(label="Skill"))
    async def on_submit(self, i):
        res = calcular_alchemy_enchant(int(self.children[0].value), float(self.v[1]))
        await i.response.send_message(f"Chance: {res['chance_real']}%", ephemeral=True)

class AlchemyRuneSelect(ui.Select):
    def __init__(self, l): super().__init__(placeholder="Runa...", options=[discord.SelectOption(label=r) for r in sorted(ALCHEMY_RUNES.keys())][:25])
    async def callback(self, i): await i.response.send_modal(AlchemyRuneModal(self.values[0]))

class AlchemyRuneModal(ui.Modal):
    def __init__(self, r): super().__init__(title=r); self.r=r; self.add_item(ui.TextInput(label="Skill"))
    async def on_submit(self, i):
        res = calcular_alchemy_rune(int(self.children[0].value), self.r)
        await i.response.send_message(f"Chance: {res['chance']}%", ephemeral=True)

class ToolsSelect(ui.View):
    def __init__(self, lang): super().__init__(timeout=None); self.lang=lang; t=TEXTOS[lang]; self.children[0].label=t['btn_mining']; self.children[1].label=t['btn_party']; self.children[2].label=t['btn_ss']
    @ui.button(label="Mining", style=discord.ButtonStyle.secondary)
    async def min(self, i, b): await i.response.send_message(TEXTOS[self.lang]['mining_pick_ph'], view=ui.View().add_item(MiningSelect(self.lang)), ephemeral=True)
    @ui.button(label="Party", style=discord.ButtonStyle.primary)
    async def party(self, i, b): await i.response.send_modal(PartyModal(self.lang))
    @ui.button(label="SS", style=discord.ButtonStyle.danger)
    async def ss(self, i, b):
        diff = (datetime.now(FUSO_BRASILIA).replace(hour=5, minute=0, second=0) + timedelta(days=1)) - datetime.now(FUSO_BRASILIA)
        if diff.days > 0: diff -= timedelta(days=1)
        await i.response.send_message(TEXTOS[self.lang]['ss_msg'].format(f"{diff.seconds//3600}h {(diff.seconds%3600)//60}m"), ephemeral=True)

class MiningSelect(ui.Select):
    def __init__(self, l): super().__init__(placeholder="Picareta...", options=[discord.SelectOption(label=k) for k in MINING_PICKS.keys()])
    async def callback(self, i): await i.response.send_modal(MiningModal(self.values[0]))

class MiningModal(ui.Modal):
    def __init__(self, p): super().__init__(title="Mining"); self.p=p; self.add_item(ui.TextInput(label="Skill"))
    async def on_submit(self, i):
        res = calcular_mining(int(self.children[0].value), self.p)
        await i.response.send_message(f"Break: {res['break_chance']}% | Min: {res['minerals_chance']}%", ephemeral=True)

class PartyModal(ui.Modal):
    def __init__(self, lang): super().__init__(title="Party"); self.lang=lang; t=TEXTOS[lang]; self.add_item(ui.TextInput(label=t['party_label']))
    async def on_submit(self, i):
        r = calcular_party_range(int(self.children[0].value)); t = TEXTOS[self.lang]
        await i.response.send_message(t['party_res'].format(self.children[0].value) + f" **{r[0]} - {r[1]}**", ephemeral=True)

class LanguageSelect(ui.Select):
    def __init__(self): super().__init__(placeholder="Language...", options=[discord.SelectOption(label="PT", value="pt"), discord.SelectOption(label="EN", value="en"), discord.SelectOption(label="PL", value="pl")])
    async def callback(self, i): await i.response.send_message(TEXTOS[self.values[0]]['select_lang'], view=ModeSelect(self.values[0]), ephemeral=True)

class PersistentControlView(ui.View):
    def __init__(self): super().__init__(timeout=None)
    @ui.button(label="Start", style=discord.ButtonStyle.blurple, custom_id="btn_start")
    async def start(self, i, b): await i.response.send_message("Language:", view=ui.View(timeout=None).add_item(LanguageSelect()), ephemeral=True)

@bot.tree.command(name="setup_calculadora")
async def setup(i): await i.response.send_message(embed=discord.Embed(title="Miracle Tools", color=discord.Color.gold()), view=PersistentControlView())

if __name__ == "__main__":
    if TOKEN:
        Thread(target=run_web_server, daemon=True).start()
        bot.run(TOKEN)
