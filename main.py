# ... (Imports e configurações iniciais iguais) ...
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
from calculadora import calcular_crafting_detalhado, calcular_tempo_skill
from itens import RECEITAS, ESTRUTURA_MENU, ARMAS_TREINO
from idiomas import TEXTOS

TOKEN = os.environ.get('DISCORD_TOKEN') 
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')

URL_RAIDS = "https://miracle74.com/?subtopic=raids"
FUSO_BRASILIA = pytz.timezone('America/Sao_Paulo')

app = Flask('')
@app.route('/')
def home(): return "Bot Bellão (Raids + Skills V8) Online"
def run_web_server(): app.run(host='0.0.0.0', port=8080)

# --- RAIDS (MANTIDO) ---
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
# ⚔️ SISTEMA DE SKILLS
# ==========================================

class DualSkillModal(ui.Modal):
    def __init__(self, vocacao, tipo_melee, tier_arma, lang):
        self.lang = lang; self.vocacao = vocacao; self.tipo_melee = tipo_melee
        self.tier = tier_arma # Armazena o nome exato do tier selecionado
        
        # Lógica de seleção de stats
        if "Spark" in self.tier:
            w_key = next((k for k in ARMAS_TREINO if "Spark" in k and "Weapon" in k), None)
            s_key = next((k for k in ARMAS_TREINO if "Spark" in k and "Shield" in k), None)
        elif "Lightning" in self.tier:
            w_key = next((k for k in ARMAS_TREINO if "Lightning" in k and "Weapon" in k), None)
            s_key = next((k for k in ARMAS_TREINO if "Lightning" in k and "Shield" in k), None)
        elif "Inferno" in self.tier:
            w_key = next((k for k in ARMAS_TREINO if "Inferno" in k and "Weapon" in k), None)
            s_key = next((k for k in ARMAS_TREINO if "Inferno" in k and "Shield" in k), None)
        elif "-5%" in self.tier:
            w_key = "Weapon (-5% Atk Speed)"
            s_key = "Normal / Nenhuma" # Shield normal
        elif "-6%" in self.tier:
            w_key = "Weapon (-6% Atk Speed)"
            s_key = "Normal / Nenhuma" # Shield normal
        else: # Normal
            w_key = "Normal / Nenhuma"
            s_key = "Normal / Nenhuma"

        # Ajuste para Spear se for Distance
        if tipo_melee == 'distance' and "Spark" in str(w_key):
             w_key = next((k for k in ARMAS_TREINO if "Spark" in k and "Spear" in k), w_key)
        # (Repetir para Lightning/Inferno se Spear existir, senão usa Weapon mesmo ou Normal)

        self.w_stats = ARMAS_TREINO.get(w_key, ARMAS_TREINO["Normal / Nenhuma"])
        self.s_stats = ARMAS_TREINO.get(s_key, ARMAS_TREINO["Normal / Nenhuma"])

        t = TEXTOS[lang]
        super().__init__(title=f"{vocacao.capitalize()} (Treino Duplo)")
        self.add_item(ui.TextInput(label=f"{tipo_melee.capitalize()} (Atual - Alvo)", placeholder="Ex: 80-85", custom_id="melee_vals"))
        self.add_item(ui.TextInput(label=f"{tipo_melee.capitalize()} % (Já treinado)", placeholder="Ex: 50 (50%)", custom_id="melee_pct", max_length=3))
        self.add_item(ui.TextInput(label="Shielding (Atual - Alvo)", placeholder="Ex: 75-80", custom_id="shield_vals"))
        self.add_item(ui.TextInput(label="Shielding % (Já treinado)", placeholder="Ex: 0 (0%)", custom_id="shield_pct", max_length=3))
        self.add_item(ui.TextInput(label="Preço Unit. Arma (Opcional)", placeholder="Ex: 150000", required=False, custom_id="price"))

    async def on_submit(self, interaction: discord.Interaction):
        try:
            m_curr, m_target = map(int, self.children[0].value.replace('/', '-').split('-'))
            m_pct = float(self.children[1].value.replace(',', '.'))
            s_curr, s_target = map(int, self.children[2].value.replace('/', '-').split('-'))
            s_pct = float(self.children[3].value.replace(',', '.'))
            price_unit = int(self.children[4].value.replace('.', '').replace('k', '000')) if self.children[4].value else 0

            res_m = calcular_tempo_skill(self.vocacao, self.tipo_melee, m_curr, m_pct, m_target, self.w_stats['speed'])
            res_s = calcular_tempo_skill(self.vocacao, "shielding", s_curr, s_pct, s_target, self.s_stats['speed'])
            
            # Custo: Se for infinita (charges > 10 milhões), considera 1 unidade
            qtd_weapons = math.ceil(res_m['hits'] / self.w_stats['charges'])
            if self.w_stats['charges'] > 999999: qtd_weapons = 1
            
            qtd_shields = math.ceil(res_s['hits'] / self.s_stats['charges'])
            if self.s_stats['charges'] > 999999: qtd_shields = 1
            
            total_gp = (qtd_weapons * price_unit) + (qtd_shields * price_unit)
            # Se for arma especial mas shield normal, cobra so arma (ajuste logico)
            if "Normal" in str(self.s_stats['charges']): total_gp = qtd_weapons * price_unit

            embed = discord.Embed(title=f"⚔️ Treino Duplo: {self.tier.split('(')[0]}", color=discord.Color.purple())
            
            t_txt = f"{res_m['dias']}d {res_m['horas']}h {res_m['minutos']}m"
            w_val = f"{qtd_weapons}x" if self.w_stats['charges'] < 999999 else "1x (Eterna)"
            
            s_txt = f"{res_s['dias']}d {res_s['horas']}h {res_s['minutos']}m"
            s_val = f"{qtd_shields}x" if self.s_stats['charges'] < 999999 else "—"

            embed.add_field(name=f"⚔️ {self.tipo_melee.capitalize()}: {m_curr}➝{m_target}", value=f"⏱️ {t_txt}\n📦 {w_val}", inline=True)
            embed.add_field(name=f"🛡️ Shield: {s_curr}➝{s_target}", value=f"⏱️ {s_txt}\n📦 {s_val}", inline=True)
            
            if price_unit > 0:
                embed.add_field(name="💰 Custo Estimado", value=f"{total_gp:,} gp", inline=False)
            
            embed.set_footer(text=f"Hits Totais: {res_m['hits']:,} (Atk) / {res_s['hits']:,} (Def)")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Formato inválido. Use '80-85' para niveis.", ephemeral=True)

