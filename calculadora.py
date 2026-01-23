import math
from itens import ALCHEMY_DATA, ALCHEMY_RUNES, MINING_PICKS

def calcular_alchemy_gold(skill, gold_total):
    dados = ALCHEMY_DATA['converter']
    stacks = math.ceil(gold_total / 100)
    if stacks == 0: return {"chance": 0, "converters": 0, "custo": 0}
    chance = min(dados['base_chance'] + (dados['skill_factor'] * skill), 100.0)
    chance_dec = max(chance / 100.0, 0.0001)
    tentativas = math.ceil(stacks / chance_dec)
    ferramentas = math.ceil(tentativas / dados['charges'])
    return { "chance": round(chance, 2), "converters": ferramentas, "custo": ferramentas * dados['cost'] }

def calcular_tempo_skill(vocacao, tipo_skill, atual, pct_atual, alvo, intervalo_ataque=2.0):
    vocacao = vocacao.lower(); tipo_skill = tipo_skill.lower()
    CONSTANTES = { 'knight': {'melee': 50, 'distance': 140, 'shielding': 100}, 'paladin': {'melee': 120, 'distance': 25, 'shielding': 100}, 'druid': {'melee': 200, 'distance': 200, 'shielding': 100}, 'sorcerer': {'melee': 200, 'distance': 200, 'shielding': 100} }
    try: A = CONSTANTES[vocacao][tipo_skill]
    except KeyError: A = 50 
    hits_totais = 0
    for level in range(atual, alvo):
        hits_nivel = A * (math.pow(1.1, (level - 10)))
        if level == atual: hits_totais += hits_nivel * (1 - (pct_atual / 100.0))
        else: hits_totais += hits_nivel
    seg = hits_totais * intervalo_ataque
    return { "dias": int(seg//86400), "horas": int((seg%86400)//3600), "minutos": int((seg%3600)//60), "hits": int(hits_totais) }

def calcular_crafting_detalhado(skill, mult, ingredientes, qtd=1):
    chance = 10 + ((skill - 10) * mult)
    chance = max(0.1, min(chance, 100))
    tentativas = qtd / (chance / 100.0)
    mat_totais = {}
    custo_total = 0
    for nome, dados in ingredientes.items():
        if dados.get('consome_na_falha', True): q_nec = round(tentativas * dados['qtd'], 2)
        else: q_nec = dados['qtd'] * qtd
        mat_totais[nome] = q_nec
        custo_total += q_nec * dados.get('preco', 0)
    return { "chance_sucesso": round(chance, 2), "tentativas_para_meta": round(tentativas, 1), "materiais_necessarios": mat_totais, "custo_total": custo_total }

def calcular_mining(skill, pick_name):
    pick = MINING_PICKS.get(pick_name, MINING_PICKS["Pick (Normal)"])
    base_break = 10 + (0.597 * (skill - 10)) if 10 <= skill < 77 else (50 if skill >= 77 else 10)
    final_break = min(base_break + pick['bonus_break'], 100.0)
    final_min = (2 + (0.1 * skill)) * (1 + pick['bonus_collect'])
    final_frag = (0.5 + (0.025 * skill)) * (1 + pick['bonus_collect'])
    return { "break_chance": round(final_break, 2), "minerals_chance": round(final_min, 2), "fragments_chance": round(final_frag, 2) }

def calcular_alchemy_enchant(skill, base):
    return { "chance_real": round(min(base + (0.75 * skill), 100.0), 2) }

def calcular_alchemy_rune(skill, rune_name):
    info = ALCHEMY_RUNES.get(rune_name)
    if not info: return {"chance": 0}
    return { "chance": round(min(info['base'] + (0.2 * skill), 100.0), 2) }

def calcular_party_range(level):
    return math.floor(level * 0.66), math.floor(level * 1.5)
