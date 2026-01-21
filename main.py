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
# A linha abaixo vai funcionar agora que atualizamos o calculadora.py
from calculadora import calcular_crafting_detalhado, calcular_tempo_skill, calcular_alchemy_gold, calcular_alchemy_enchant, calcular_alchemy_rune, calcular_party_range
from itens import RECEITAS, ESTRUTURA_MENU, ARMAS_TREINO, ALCHEMY_DATA, ALCHEMY_MENU_CATS, RASHID_SCHEDULE
from idiomas import TEXTOS

TOKEN = os.environ.get('DISCORD_TOKEN') 
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')

URL_RAIDS = "https://miracle74.com/?subtopic=raids"
FUSO_BRASILIA = pytz.timezone('America/Sao_Paulo')

app = Flask('')
@app.route('/')
def home(): return "Bot Bellão (V21 Final) Online"
def run_web_server(): app.run(host='0.0.0.0', port=8080)

# --- RAIDS SYSTEM ---
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
        v = ui.View(timeout=None); v.add_item(LanguageSelect())
        await interaction.response.send_message("🇧🇷 🇺🇸 🇵🇱 Selecione / Select:", view=v, ephemeral=True)

# ==========================================
# 🛠️ NOVAS FERRAMENTAS (PARTY & SS)
# ==========================================

class PartyShareModal(ui.Modal):
    def __init__(self, lang):
        self.lang = lang; t = TEXTOS[lang]
        super().__init__(title=t['party_title'])
        self.add_item(ui.TextInput(label=t['party_label'], placeholder="Ex: 80", custom_id="lvl", max_length=4))

    async def on_submit(self, interaction: discord.Interaction):
        try:
            level = int(self.children[0].value)
            min_lvl, max_lvl = calcular_party_range(level)
            t = TEXTOS[self.lang]
            
            embed = discord.Embed(title=t['party_title'], color=discord.Color.green())
            embed.description = t['party_res'].format(level)
            embed.add_field(name="Min Level 📉", value=f"**{min_lvl}**", inline=True)
            embed.add_field(name="Max Level 📈", value=f"**{max_lvl}**", inline=True)
            
            await interaction.response.send_message(embed=embed, ephemeral=True, view=ResultView())
        except: await interaction.response.send_message("❌ Error: Number required.", ephemeral=True)