class SingleSkillModal(ui.Modal):
    def __init__(self, vocacao, tipo_skill, arma_nome, arma_speed, arma_charges, lang):
        self.lang = lang; self.vocacao = vocacao; self.tipo_skill = tipo_skill
        self.arma_speed = arma_speed; self.arma_nome = arma_nome; self.arma_charges = arma_charges
        t = TEXTOS[lang]
        super().__init__(title=f"{vocacao} - {tipo_skill}")
        self.add_item(ui.TextInput(label="Skill Atual", placeholder="Ex: 80", custom_id="c"))
        self.add_item(ui.TextInput(label="% Atual", placeholder="Ex: 50", custom_id="p"))
        self.add_item(ui.TextInput(label="Skill Desejado", placeholder="Ex: 85", custom_id="t"))
        req_price = True if "Normal" not in arma_nome else False
        lbl_price = "Preço Arma (Opcional)" if req_price else "Preço (Não se aplica)"
        self.add_item(ui.TextInput(label=lbl_price, required=False, placeholder="Ex: 10000", custom_id="pr"))

    async def on_submit(self, interaction: discord.Interaction):
        try:
            curr = int(self.children[0].value); pct = float(self.children[1].value.replace(',', '.'))
            target = int(self.children[2].value)
            price = int(self.children[3].value.replace('.', '').replace('k', '000')) if self.children[3].value and self.children[3].value[0].isdigit() else 0
            
            res = calcular_tempo_skill(self.vocacao, self.tipo_skill, curr, pct, target, self.arma_speed)
            
            # Custo
            qtd = math.ceil(res['hits'] / self.arma_charges)
            if self.arma_charges > 999999: qtd = 1
            cost = qtd * price
            
            t = TEXTOS[self.lang]
            embed = discord.Embed(title=f"⚔️ {self.vocacao.capitalize()} - {self.tipo_skill.capitalize()}", color=discord.Color.red())
            time_str = f"{res['dias']}d {res['horas']}h {res['minutos']}m"
            
            embed.add_field(name=t['time_est'], value=f"⏱️ **{time_str}**", inline=False)
            
            r_val = f"Hits: {res['hits']:,}"
            if "Normal" not in self.arma_nome:
                suffix = "(Eterna)" if self.arma_charges > 999999 else self.arma_nome
                r_val += f"\nQtd: **{qtd}x** {suffix}"
                if cost > 0: embed.add_field(name="💰 Custo", value=f"{cost:,} gp", inline=True)
            
            embed.add_field(name="📦 Recursos", value=r_val, inline=True)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except: await interaction.response.send_message("❌ Erro", ephemeral=True)

