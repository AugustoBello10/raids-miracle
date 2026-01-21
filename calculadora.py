# calculadora.py

# ... (Mantenha imports e outras funções iguais) ...
from itens import ALCHEMY_DATA, ALCHEMY_RUNES # Certifique-se que o import está assim

# --- ALCHEMY: GOLD CONVERSION (LÓGICA CORRIGIDA) ---
def calcular_alchemy_gold(skill, gold_total):
    """
    Calcula quantos converters precisa baseado no total de ouro.
    1 Clique = Converte 100gp (1 stack).
    1 Converter = 100 Cargas.
    Logo, 1 Converter processa 10.000 gp.
    """
    dados = ALCHEMY_DATA['converter']
    
    # Capacidade de processamento de UM converter (GP)
    # Ex: 100 cargas * 100 gp por clique = 10.000 gp
    gp_por_converter = dados['charges'] * 100 
    
    # Quantos converters precisa?
    qtd_ferramentas = math.ceil(gold_total / gp_por_converter)
    
    # Custo total
    custo_total = qtd_ferramentas * dados['cost']
    
    # Chance (Informativa)
    chance = dados['base_chance'] + (dados['skill_factor'] * skill)
    chance = min(chance, 100.0)
    
    return {
        "chance": round(chance, 2),
        "converters": qtd_ferramentas,
        "custo": custo_total,
        "gold_processado": gold_total
    }

# ... (Mantenha calcular_alchemy_enchant, calcular_alchemy_rune e skill/crafting iguais) ...
