import discord
import requests
import pytz
import time
import os
import math
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread
from discord import app_commands, ui
from calculadora import calcular_crafting_detalhado, calcular_tempo_skill, calcular_alchemy_gold, calcular_alchemy_enchant, calcular_alchemy_rune
from itens import RECEITAS, ESTRUTURA_MENU, ARMAS_TREINO, ALCHEMY_DATA, ALCHEMY_MENU_CATS
from idiomas import TEXTOS

TOKEN = os.environ.get('DISCORD_TOKEN') 
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')

URL_RAIDS = "https://miracle74.com/?subtopic=raids"
FUSO_BRASILIA = pytz.timezone('America/Sao_Paulo')

app = Flask('')
@app.route('/')
def home(): return "Bot Bellão (Fix Interaction V13) Online"
def run_web_server(): app.run(host='0.0.0.0', port=8080)

# --- RAIDS (MANTIDO) ---
def carregar_raids():
    try:
        response = requests.get(URL_RAIDS, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        if not table: return []
        raids = []
        rows = table.find_all('tr')[1:] 
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 3:
                nome = cols[0].text.strip()
                intervalo_txt = cols[1].text.lower()
                nums = ''.join(filter(str.isdigit, intervalo_txt))
                if not nums: continue
                val = int(nums)
                if 'day' in intervalo_txt or 'dia' in intervalo_txt: val *= 24
                last_txt = cols[2].text.strip()
                if last_txt and val > 0:
                    try:
                        dt = datetime.strptime(last_txt, '%Y-%m-%d %H:%M:%S')
                        dt = FUSO_BRASILIA.localize(dt) if dt.tzinfo is None else dt
                        raids.append({"nome": nome, "proxima": dt + timedelta(hours=val)})
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
                if 14 < diff <= 16: 
                    msg = f"⚠️ **RAID:** {r['nome']} @ {r['proxima'].strftime('%H:%M')} (BRT)\n⏳ Faltam 15 min!"
                    requests.post(WEBHOOK_URL, json={"content": msg})
            time.sleep(60)
        except: time.sleep(60)

# ==========================================
# 🔄 VIEW RESTART
# ==========================================
class ResultView(ui.View):
    def __init__(self): super().__init__(timeout=None)
    @ui.button(label="🔄 Menu Principal / Restart", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def restart(self, interaction: discord.Interaction, button: ui.Button):
        v = ui.View(); v.add_item(LanguageSelect())
        await interaction.response.send_message("🇧🇷 🇺🇸 🇵🇱 Selecione / Select:", view=v, ephemeral=True)

# ==========================================
# 🧪 SISTEMA ALCHEMY (CORRIGIDO)
# ==========================================

class AlchemyGoldModal(ui.Modal):
    def __init__(self, lang):
        self.lang = lang; t = TEXTOS[lang]
        super().__init__(title=t['alch_gold'])
        self.add_item(ui.TextInput(label=t['alch_skill_label'], placeholder="Ex: 50", custom_id="s", max_length=3))
        # Label atualizado para "Total de Gold"
        self.add_item(ui.TextInput(label=t['alch_gold_label'], placeholder=t['alch_gold_ph'], custom_id="q"))

    async def on_submit(self, interaction: discord.Interaction):
        try:
            skill = int(self.children[0].value)
            # Tratamento para 1kk, 10k, etc
            raw_gold = self.children[1].value.lower().replace('.', '').replace(',', '')
            if 'k' in raw_gold:
                # Conta quantos 'k' tem (ex: 1kk = 1.000.000)
                multiplicador = 1000 ** raw_gold.count('k')
                raw_gold = raw_gold.replace('k', '')
                gold_total = int(float(raw_gold) * multiplicador)
            else:
                gold_total = int(raw_gold)
            
            res = calcular_alchemy_gold(skill, gold_total)
            t = TEXTOS[self.lang]
            
            embed = discord.Embed(title=t['alch_res_gold'], color=discord.Color.gold())
            embed.description = f"Convertendo: **{gold_total:,} gp**"
            embed.add_field(name=t['alch_needs'], value=f"🛒 **{res['converters']}x** {t['alch_conv_name']}", inline=True)
            embed.add_field(name=t['cost'], value=f"💰 **{res['custo']:,} gp**", inline=True)
            embed.add_field(name=t['alch_chance'], value=f"🍀 {res['chance']}% (Bonus)", inline=False)
            
            await interaction.response.send_message(embed=embed, ephemeral=True, view=ResultView())
        except Exception as e: 
            print(e)
            await interaction.response.send_message("❌ Erro: Use numeros ex: 10000 ou 10k", ephemeral=True)

class AlchemyRuneModal(ui.Modal):
    def __init__(self, rune_name, lang):
        self.lang = lang; self.rune = rune_name; t = TEXTOS[lang]
        super().__init__(title=t['alch_rune_title'].format(rune_name[:15]))
        self.add_item(ui.TextInput(label=t['alch_skill_label'], placeholder="Ex: 60", custom_id="s"))
    async def on_submit(self, interaction: discord.Interaction):
        try:
            skill = int(self.children[0].value)
            res = calcular_alchemy_rune(skill, self.rune)
            t = TEXTOS[self.lang]
            embed = discord.Embed(title=t['alch_rune_title'].format(self.rune), color=discord.Color.magenta())
            if not res['possivel']:
                embed.description = t['alch_low_skill'].format(res['min_skill']); embed.color = discord.Color.red()
            else:
                embed.add_field(name=t['alch_real_chance'], value=f"🎯 **{res['chance']}%**", inline=False)
                if res['pro']: embed.add_field(name="⚠️ Profession", value=t['alch_req_pro'], inline=False)
                embed.set_footer(text=t['alch_rune_decay'])
            await interaction.response.send_message(embed=embed, ephemeral=True, view=ResultView())
        except: await interaction.response.send_message("❌ Error", ephemeral=True)

class AlchemyEnchantModal(ui.Modal):
    def __init__(self, crystal_name, base_chance, lang):
        self.lang = lang; self.crystal = crystal_name; self.base = base_chance; t = TEXTOS[lang]
        super().__init__(title=t['alch_ench_title'].format(crystal_name))
        self.add_item(ui.TextInput(label=t['alch_skill_label'], placeholder="Ex: 60", custom_id="s"))
    async def on_submit(self, interaction: discord.Interaction):
        try:
            skill = int(self.children[0].value); res = calcular_alchemy_enchant(skill, self.base); t = TEXTOS[self.lang]
            embed = discord.Embed(title=t['alch_ench_res'].format(self.crystal), color=discord.Color.purple())
            embed.add_field(name=t['alch_real_chance'], value=f"🎯 **{res['chance_real']}%**", inline=False)
            embed.add_field(name=t['alch_guarantee'], value=f"📦 **{res['qtd_media']}x** {t['alch_crystals']}", inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True, view=ResultView())
        except: await interaction.response.send_message("❌ Error", ephemeral=True)

# VIEWS COM TIMEOUT=NONE
class AlchemyRuneSelect(ui.Select):
    def __init__(self, category_key, lang):
        self.lang = lang; runes_list = sorted(ALCHEMY_MENU_CATS.get(category_key, []))
        opts = [discord.SelectOption(label=r, value=r) for r in runes_list]
        super().__init__(placeholder="Select Rune...", options=opts)
    async def callback(self, i: discord.Interaction): await i.response.send_modal(AlchemyRuneModal(self.values[0], self.lang))

class AlchemyRuneCategorySelect(ui.Select):
    def __init__(self, lang):
        self.lang = lang; t = TEXTOS[lang]
        opts = [discord.SelectOption(label=t['alch_rune_atk'], value="cat_atk"), discord.SelectOption(label=t['alch_rune_sup'], value="cat_sup")]
        super().__init__(placeholder=t['alch_rune_cat'], options=opts)
    async def callback(self, i: discord.Interaction):
        v = ui.View(timeout=None); v.add_item(AlchemyRuneSelect(self.values[0], self.lang)) # Timeout None aqui
        await i.response.edit_message(content=TEXTOS[self.lang]['select_cat'], view=v)

class AlchemyEnchantSelect(ui.Select):
    def __init__(self, lang):
        self.lang = lang; crystals = ALCHEMY_DATA['crystals']; opts = []
        for nome, dados in crystals.items():
            opts.append(discord.SelectOption(label=nome, description=f"Base Chance: {dados['base_chance']}%", value=f"{nome}|{dados['base_chance']}"))
        super().__init__(placeholder="Select Crystal...", options=opts)
    async def callback(self, i: discord.Interaction):
        nome, base = self.values[0].split('|')
        await i.response.send_modal(AlchemyEnchantModal(nome, float(base), self.lang))

class AlchemySelect(ui.View):
    def __init__(self, lang): super().__init__(timeout=None); self.lang = lang # Timeout None aqui
    @ui.button(label="💰 Gold Converter", style=discord.ButtonStyle.primary, emoji="💰") # Nome alterado
    async def gold(self, i: discord.Interaction, b: ui.Button): await i.response.send_modal(AlchemyGoldModal(self.lang))
    @ui.button(label="✨ Enchant", style=discord.ButtonStyle.secondary, emoji="✨")
    async def enchant(self, i: discord.Interaction, b: ui.Button):
        v = ui.View(timeout=None); v.add_item(AlchemyEnchantSelect(self.lang))
        await i.response.send_message(TEXTOS[self.lang]['select_cat'], view=v, ephemeral=True)
    @ui.button(label="💎 Runes", style=discord.ButtonStyle.success, emoji="💎")
    async def runes(self, i: discord.Interaction, b: ui.Button):
        v = ui.View(timeout=None); v.add_item(AlchemyRuneCategorySelect(self.lang))
        await i.response.send_message(TEXTOS[self.lang]['select_cat'], view=v, ephemeral=True)

# ==========================================
# ⚔️ SKILLS & GERAL (Views com Timeout=None)
# ==========================================
# ... DualSkillModal, DualWeaponSelect, DualShieldSelect, DualEquipmentView ...
# Apenas certifique-se de adicionar `timeout=None` no __init__ das Views que chamam menus
# Para economizar espaço, vou focar nas classes principais de view:

class DualEquipmentView(ui.View):
    def __init__(self, voc, tipo, lang):
        super().__init__(timeout=None); self.voc = voc; self.tipo = tipo; self.lang = lang # Timeout None
        self.w_tier = "Normal"; self.s_tier = "Normal"
        self.add_item(DualWeaponSelect()); self.add_item(DualShieldSelect())
    @ui.button(label="Avançar / Next ➡️", style=discord.ButtonStyle.success, row=2)
    async def confirm(self, i: discord.Interaction, b: ui.Button):
        await i.response.send_modal(DualSkillModal(self.voc, self.tipo, self.w_tier, self.s_tier, self.lang))

class SkillTypeSelect(ui.Select):
    def __init__(self, voc, lang):
        self.voc = voc; self.lang = lang
        opts = [discord.SelectOption(label="⚔️ Melee + Shield", value="dual_melee"), discord.SelectOption(label="🏹 Distance + Shield", value="dual_dist"), discord.SelectOption(label="⚔️ Melee", value="melee"), discord.SelectOption(label="🛡️ Shielding", value="shielding"), discord.SelectOption(label="🏹 Distance", value="distance")]
        super().__init__(placeholder="Qual treino?", options=opts)
    async def callback(self, i: discord.Interaction):
        if "dual" in self.values[0]:
            view = DualEquipmentView(self.voc, "distance" if "dist" in self.values[0] else "melee", self.lang)
            await i.response.send_message("🛠️ Configure Equipamentos:", view=view, ephemeral=True)
        else:
            v = ui.View(timeout=None); v.add_item(WeaponSelect(self.voc, self.values[0], self.lang))
            await i.response.edit_message(content=f"🛠️ Configurando **{self.values[0]}**:", view=v)

class VocationSelect(ui.Select):
    def __init__(self, lang):
        self.lang = lang
        opts = [discord.SelectOption(label="🛡️ Knight", value="knight"), discord.SelectOption(label="🏹 Paladin", value="paladin"), discord.SelectOption(label="🔥 Mage", value="druid")]
        super().__init__(placeholder="Vocação...", options=opts)
    async def callback(self, i: discord.Interaction):
        v = ui.View(timeout=None); v.add_item(SkillTypeSelect(self.values[0], self.lang))
        await i.response.send_message("Tipo de Treino:", view=v, ephemeral=True)

class CategorySelect(ui.Select):
    def __init__(self, lang):
        self.lang = lang; cats = ESTRUTURA_MENU['crafting']
        opts = [discord.SelectOption(label=TEXTOS[lang]['cats'].get(k, k), value=k) for k in cats.keys()]
        super().__init__(placeholder=TEXTOS[lang]['select_cat'], options=opts)
    async def callback(self, i: discord.Interaction):
        v = ui.View(timeout=None); v.add_item(ItemSelect(self.values[0], self.lang))
        await i.response.edit_message(content=TEXTOS[self.lang]['ask_category'], view=v)

class ModeSelect(ui.View):
    def __init__(self, lang): super().__init__(timeout=None); self.lang = lang # Timeout None
    @ui.button(label="🔨 Crafting", style=discord.ButtonStyle.primary, row=0)
    async def craft(self, i: discord.Interaction, b: ui.Button):
        v = ui.View(timeout=None); v.add_item(CategorySelect(self.lang))
        await i.response.send_message(TEXTOS[self.lang]['select_cat'], view=v, ephemeral=True)
    @ui.button(label="🧪 Alchemy", style=discord.ButtonStyle.success, row=0)
    async def alchemy(self, i: discord.Interaction, b: ui.Button):
        await i.response.send_message(TEXTOS[self.lang]['alch_select'], view=AlchemySelect(self.lang), ephemeral=True)
    @ui.button(label="⚔️ Skills", style=discord.ButtonStyle.danger, row=0)
    async def skills(self, i: discord.Interaction, b: ui.Button):
        v = ui.View(timeout=None); v.add_item(VocationSelect(self.lang))
        await i.response.send_message("Vocation:", view=v, ephemeral=True)
    @ui.button(label="☕ Apoiar / Donate", style=discord.ButtonStyle.secondary, emoji="💰", row=1)
    async def donate(self, i: discord.Interaction, b: ui.Button):
        embed = discord.Embed(title="☕ Apoie o Dev", color=discord.Color.gold())
        embed.description = "Feito com ❤️ para a comunidade Miracle."
        embed.add_field(name="🇧🇷 Pix", value="`seu_email@pix.com`", inline=True)
        embed.add_field(name="🌎 PayPal", value="[Link](https://paypal.me/seuusuario)", inline=True)
        embed.add_field(name="🪙 Tibia Coins", value="Parcel to: **Obellao**", inline=False)
        await i.response.send_message(embed=embed, ephemeral=True)

class LanguageSelect(ui.Select):
    def __init__(self):
        opts = [discord.SelectOption(label="Português", emoji="🇧🇷", value="pt"), discord.SelectOption(label="English", emoji="🇺🇸", value="en"), discord.SelectOption(label="Polski", emoji="🇵🇱", value="pl")]
        super().__init__(placeholder="Select Language / Idioma...", options=opts)
    async def callback(self, i: discord.Interaction):
        t = TEXTOS[self.values[0]]; v = ModeSelect(self.values[0])
        v.children[0].label = t['btn_craft']; v.children[1].label = t['btn_alch']; v.children[2].label = t['btn_skill']
        await i.response.send_message(t['select_lang'], view=v, ephemeral=True)

class PersistentControlView(ui.View):
    def __init__(self): super().__init__(timeout=None)
    @ui.button(label="🌐 Start / Iniciar", style=discord.ButtonStyle.blurple, custom_id="btn_start")
    async def start(self, i: discord.Interaction, b: ui.Button):
        v = ui.View(timeout=None); v.add_item(LanguageSelect()) # Timeout None
        await i.response.send_message("🇧🇷 🇺🇸 🇵🇱", view=v, ephemeral=True)

# --- BOT SETUP (MANTIDO) ---
class MyBot(discord.Client):
    def __init__(self): super().__init__(intents=discord.Intents.all()); self.tree = app_commands.CommandTree(self)
    async def setup_hook(self): self.add_view(PersistentControlView()); await self.tree.sync()

bot = MyBot()

@bot.tree.command(name="setup_calculadora")
async def setup(interaction: discord.Interaction):
    await interaction.response.send_message(embed=discord.Embed(title="⚒️ Miracle Tools", color=discord.Color.gold()), view=PersistentControlView())

@bot.tree.command(name="checar_raids", description="Verifica as próximas raids.")
async def checar_raids(interaction: discord.Interaction):
    await interaction.response.defer()
    raids = carregar_raids()
    agora = datetime.now(FUSO_BRASILIA)
    futuras = sorted([r for r in raids if r['proxima'] > agora], key=lambda x: x['proxima'])
    if not futuras: await interaction.followup.send("❌ Nenhuma raid futura detectada.")
    else:
        txt = "**📋 Próximas Raids:**\n"
        for r in futuras[:8]:
            d = r['proxima'] - agora
            h, m = int(d.total_seconds()//3600), int((d.total_seconds()%3600)//60)
            txt += f"• **{r['nome']}** em {h}h {m}m ({r['proxima'].strftime('%d/%m %H:%M')})\n"
        await interaction.followup.send(txt)

if __name__ == "__main__":
    if TOKEN:
        Thread(target=run_web_server, daemon=True).start()
        Thread(target=loop_monitoramento, daemon=True).start()
        bot.run(TOKEN)