class WeaponSelect(ui.Select):
    def __init__(self, vocacao, tipo_skill, lang):
        self.vocacao = vocacao; self.tipo_skill = tipo_skill; self.lang = lang
        opts = []
        # Lista com as novas opções
        tiers = [
            "Normal / Nenhuma", 
            "Weapon (-5% Atk Speed)", 
            "Weapon (-6% Atk Speed)",
            "Spark Weapon/Shield", 
            "Lightning Weapon/Shield", 
            "Inferno Weapon/Shield"
        ]
        for t in tiers:
            # Value é o identificador que usaremos no callback
            val = t
            if "Spark" in t: val = "Spark"
            elif "Lightning" in t: val = "Lightning"
            elif "Inferno" in t: val = "Inferno"
            
            opts.append(discord.SelectOption(label=t, value=val))
        
        super().__init__(placeholder="Escolha o Tier da Arma...", options=opts)

    async def callback(self, interaction: discord.Interaction):
        tier = self.values[0] # Pode ser "Normal / Nenhuma", "-5%...", "Spark", etc.
        
        if self.tipo_skill == "dual_melee":
            await interaction.response.send_modal(DualSkillModal(self.vocacao, "melee", tier, self.lang))
        elif self.tipo_skill == "dual_dist":
            await interaction.response.send_modal(DualSkillModal(self.vocacao, "distance", tier, self.lang))
        else:
            # Single Mode
            stats = ARMAS_TREINO["Normal / Nenhuma"]
            nome_arma = tier
            
            # Lógica para achar os stats corretos
            # Se for tier simples (Spark/Lightning/Inferno)
            if tier in ["Spark", "Lightning", "Inferno"]:
                for k, v in ARMAS_TREINO.items():
                    if tier in k:
                        if "shield" in self.tipo_skill and "Shield" in k:
                            stats = v; nome_arma = k; break
                        elif "shield" not in self.tipo_skill and "Weapon" in k: 
                            stats = v; nome_arma = k; break
            else:
                # Se for Normal ou -5%/-6%, o nome no dict é igual ao value
                stats = ARMAS_TREINO.get(tier, ARMAS_TREINO["Normal / Nenhuma"])
            
            await interaction.response.send_modal(SingleSkillModal(self.vocacao, self.tipo_skill, nome_arma, stats['speed'], stats['charges'], self.lang))

# ... (RESTANTE DO CÓDIGO IGUAL: SkillTypeSelect, VocationSelect, Crafting, etc) ...
class SkillTypeSelect(ui.Select):
    def __init__(self, vocacao, lang):
        self.vocacao = vocacao; self.lang = lang
        opts = [
            discord.SelectOption(label="⚔️ Melee + Shield (Juntos)", value="dual_melee", description="Calcula os dois ao mesmo tempo"),
            discord.SelectOption(label="🏹 Distance + Shield (Juntos)", value="dual_dist", description="Calcula Spear + Shield"),
            discord.SelectOption(label="⚔️ Apenas Melee", value="melee"),
            discord.SelectOption(label="🛡️ Apenas Shielding", value="shielding"),
            discord.SelectOption(label="🏹 Apenas Distance", value="distance")
        ]
        super().__init__(placeholder="Qual treino?", options=opts)

    async def callback(self, interaction: discord.Interaction):
        v = ui.View(); v.add_item(WeaponSelect(self.vocacao, self.values[0], self.lang))
        await interaction.response.edit_message(content=f"🛠️ Configurando **{self.values[0]}**. Qual arma?", view=v)

class VocationSelect(ui.Select):
    def __init__(self, lang):
        self.lang = lang
        opts = [discord.SelectOption(label="🛡️ Knight", value="knight"), discord.SelectOption(label="🏹 Paladin", value="paladin"), discord.SelectOption(label="🔥 Mage", value="druid")]
        super().__init__(placeholder="Vocação...", options=opts)
    async def callback(self, interaction: discord.Interaction):
        v = ui.View(); v.add_item(SkillTypeSelect(self.values[0], self.lang))
        await interaction.response.send_message("Tipo de Treino:", view=v, ephemeral=True)

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

class ModeSelect(ui.View):
    def __init__(self, lang):
        super().__init__(); self.lang = lang
    
    @ui.button(label="🔨 Crafting", style=discord.ButtonStyle.primary)
    async def craft(self, interaction: discord.Interaction, button: ui.Button):
        v = ui.View(); v.add_item(CategorySelect(self.lang))
        await interaction.response.send_message(TEXTOS[self.lang]['select_cat'], view=v, ephemeral=True)

    @ui.button(label="🧪 Alchemy", style=discord.ButtonStyle.success, disabled=True)
    async def alchemy(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("Coming soon...", ephemeral=True)

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
        v.children[2].label = t['btn_skill']
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
