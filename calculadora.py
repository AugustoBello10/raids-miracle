import math
from itens import ALCHEMY_DATA, ALCHEMY_RUNES, MINING_PICKS

# ==========================================
# 🧪 ALCHEMY: GOLD CONVERTER
# ==========================================
def calcular_alchemy_gold(skill, gold_total):
    """
    Calcula quantos 'Gold Converters' são necessários para transformar
    uma quantidade de Gold, baseado na chance do Skill.
    """
    dados = ALCHEMY_DATA['converter']
    
    # Cada converter processa stacks de 100gp.
    stacks_para_sucesso = math.ceil(gold_total / 100)
    
    if stacks_para_sucesso == 0: 
        return {"chance": 0, "converters": 0, "custo": 0, "gold_processado": 0}
    
    # Chance = Base + (Fator * Skill). Teto 100%.
    chance_pct = dados['base_chance'] + (dados['skill_factor'] * skill)
    chance_pct = min(chance_pct, 100.0)
    
    # Evita divisão por zero
    chance_decimal = max(chance_pct / 100.0, 0.0001)
    
    # Quantas tentativas (cliques) em média para conseguir o sucesso nas stacks
    total_cliques_necessarios = math.ceil(stacks_para_sucesso / chance_decimal)
    
    # Quantas ferramentas precisa comprar (cada uma tem X cargas)
    qtd_ferramentas = math.ceil(total_cliques_necessarios / dados['charges'])
    custo_total = qtd_ferramentas * dados['cost']

    return { 
        "chance": round(chance_pct, 2), 
        "converters": qtd_ferramentas, 
        "custo": custo_total, 
        "gold_processado": gold_total 
    }

# ==========================================
# ✨ ALCHEMY: ENCHANT WEAPONS
# ==========================================
def calcular_alchemy_enchant(skill, crystal_base_chance):
    """
    Calcula a chance real de encantar uma arma usando cristais.
    Fórmula: Base do Cristal + (0.75 * Skill).
    """
    chance = crystal_base_chance + (0.75 * skill)
    chance = min(chance, 100.0)
    
    chance_decimal = max(chance / 100.0, 0.01)
    estimativa_para_sucesso = 1 / chance_decimal
    
    return { 
        "chance_real": round(chance, 2), 
        "qtd_media": round(estimativa_para_sucesso, 1) 
    }

# ==========================================
# 💎 ALCHEMY: RUNE OVERCHARGE
# ==========================================
def calcular_alchemy_rune(skill, rune_name):
    """
    Calcula a chance de duplicar (Overcharge) uma runa.
    Verifica se tem skill mínimo e profissão.
    """
    rune_info = ALCHEMY_RUNES.get(rune_name)
    if not rune_info: return None
    
    if skill < rune_info['min']:
        return { "possivel": False, "min_skill": rune_info['min'], "chance": 0.0, "pro": rune_info['pro'] }
    
    chance = rune_info['base'] + (0.2 * skill)
    chance = min(chance, 100.0)
    
    return { 
        "possivel": True, 
        "min_skill": rune_info['min'], 
        "chance": round(chance, 2), 
        "pro": rune_info['pro'] 
    }

