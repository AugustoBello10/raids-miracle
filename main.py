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
from calculadora import calcular_crafting_detalhado, calcular_tempo_skill
from itens import RECEITAS, ESTRUTURA_MENU, ARMAS_TREINO
from idiomas import TEXTOS

TOKEN = os.environ.get('DISCORD_TOKEN') 
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')

URL_RAIDS = "https://miracle74.com/?subtopic=raids"
FUSO_BRASILIA = pytz.timezone('America/Sao_Paulo')

# --- FLASK ---
app = Flask('')
@app.route('/')
def home(): return "Bot Bellão (Raids + Skills V5) Online"
def run_web_server(): app.run(host='0.0.0.0', port=8080)

# --- RAIDS ---
def carregar_raids():
    try:
        response = requests.get(URL_RAIDS, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        if not table: return []
        raids = []
        for row in table.find_all('tr')[1:]:
            cols = row.find_all('td')
            if len(cols) >= 3:
                nome = cols[0].text.strip()
                hrs = int(''.join(filter(str.isdigit, cols[1].text)) or 0)
                last = cols[2].text.strip()
                if last and hrs > 0:
                    try:
                        dt = datetime.strptime(last, '%Y-%m-%d %H:%M:%S')
                        dt = FUSO_BRASILIA.localize(dt) if dt.tzinfo is None else dt
                        raids.append({"nome": nome, "proxima": dt + timedelta(hours=hrs)})
                    except: continue
        return raids
    except: return []

def loop_monitoramento():
    if not WEBHOOK_URL: return
    while True:
        try:
            agora = datetime.now(FUSO_BRASILIA)
            for r in carregar_raids():
                diff = (r['proxima'] - agora).total_seconds() / 60
                if 14.5 < diff <= 15.5: 
                    requests.post(WEBHOOK_URL, json={"content": f"⚠️ **RAID:** {r['nome']} @ {r['proxima'].strftime('%H:%M')} (BRT)"})
            time.sleep(60)
        except: time.sleep(60)

# ==========================================
# ⚔️ SISTEMA DE SKILLS (FLUXO FINAL)
# ==========================================

class SkillCalcModal(ui.Modal):
    def __init__(self, vocacao, tipo_skill, arma_nome, arma_speed, lang):
        self.lang = lang
        self.vocacao = vocacao
        self.tipo_skill = tipo_skill
        self.arma_speed = arma_speed
        self.arma_nome = arma_nome
        t = TEXTOS[lang]
        
        super().__init__(title=f"{vocacao.capitalize()} - {tipo_skill.capitalize()}")
        
        self.add_item(ui.TextInput(label="Skill Atual", placeholder="Ex: 80", custom_id="curr", max_length=3))
        self.add_item(ui.TextInput(label="% Atual (Quanto já treinou?)", placeholder="Ex: 50 (50% concluído)", custom_id="pct", max_length=3))
        self.add_item(ui.TextInput(label="Skill Desejado", placeholder="Ex: 85", custom_id="target", max_length=3))

    async def on_submit(self, interaction: discord.Interaction):
        try:
            curr = int(self.children[0].value)
            pct = float(self.children[1].value.replace(',', '.'))
            target = int(self.children[2].value)
            
            if target <= curr:
                await interaction.response.send_message("❌ Target > Current.", ephemeral=True); return
            if pct < 0 or pct >= 100:
                await interaction.response.send_message("❌ % 0-99.", ephemeral=True); return

            res = calcular_tempo_skill(self.vocacao, self.tipo_skill, curr, pct, target, self.arma_speed)
            
            t = TEXTOS[self.lang]
            embed = discord.Embed(title=f"⚔️ {self.vocacao.capitalize()} - {self.tipo_skill.capitalize()}", color=discord.Color.red())
            
            tempo_txt = []
            if res['dias'] > 0: tempo_txt.append(f"**{res['dias']}**d")
            if res['horas'] > 0: tempo_txt.append(f"**{res['horas']}**h")
            if res['minutos'] > 0: tempo_txt.append(f"**{res['minutos']}**m")
            tempo_txt.append(f"**{res['segundos']}**s")
            
            embed.description = f"**{curr}** ({int(pct)}%) ➝ **{target}**"
            embed.add_field(name=t['time_est'], value=", ".join(tempo_txt), inline=False)
            embed.add_field(name=t['hits'], value=f"{res['hits']:,}", inline=True)
            embed.add_field(name=t['weapon'], value=f"{self.arma_nome} ({self.arma_speed}s)", inline=True)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Error: Numbers only.", ephemeral=True)

class WeaponSelect(ui.Select):
    def __init__(self, vocacao, tipo_skill, lang):
        self.vocacao = vocacao; self.tipo_skill = tipo_skill; self.lang = lang
        opts = [discord.SelectOption(label=n, description=f"Speed: {s}s", value=f"{n}|{s}") for n, s in ARMAS_TREINO.items()]
        super().__init__(placeholder="Select Weapon / Arma...", options=opts)

    async def callback(self, interaction: discord.Interaction):
        n, s = self.values[0].split('|')
        await interaction.response.send_modal(SkillCalcModal(self.vocacao, self.tipo_skill, n, float(s), self.lang))

class SkillTypeSelect(ui.Select):
    def __init__(self, vocacao, lang):
        self.vocacao = vocacao; self.lang = lang
        opts = [
            discord.SelectOption(label="⚔️ Melee (Sword/Axe/Club)", value="melee"),
            discord.SelectOption(label="🏹 Distance", value="distance"),
            discord.SelectOption(label="🛡️ Shielding", value="shielding")
        ]
        super().__init__(placeholder="Select Skill Type...", options=opts)

    async def callback(self, interaction: discord.Interaction):
        v = ui.View(); v.add_item(WeaponSelect(self.vocacao, self.values[0], self.lang))
        await interaction.response.edit_message(content=f"🛠️ **{self.values[0].capitalize()}**. Select Weapon:", view=v)

class VocationSelect(ui.Select):
    def __init__(self, lang):
        self.lang = lang
        opts = [
            discord.SelectOption(label="🛡️ Knight", value="knight"),
            discord.SelectOption(label="🏹 Paladin", value="paladin"),
            discord.SelectOption(label="🔥 Mage (Sorc/Druid)", value="druid")
        ]
        super().__init__(placeholder="Select Vocation...", options=opts)

    async def callback(self, interaction: discord.Interaction):
        v = ui.View(); v.add_item(SkillTypeSelect(self.values[0], self.lang))
        await interaction.response.send_message("Select Skill Type:", view=v, ephemeral=True)

# ==========================================
# 🧮 SISTEMA DE CRAFTING
# ==========================================

class DynamicCraftingModal(ui.Modal):
    def __init__(self, item_name, receita_data, lang):
        self.lang = lang
        t = TEXTOS[lang]
        super().__init__(title=t['modal_title'].format(item_name))
        self.item_name = item_name; self.receita_data = receita_data
        
        resumo = " | ".join([f"{q}x {m[:8]}" for m, q in receita_data['ingredientes'].items()])
        self.add_item(ui.TextInput(label=t['label_skill'], placeholder=t['placeholder_skill'].format(resumo), custom_id="skill"))
        self.add_item(ui.TextInput(label=t['label_qtd'], placeholder=t['placeholder_qtd'], default="1", custom_id="qtd"))
        
        self.materiais_na_janela = list(receita_data['ingredientes'].items())[:3]
        for m, q in self.materiais_na_janela:
            p = t['yes'] if m not in receita_data.get('nao_perde', []) else t['no']
            self.add_item(ui.TextInput(label=t['label_price'].format(m, q), placeholder=t['placeholder_price'].format(p), custom_id=f"price_{m}"))

    async def on_submit(self, interaction: discord.Interaction):
        t = TEXTOS[self.lang]
        try:
            skill = int(self.children[0].value); qtd = int(self.children[1].value)
            ings = {}
            for i, (m, q) in enumerate(self.materiais_na_janela):
                ings[m] = {"qtd": q, "preco": float(self.children[i+2].value), "consome_na_falha": m not in self.receita_data.get('nao_perde', [])}
            
            res = calcular_crafting_detalhado(skill, self.receita_data['multiplicador'], ings, qtd)
            
            embed = discord.Embed(title=t['result_title'].format(qtd, self.item_name), color=discord.Color.blue())
            embed.add_field(name=t['chance'], value=f"{res['chance_sucesso']}%", inline=True)
            embed.add_field(name=t['cost'], value=f"{res['custo_total']:,} gp", inline=True)
            msg_list = "\n".join([f"• **{m}**: {q}" for m, q in res['materiais_necessarios'].items()])
            embed.add_field(name=t['list'], value=msg_list, inline=False)
            embed.set_footer(text=t['footer'].format(interaction.user.display_name))
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except: await interaction.response.send_message("❌ Error", ephemeral=True)

class ItemSelect(ui.Select):
    def __init__(self, cat_key, lang):
        self.lang = lang
        itens_nomes = sorted(ESTRUTURA_MENU.get('crafting', {}).get(cat_key, []))
        opts = [discord.SelectOption(label=i, description=f"Mult: {RECEITAS[i]['multiplicador']}") for i in itens_nomes if i in RECEITAS]
        t = TEXTOS[lang]
        super().__init__(placeholder=t['ask_item'].format(t['cats'].get(cat_key, cat_key)), options=opts)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(DynamicCraftingModal(self.values[0], RECEITAS[self.values[0]], self.lang))

class CategorySelect(ui.Select):
    def __init__(self, lang):
        self.lang = lang
        cats = ESTRUTURA_MENU['crafting']
        opts = [discord.SelectOption(label=TEXTOS[lang]['cats'].get(k, k), value=k) for k in cats.keys()]
        super().__init__(placeholder=TEXTOS[lang]['select_cat'], options=opts)

    async def callback(self, interaction: discord.Interaction):
        v = ui.View(); v.add_item(ItemSelect(self.values[0], self.lang))
        await interaction.response.edit_message(content=TEXTOS[self.lang]['ask_category'], view=v)

# ==========================================
# 🚦 MENU INICIAL
# ==========================================
class ModeSelect(ui.View):
    def __init__(self, lang):
        super().__init__(); self.lang = lang
    
    @ui.button(label="🔨 Crafting", style=discord.ButtonStyle.primary)
    async def craft(self, interaction: discord.Interaction, button: ui.Button):
        v = ui.View(); v.add_item(CategorySelect(self.lang))
        await interaction.response.send_message(TEXTOS[self.lang]['select_cat'], view=v, ephemeral=True)

    @ui.button(label="⚔️ Skills", style=discord.ButtonStyle.danger)
    async def skills(self, interaction: discord.Interaction, button: ui.Button):
        v = ui.View(); v.add_item(VocationSelect(self.lang))
        await interaction.response.send_message("Vocation:", view=v, ephemeral=True)

class LanguageSelect(ui.Select):
    def __init__(self):
        opts = [
            discord.SelectOption(label="Português", emoji="🇧🇷", value="pt"),
            discord.SelectOption(label="English", emoji="🇺🇸", value="en"),
            discord.SelectOption(label="Polski", emoji="🇵🇱", value="pl")
        ]
        super().__init__(placeholder="Select Language / Idioma...", options=opts)

    async def callback(self, interaction: discord.Interaction):
        t = TEXTOS[self.values[0]]
        v = ModeSelect(self.values[0])
        v.children[0].label = t['btn_craft']
        v.children[1].label = t['btn_skill']
        await interaction.response.send_message(t['select_lang'], view=v, ephemeral=True)

class PersistentControlView(ui.View):
    def __init__(self): super().__init__(timeout=None)
    @ui.button(label="🌐 Start / Iniciar", style=discord.ButtonStyle.blurple, custom_id="btn_start")
    async def start(self, interaction: discord.Interaction, button: ui.Button):
        v = ui.View(); v.add_item(LanguageSelect())
        await interaction.response.send_message("🇧🇷 🇺🇸 🇵🇱", view=v, ephemeral=True)

class MyBot(discord.Client):
    def __init__(self): super().__init__(intents=discord.Intents.all()); self.tree = app_commands.CommandTree(self)
    async def setup_hook(self): self.add_view(PersistentControlView()); await self.tree.sync()

bot = MyBot()
@bot.tree.command(name="setup_calculadora")
async def setup(interaction: discord.Interaction):
    await interaction.response.send_message(embed=discord.Embed(title="⚒️ Miracle 7.4 - Tools", color=discord.Color.gold()), view=PersistentControlView())

if __name__ == "__main__":
    if TOKEN:
        Thread(target=run_web_server, daemon=True).start()
        Thread(target=loop_monitoramento, daemon=True).start()
        bot.run(TOKEN)
