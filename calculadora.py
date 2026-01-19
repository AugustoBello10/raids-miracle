import math

# --- LÓGICA DE SKILLS (TIBIA 7.4) ---
def calcular_tempo_skill(vocacao, tipo_skill, atual, pct_atual, alvo, intervalo_ataque=2.0):
    """
    Calcula tempo de treino considerando a % atual e velocidade da arma.
    """
    vocacao = vocacao.lower()
    tipo_skill = tipo_skill.lower()
    
    # CONSTANTES DE DIFICULDADE (A)
    # Quanto maior, mais difícil subir.
    CONSTANTES = {
        'knight':    {'melee': 50,  'distance': 140, 'shielding': 100},
        'paladin':   {'melee': 120, 'distance': 25,  'shielding': 100},
        'druid':     {'melee': 200, 'distance': 200, 'shielding': 100},
        'sorcerer':  {'melee': 200, 'distance': 200, 'shielding': 100}
    }
    
    # Tenta pegar a constante. Se a combinação não existir (ex: Druid melee), usa o padrão 50.
    try:
        A = CONSTANTES[vocacao][tipo_skill]
    except KeyError:
        A = 50 

    B = 1.1 # Constante exponencial padrão
    
    hits_totais = 0
    
    for level in range(atual, alvo):
        # Hits para fechar o nível inteiro
        hits_nivel = A * (math.pow(B, (level - 10)))
        
        if level == atual:
            # Desconta o que já foi treinado (Ex: Se tem 20%, falta 80%)
            fator_restante = 1 - (pct_atual / 100.0)
            hits_totais += hits_nivel * fator_restante
        else:
            hits_totais += hits_nivel
            
    # Converte Hits em Tempo (Segundos)
    segundos_totais = hits_totais * intervalo_ataque
    
    # Formatação (Dias, Horas, Minutos, Segundos)
    dias = int(segundos_totais // 86400)
    restante = segundos_totais % 86400
    horas = int(restante // 3600)
    restante %= 3600
    minutos = int(restante // 60)
    segundos = int(restante % 60)
    
    return {
        "dias": dias,
        "horas": horas,
        "minutos": minutos,
        "segundos": segundos,
        "hits": int(hits_totais)
    }

# --- LÓGICA DE CRAFTING (MANTIDA) ---
def calcular_crafting_detalhado(skill_atual, multiplicador, ingredientes, quantidade_desejada=1):
    chance_real = 10 + ((skill_atual - 10) * multiplicador)
    chance_exibicao = min(chance_real, 100)
    chance_decimal = max(chance_exibicao / 100, 0.01)
    tentativas = quantidade_desejada / chance_decimal
    
    materiais_totais = {}
    custo_total = 0
    
    for nome, dados in ingredientes.items():
        if dados.get('consome_na_falha', True):
            qtd = round(tentativas * dados['qtd'], 2)
        else:
            qtd = dados['qtd'] * quantidade_desejada
        materiais_totais[nome] = qtd
        custo_total += qtd * dados['preco']

    return {
        "chance_sucesso": chance_exibicao,
        "tentativas_para_meta": round(tentativas, 1),
        "materiais_necessarios": materiais_totais,
        "custo_total": round(custo_total, 2)
    }