# ==========================================
# ⚔️ SKILL TRAINING CALCULATOR
# ==========================================
def calcular_tempo_skill(vocacao, tipo_skill, atual, pct_atual, alvo, intervalo_ataque=2.0):
    """
    Calcula o tempo estimado para treinar skills no Tibia (Fórmula Clássica).
    """
    vocacao = vocacao.lower()
    tipo_skill = tipo_skill.lower()
    
    CONSTANTES = { 
        'knight': {'melee': 50, 'distance': 140, 'shielding': 100}, 
        'paladin': {'melee': 120, 'distance': 25, 'shielding': 100}, 
        'druid': {'melee': 200, 'distance': 200, 'shielding': 100}, 
        'sorcerer': {'melee': 200, 'distance': 200, 'shielding': 100} 
    }
    
    try: A = CONSTANTES[vocacao][tipo_skill]
    except KeyError: A = 50 
    
    B = 1.1
    hits_totais = 0
    
    for level in range(atual, alvo):
        hits_nivel = A * (math.pow(B, (level - 10)))
        if level == atual: hits_totais += hits_nivel * (1 - (pct_atual / 100.0))
        else: hits_totais += hits_nivel
        
    segundos_totais = hits_totais * intervalo_ataque
    
    dias = int(segundos_totais // 86400)
    restante = segundos_totais % 86400
    horas = int(restante // 3600)
    restante %= 3600
    minutos = int(restante // 60)
    segundos = int(restante % 60)
    
    return { 
        "dias": dias, "horas": horas, "minutos": minutos, "segundos": segundos, 
        "hits": int(hits_totais) 
    }

# ==========================================
# 🔨 CRAFTING CALCULATOR
# ==========================================
def calcular_crafting_detalhado(skill_atual, multiplicador, ingredientes, quantidade_desejada=1):
    """
    Calcula a chance de sucesso no Crafting baseado no multiplicador do item.
    """
    chance_real = 10 + ((skill_atual - 10) * multiplicador)
    chance_exibicao = min(chance_real, 100)
    
    # Cálculo simples de custo (se houver ingredientes passados)
    chance_decimal = max(chance_exibicao / 100, 0.01)
    tentativas = quantidade_desejada / chance_decimal
    
    mat_totais = {}
    custo_total = 0
    
    for nome, dados in ingredientes.items():
        if dados.get('consome_na_falha', True): 
            qtd = round(tentativas * dados['qtd'], 2)
        else: 
            qtd = dados['qtd'] * quantidade_desejada
            
        mat_totais[nome] = qtd
        custo_total += qtd * dados['preco']
        
    return { 
        "chance_sucesso": chance_exibicao, 
        "tentativas_para_meta": round(tentativas, 1), 
        "materiais_necessarios": mat_totais, 
        "custo_total": round(custo_total, 2) 
    }

# ==========================================
# 🤝 PARTY SHARE CALCULATOR
# ==========================================
def calcular_party_range(level):
    """
    Regra Tibia: Level mais baixo deve ser >= 2/3 do mais alto.
    """
    min_share = math.floor(level * (2/3))
    max_share = math.floor(level * 1.5)
    return min_share, max_share

# ==========================================
# ⛏️ MINING CALCULATOR (MIRACLE 7.4)
# ==========================================
def calcular_mining(skill, pick_name):
    """
    Calcula as chances de mineração baseadas na wiki do Miracle.
    
    1. Break Chance (Quebrar a rocha):
       Base 10% + 0.597% por skill (após skill 10). Teto 50% (Skill 77).
       Bônus da picareta é SOMADO.
       
    2. Collect Chance (Coletar item):
       Minerals: 2% + 0.1% * Skill
       Fragments: 0.5% + 0.025% * Skill
       Bônus da picareta é MULTIPLICADO no final.
    """
    pick_stats = MINING_PICKS.get(pick_name, MINING_PICKS["Pick (Normal)"])
    
    # --- 1. Chance de Quebrar (Break) ---
    if skill < 10:
        base_break = 10.0
    elif skill >= 77:
        base_break = 50.0
    else:
        base_break = 10 + (0.597 * (skill - 10))
    
    # Bônus da picareta soma direto na porcentagem
    final_break = base_break + pick_stats['bonus_break']
    final_break = min(final_break, 100.0)

    # --- 2. Chance de Coletar (Collect) ---
    # Minerais Comuns
    base_min = 2 + (0.1 * skill)
    # Bônus da picareta multiplica a chance (ex: +25% vira * 1.25)
    final_min = base_min * (1 + pick_stats['bonus_collect'])
    
    # Fragmentos Raros
    base_frag = 0.5 + (0.025 * skill)
    final_frag = base_frag * (1 + pick_stats['bonus_collect'])

    return {
        "break_chance": round(final_break, 2),
        "minerals_chance": round(final_min, 2),
        "fragments_chance": round(final_frag, 2),
        "pick_used": pick_name
    }
