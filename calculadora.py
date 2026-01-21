import math
from itens import ALCHEMY_DATA, ALCHEMY_RUNES

# --- ALCHEMY: RUNE OVERCHARGING (NOVO) ---
def calcular_alchemy_rune(skill, rune_name):
    """
    Calcula chance de duplicar runa.
    Formula: Base + (0.2% * Skill)
    """
    rune_info = ALCHEMY_RUNES.get(rune_name)
    if not rune_info: return None
    
    # Verifica Skill Minimo
    if skill < rune_info['min']:
        return {
            "possivel": False,
            "min_skill": rune_info['min'],
            "chance": 0.0,
            "pro": rune_info['pro']
        }
    
    # Calcula Chance
    chance = rune_info['base'] + (0.2 * skill)
    chance = min(chance, 100.0) # Max 100%
    
    return {
        "possivel": True,
        "min_skill": rune_info['min'],
        "chance": round(chance, 2),
        "pro": rune_info['pro'] # True se precisa de Alchemist
    }

# --- ALCHEMY: GOLD & ENCHANT (MANTIDOS) ---
def calcular_alchemy_gold(skill, tentativas):
    dados = ALCHEMY_DATA['converter']
    chance = dados['base_chance'] + (dados['skill_factor'] * skill)
    chance = min(chance, 100.0)
    qtd_ferramentas = math.ceil(tentativas / dados['charges'])
    custo_total = qtd_ferramentas * dados['cost']
    return { "chance": round(chance, 2), "converters": qtd_ferramentas, "custo": custo_total, "charges_total": tentativas }

def calcular_alchemy_enchant(skill, crystal_base_chance):
    chance = crystal_base_chance + (0.75 * skill)
    chance = min(chance, 100.0)
    chance_decimal = max(chance / 100.0, 0.01)
    estimativa_para_sucesso = 1 / chance_decimal
    return { "chance_real": round(chance, 2), "qtd_media": round(estimativa_para_sucesso, 1) }

# --- SKILLS E CRAFTING (MANTIDOS IGUAIS) ---
def calcular_tempo_skill(vocacao, tipo_skill, atual, pct_atual, alvo, intervalo_ataque=2.0):
    vocacao = vocacao.lower(); tipo_skill = tipo_skill.lower()
    CONSTANTES = { 'knight': {'melee': 50, 'distance': 140, 'shielding': 100}, 'paladin': {'melee': 120, 'distance': 25, 'shielding': 100}, 'druid': {'melee': 200, 'distance': 200, 'shielding': 100}, 'sorcerer': {'melee': 200, 'distance': 200, 'shielding': 100} }
    try: A = CONSTANTES[vocacao][tipo_skill]
    except KeyError: A = 50 
    B = 1.1; hits_totais = 0
    for level in range(atual, alvo):
        hits_nivel = A * (math.pow(B, (level - 10)))
        if level == atual: hits_totais += hits_nivel * (1 - (pct_atual / 100.0))
        else: hits_totais += hits_nivel
    segundos_totais = hits_totais * intervalo_ataque
    dias = int(segundos_totais // 86400); restante = segundos_totais % 86400
    horas = int(restante // 3600); restante %= 3600
    minutos = int(restante // 60); segundos = int(restante % 60)
    return { "dias": dias, "horas": horas, "minutos": minutos, "segundos": segundos, "hits": int(hits_totais) }

def calcular_crafting_detalhado(skill_atual, multiplicador, ingredientes, quantidade_desejada=1):
    chance_real = 10 + ((skill_atual - 10) * multiplicador)
    chance_exibicao = min(chance_real, 100)
    chance_decimal = max(chance_exibicao / 100, 0.01)
    tentativas = quantidade_desejada / chance_decimal
    mat_totais = {}
    custo_total = 0
    for nome, dados in ingredientes.items():
        if dados.get('consome_na_falha', True): qtd = round(tentativas * dados['qtd'], 2)
        else: qtd = dados['qtd'] * quantidade_desejada
        mat_totais[nome] = qtd
        custo_total += qtd * dados['preco']
    return { "chance_sucesso": chance_exibicao, "tentativas_para_meta": round(tentativas, 1), "materiais_necessarios": mat_totais, "custo_total": round(custo_total, 2) }