class ToolsSelect(ui.View):
    def __init__(self, lang): super().__init__(timeout=None); self.lang = lang
    
    @ui.button(label="🤝 Party Share", style=discord.ButtonStyle.primary)
    async def party(self, i: discord.Interaction, b: ui.Button):
        await i.response.send_modal(PartyShareModal(self.lang))

    @ui.button(label="💾 Server Save", style=discord.ButtonStyle.danger)
    async def ss(self, i: discord.Interaction, b: ui.Button):
        agora = datetime.now(FUSO_BRASILIA)
        target = agora.replace(hour=5, minute=0, second=0, microsecond=0)
        if agora.hour >= 5: target += timedelta(days=1)
        
        diff = target - agora
        h, m = int(diff.total_seconds()//3600), int((diff.total_seconds()%3600)//60)
        tempo_str = f"{h}h {m}m"
        
        t = TEXTOS[self.lang]
        embed = discord.Embed(title=t['ss_title'], color=discord.Color.red())
        embed.description = t['ss_msg'].format(tempo_str)
        await i.response.send_message(embed=embed, ephemeral=True, view=ResultView())

# ==========================================
# 🧪 SISTEMA ALCHEMY
# ==========================================

class AlchemyGoldModal(ui.Modal):
    def __init__(self, lang):
        self.lang = lang; t = TEXTOS[lang]
        super().__init__(title=t['alch_gold'])
        self.add_item(ui.TextInput(label=t['alch_skill_label'], placeholder="Ex: 50", custom_id="s", max_length=3))
        self.add_item(ui.TextInput(label=t['alch_gold_label'], placeholder=t['alch_gold_ph'], custom_id="q"))

    async def on_submit(self, interaction: discord.Interaction):
        try:
            skill = int(self.children[0].value)
            raw_gold = self.children[1].value.lower().replace('.', '').replace(',', '')
            if 'k' in raw_gold:
                multiplier = 1000 ** raw_gold.count('k')
                gold_total = int(float(raw_gold.replace('k', '')) * multiplier)
            else:
                gold_total = int(raw_gold)
            res = calcular_alchemy_gold(skill, gold_total)
            t = TEXTOS[self.lang]
            embed = discord.Embed(title=t['alch_res_gold'], color=discord.Color.gold())
            embed.description = f"Convertendo: **{gold_total:,} gp**"
            embed.add_field(name=t['alch_needs'], value=f"🛒 **{res['converters']}x** {t['alch_conv_name']}", inline=True)
            embed.add_field(name=t['cost'], value=f"💰 **{res['custo']:,} gp**", inline=True)
            embed.add_field(name=t['alch_chance'], value=f"🍀 {res['chance']}%", inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True, view=ResultView())
        except Exception as e: 
            print(f"Erro Gold: {e}")
            await interaction.response.send_message("❌ Erro no formato. Use ex: 10000 ou 10k", ephemeral=True)

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
        v = ui.View(timeout=None); v.add_item(AlchemyRuneSelect(self.values[0], self.lang))
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
    def __init__(self, lang): super().__init__(timeout=None); self.lang = lang
    @ui.button(label="💰 Gold Converter", style=discord.ButtonStyle.primary, emoji="💰")
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
# ⚔️ SKILLS & GERAL
# ==========================================

class DualSkillModal(ui.Modal):
    def __init__(self, vocacao, tipo_melee, w_tier_sel, s_tier_sel, lang):
        self.lang = lang; self.vocacao = vocacao; self.tipo_melee = tipo_melee
        self.w_tier_name = w_tier_sel; self.s_tier_name = s_tier_sel
        w_key = "Normal / Nenhuma"
        if w_tier_sel == "Normal": w_key = "Normal / Nenhuma"
        elif "-5%" in w_tier_sel: w_key = "Weapon (-5% Atk Speed)"
        elif "-6%" in w_tier_sel: w_key = "Weapon (-6% Atk Speed)"
        else:
            term = "Spear" if tipo_melee == 'distance' else "Weapon"
            for k in ARMAS_TREINO:
                if w_tier_sel in k and term in k: w_key = k; break
            if w_key == "Normal / Nenhuma" and term == "Spear":
                for k in ARMAS_TREINO:
                    if w_tier_sel in k and "Weapon" in k: w_key = k; break
        s_key = "Normal / Nenhuma"
        if s_tier_sel != "Normal":
            for k in ARMAS_TREINO:
                if s_tier_sel in k and "Shield" in k: s_key = k; break
        self.w_stats = ARMAS_TREINO.get(w_key, ARMAS_TREINO["Normal / Nenhuma"])
        self.s_stats = ARMAS_TREINO.get(s_key, ARMAS_TREINO["Normal / Nenhuma"])
        super().__init__(title=f"{vocacao} (Dual)")
        self.add_item(ui.TextInput(label=f"{tipo_melee.capitalize()} (Atual - Alvo)", placeholder="Ex: 80-85", custom_id="m"))
        self.add_item(ui.TextInput(label=f"{tipo_melee.capitalize()} % (Já treinado)", placeholder="Ex: 50 (50%)", custom_id="mp", max_length=3))
        self.add_item(ui.TextInput(label="Shielding (Atual - Alvo)", placeholder="Ex: 75-80", custom_id="s"))
        self.add_item(ui.TextInput(label="Shielding %", placeholder="Ex: 0", custom_id="sp", max_length=3))
        self.add_item(ui.TextInput(label="Preço Unit. Arma (Opcional)", required=False, custom_id="pr"))
    async def on_submit(self, interaction: discord.Interaction):
        try:
            m_c, m_t = map(int, self.children[0].value.replace('/', '-').split('-'))
            m_p = float(self.children[1].value.replace(',', '.'))
            s_c, s_t = map(int, self.children[2].value.replace('/', '-').split('-'))
            s_p = float(self.children[3].value.replace(',', '.'))
            price = int(self.children[4].value.replace('.','').replace('k','000')) if self.children[4].value else 0
            rm = calcular_tempo_skill(self.vocacao, self.tipo_melee, m_c, m_p, m_t, self.w_stats['speed'])
            rs = calcular_tempo_skill(self.vocacao, "shielding", s_c, s_p, s_t, self.s_stats['speed'])
            qw = math.ceil(rm['hits'] / self.w_stats['charges'])
            if self.w_stats['charges'] > 999999: qw = 1
            qs = math.ceil(rs['hits'] / self.s_stats['charges'])
            if self.s_stats['charges'] > 999999: qs = 1
            fator = 0
            if "Normal" not in str(self.w_stats['charges']): fator += qw
            if "Normal" not in str(self.s_stats['charges']): fator += qs
            custo = fator * price
            embed = discord.Embed(title=f"⚔️ Treino Misto ({self.vocacao})", color=discord.Color.purple())
            w_lbl = f"🛒 **{qw}x** {self.w_tier_name}" if self.w_stats['charges'] < 999999 else f"♾️ **{self.w_tier_name}**"
            embed.add_field(name=f"⚔️ {self.tipo_melee}: {m_c}➝{m_t}", value=f"⏱️ {rm['dias']}d {rm['horas']}h {rm['minutos']}m\n{w_lbl}", inline=True)
            s_lbl = f"🛒 **{qs}x** {self.s_tier_name}" if self.s_stats['charges'] < 999999 else "🛡️ **Normal**"
            embed.add_field(name=f"🛡️ Shield: {s_c}➝{s_t}", value=f"⏱️ {rs['dias']}d {rs['horas']}h {rs['minutos']}m\n{s_lbl}", inline=True)
            if custo > 0: embed.add_field(name="💰 Custo Est.", value=f"{custo:,} gp", inline=False)
            embed.set_footer(text=f"Hits: {rm['hits']:,} (A) / {rs['hits']:,} (D)")
            await interaction.response.send_message(embed=embed, ephemeral=True, view=ResultView())
        except: await interaction.response.send_message("❌ Erro. Use formato '80-85'.", ephemeral=True)

class DualWeaponSelect(ui.Select):
    def __init__(self):
        opts = [discord.SelectOption(label=x, value=x.split()[0] if "Normal" not in x and "%" not in x else x) for x in ["Normal / Nenhuma", "Weapon (-5% Atk Speed)", "Weapon (-6% Atk Speed)", "Spark (3.6k)", "Lightning (7.2k)", "Inferno (10.8k)"]]
        super().__init__(placeholder="Selecione a Arma...", options=opts, row=0)
    async def callback(self, i: discord.Interaction): self.view.w_tier = self.values[0]; await i.response.defer()

class DualShieldSelect(ui.Select):
    def __init__(self):
        opts = [discord.SelectOption(label=x, value=x.split()[0] if "Normal" not in x else "Normal") for x in ["Normal / Nenhum", "Spark (7.2k)", "Lightning (14.4k)", "Inferno (21.6k)"]]
        super().__init__(placeholder="Selecione o Escudo...", options=opts, row=1)
    async def callback(self, i: discord.Interaction): self.view.s_tier = self.values[0]; await i.response.defer()

class DualEquipmentView(ui.View):
    def __init__(self, voc, tipo, lang):
        super().__init__(timeout=None); self.voc = voc; self.tipo = tipo; self.lang = lang
        self.w_tier = "Normal"; self.s_tier = "Normal"
        self.add_item(DualWeaponSelect()); self.add_item(DualShieldSelect())
    @ui.button(label="Avançar / Next ➡️", style=discord.ButtonStyle.success, row=2)
    async def confirm(self, i: discord.Interaction, b: ui.Button):
        await i.response.send_modal(DualSkillModal(self.voc, self.tipo, self.w_tier, self.s_tier, self.lang))

class SingleSkillModal(ui.Modal):
    def __init__(self, voc, tipo, nome, spd, chg, lang):
        self.lang = lang; self.voc = voc; self.tipo = tipo; self.spd = spd; self.chg = chg; self.nome = nome
        t = TEXTOS[lang]
        super().__init__(title=f"{voc} - {tipo}")
        self.add_item(ui.TextInput(label="Skill Atual", custom_id="c"))
        self.add_item(ui.TextInput(label="% Atual", custom_id="p"))
        self.add_item(ui.TextInput(label="Skill Desejado", custom_id="t"))
        self.add_item(ui.TextInput(label="Preço (Opcional)", required=False, custom_id="pr"))
    async def on_submit(self, interaction: discord.Interaction):
        try:
            c = int(self.children[0].value); p = float(self.children[1].value.replace(',', '.'))
            t = int(self.children[2].value); pr = int(self.children[3].value.replace('.','').replace('k','000')) if self.children[3].value else 0
            res = calcular_tempo_skill(self.voc, self.tipo, c, p, t, self.spd)
            qtd = math.ceil(res['hits'] / self.chg)
            if self.chg > 999999: qtd = 1
            cost = qtd * pr
            emb = discord.Embed(title=f"⚔️ {self.voc.capitalize()} - {self.tipo.capitalize()}", color=discord.Color.red())
            emb.add_field(name=TEXTOS[self.lang]['time_est'], value=f"⏱️ **{res['dias']}d {res['horas']}h {res['minutos']}m**", inline=False)
            r_val = f"👊 Hits: {res['hits']:,}"
            if "Normal" not in self.nome:
                suf = "(Eterna)" if self.chg > 999999 else "un."
                r_val += f"\n🛒 **Qtd: {qtd}** {suf}"
                if cost > 0: emb.add_field(name="💰 Custo", value=f"{cost:,} gp", inline=True)
            emb.add_field(name="📦 Recurso", value=r_val, inline=True)
            await interaction.response.send_message(embed=emb, ephemeral=True, view=ResultView())
        except: await interaction.response.send_message("❌ Erro", ephemeral=True)

class WeaponSelect(ui.Select):
    def __init__(self, voc, tipo, lang):
        self.voc = voc; self.tipo = tipo; self.lang = lang
        opts = [discord.SelectOption(label=x, value=x.split()[0] if "Normal" not in x and "%" not in x else x) for x in ["Normal / Nenhuma", "Weapon (-5% Atk Speed)", "Weapon (-6% Atk Speed)", "Spark (3.6k)", "Lightning (7.2k)", "Inferno (10.8k)"]]
        super().__init__(placeholder="Tier da Arma...", options=opts)
    async def callback(self, i: discord.Interaction):
        tier = self.values[0]
        stats = ARMAS_TREINO["Normal / Nenhuma"]; nome = tier
        if tier in ["Spark", "Lightning", "Inferno"]:
            term = "Shield" if "shield" in self.tipo else "Weapon"
            for k,v in ARMAS_TREINO.items():
                if tier in k and term in k: stats = v; nome = k; break
        else: stats = ARMAS_TREINO.get(tier, stats)
        await i.response.send_modal(SingleSkillModal(self.voc, self.tipo, nome, stats['speed'], stats['charges'], self.lang))

class SkillTypeSelect(ui.Select):
    def __init__(self, voc, lang):
        self.voc = voc; self.lang = lang
        opts = [
            discord.SelectOption(label="⚔️ Melee + Shield (Juntos)", value="dual_melee"),
            discord.SelectOption(label="🏹 Distance + Shield (Juntos)", value="dual_dist"),
            discord.SelectOption(label="⚔️ Apenas Melee", value="melee"),
            discord.SelectOption(label="🛡️ Apenas Shielding", value="shielding"),
            discord.SelectOption(label="🏹 Apenas Distance", value="distance")
        ]
        super().__init__(placeholder="Qual treino?", options=opts)
    async def callback(self, i: discord.Interaction):
        if "dual" in self.values[0]:
            view = DualEquipmentView(self.voc, "distance" if "dist" in self.values[0] else "melee", self.lang)
            await i.response.send_message("🛠️ Configure Equipamentos:", view=view, ephemeral=True)
        else:
            v = ui.View(timeout=None); v.add_item(WeaponSelect(self.voc, self.values[0], self.lang))
            await i.response.edit_message(content=f"🛠️ Configurando **{self.values[0]}**:", view=v)

# ==========================================
# 🔨 CRAFTING & MENUS GERAIS
# ==========================================
class VocationSelect(ui.Select):
    def __init__(self, lang):
        self.lang = lang
        opts = [discord.SelectOption(label="🛡️ Knight", value="knight"), discord.SelectOption(label="🏹 Paladin", value="paladin"), discord.SelectOption(label="🔥 Mage", value="druid")]
        super().__init__(placeholder="Vocação...", options=opts)
    async def callback(self, i: discord.Interaction):
        v = ui.View(timeout=None); v.add_item(SkillTypeSelect(self.values[0], self.lang))
        await i.response.send_message("Tipo de Treino:", view=v, ephemeral=True)

class DynamicCraftingModal(ui.Modal):
    def __init__(self, item_name, receita_data, lang):
        self.lang = lang; t = TEXTOS[lang]
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
            await interaction.response.send_message(embed=embed, ephemeral=True, view=ResultView())
        except: await interaction.response.send_message("❌ Error", ephemeral=True)

class ItemSelect(ui.Select):
    def __init__(self, cat_key, lang):
        self.lang = lang
        itens_nomes = sorted(ESTRUTURA_MENU.get('crafting', {}).get(cat_key, []))
        opts = [discord.SelectOption(label=i, description=f"Mult: {RECEITAS[i]['multiplicador']}") for i in itens_nomes if i in RECEITAS]
        t = TEXTOS[lang]
        super().__init__(placeholder=t['ask_item'].format(t['cats'].get(cat_key, cat_key)), options=opts)
    async def callback(self, i: discord.Interaction): await i.response.send_modal(DynamicCraftingModal(self.values[0], RECEITAS[self.values[0]], self.lang))

class CategorySelect(ui.Select):
    def __init__(self, lang):
        self.lang = lang; cats = ESTRUTURA_MENU['crafting']
        opts = [discord.SelectOption(label=TEXTOS[lang]['cats'].get(k, k), value=k) for k in cats.keys()]
        super().__init__(placeholder=TEXTOS[lang]['select_cat'], options=opts)
    async def callback(self, i: discord.Interaction):
        v = ui.View(timeout=None); v.add_item(ItemSelect(self.values[0], self.lang))
        await i.response.edit_message(content=TEXTOS[self.lang]['ask_category'], view=v)

class ModeSelect(ui.View):
    def __init__(self, lang): super().__init__(timeout=None); self.lang = lang
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
    @ui.button(label="🕌 Rashid", style=discord.ButtonStyle.secondary, row=0)
    async def rashid_btn(self, i: discord.Interaction, b: ui.Button):
        agora = datetime.now(FUSO_BRASILIA)
        if agora.hour < 5: agora = agora - timedelta(days=1)
        dia_semana = agora.weekday()
        info = RASHID_SCHEDULE.get(dia_semana)
        t = TEXTOS[self.lang]
        if info:
            embed = discord.Embed(title=t['rashid_title'].format(info['city']), color=discord.Color.dark_gold())
            desc = t['rashid_desc'].format(info['desc'])
            if info['url']: desc += f"\n\n**[{t['rashid_map']}]({info['url']})**"
            embed.description = desc
            await i.response.send_message(embed=embed, ephemeral=True)
        else:
            await i.response.send_message(t['rashid_error'], ephemeral=True)
    @ui.button(label="🛠️ Extras", style=discord.ButtonStyle.primary, row=1)
    async def tools(self, i: discord.Interaction, b: ui.Button):
        v = ui.View(timeout=None); v.add_item(ToolsSelect(self.lang))
        await i.response.send_message(TEXTOS[self.lang]['tools_select'], view=v, ephemeral=True)
    @ui.button(label="☕ Apoiar / Donate", style=discord.ButtonStyle.secondary, emoji="💰", row=1)
    async def donate(self, i: discord.Interaction, b: ui.Button):
        embed = discord.Embed(title="☕ Apoie o Dev / Support", color=discord.Color.gold())
        embed.description = "Feito com ❤️ para a comunidade Miracle."
        embed.add_field(name="🇧🇷 Pix", value="`seu_email@pix.com`", inline=True)
        embed.add_field(name="🌎 PayPal", value="[Link](https://livepix.gg/obellao)", inline=True)
        embed.add_field(name="🪙 Tibia Coins", value="Parcel to: **Obellao**", inline=False)
        await i.response.send_message(embed=embed, ephemeral=True)

class LanguageSelect(ui.Select):
    def __init__(self):
        opts = [discord.SelectOption(label="Português", emoji="🇧🇷", value="pt"), discord.SelectOption(label="English", emoji="🇺🇸", value="en"), discord.SelectOption(label="Polski", emoji="🇵🇱", value="pl")]
        super().__init__(placeholder="Select Language / Idioma...", options=opts)
    async def callback(self, i: discord.Interaction):
        t = TEXTOS[self.values[0]]; v = ModeSelect(self.values[0])
        v.children[0].label = t['btn_craft']; v.children[1].label = t['btn_alch']; v.children[2].label = t['btn_skill']; v.children[3].label = t['btn_rashid']; v.children[4].label = t['btn_tools']
        await i.response.send_message(t['select_lang'], view=v, ephemeral=True)

class PersistentControlView(ui.View):
    def __init__(self): super().__init__(timeout=None)
    @ui.button(label="🌐 Start / Iniciar", style=discord.ButtonStyle.blurple, custom_id="btn_start")
    async def start(self, i: discord.Interaction, b: ui.Button):
        v = ui.View(timeout=None); v.add_item(LanguageSelect())
        await i.response.send_message("🇧🇷 🇺🇸 🇵🇱", view=v, ephemeral=True)

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

@bot.tree.command(name="rashid", description="Onde está o Rashid hoje?")
async def rashid(interaction: discord.Interaction):
    agora = datetime.now(FUSO_BRASILIA)
    if agora.hour < 5: agora = agora - timedelta(days=1)
    dia_semana = agora.weekday()
    info = RASHID_SCHEDULE.get(dia_semana)
    if info:
        embed = discord.Embed(title=f"🕌 Rashid está em: {info['city']}", color=discord.Color.dark_gold())
        desc_txt = f"📍 {info['desc']}"
        if info['url']: desc_txt += f"\n\n🗺️ **[Clique aqui para ver no Mapa]({info['url']})**"
        embed.description = desc_txt
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("❌ Erro ao localizar Rashid.")

if __name__ == "__main__":
    if TOKEN:
        Thread(target=run_web_server, daemon=True).start()
        Thread(target=loop_monitoramento, daemon=True).start()
        bot.run(TOKEN)
