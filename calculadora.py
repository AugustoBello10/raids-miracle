import math
from itens import ALCHEMY_DATA, MINING_PICKS

def calcular_alchemy_gold(skill, gold_total):
    dados = ALCHEMY_DATA['converter']
    stacks = math.ceil(gold_total / 100)
    chance_pct = min(dados['base_chance'] + (dados['skill_factor'] * skill), 100.0)
    chance_dec = max(chance_pct / 100.0, 0.0001)
    converters = math.ceil((stacks / chance_dec) / dados['charges'])
    return { "chance": round(chance_pct, 2), "converters": converters }

def calcular_party_range(level):
    return math.floor(level * 0.66), math.floor(level * 1.5)

def calcular_mining(skill, pick_name):
    pick = MINING_PICKS.get(pick_name, MINING_PICKS["Pick (Normal)"])
    base_break = 10 + (0.597 * (skill - 10)) if 10 <= skill < 77 else (50 if skill >= 77 else 10)
    final_break = min(base_break + pick['bonus_break'], 100.0)
    final_min = (2 + (0.1 * skill)) * (1 + pick['bonus_collect'])
    final_frag = (0.5 + (0.025 * skill)) * (1 + pick['bonus_collect'])
    return { "break_chance": round(final_break, 2), "minerals_chance": round(final_min, 2), "fragments_chance": round(final_frag, 2) }

def calcular_crafting_detalhado(skill, mult, ings, qtd):
    chance = min(10 + ((skill - 10) * mult), 100)
    return { "chance_sucesso": chance }

def calcular_alchemy_enchant(skill, crystal_base_chance):
    chance = min(crystal_base_chance + (0.75 * skill), 100.0)
    return { "chance_real": round(chance, 2) }

def calcular_alchemy_rune(skill, rune_name):
    from itens import ALCHEMY_RUNES
    info = ALCHEMY_RUNES.get(rune_name)
    if not info: return {"chance": 0}
    chance = min(info['base'] + (0.2 * skill), 100.0)
    return { "chance": round(chance, 2) }
