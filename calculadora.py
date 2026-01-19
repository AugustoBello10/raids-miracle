# calculadora.py

def calcular_crafting_detalhado(skill_atual, multiplicador, ingredientes, quantidade_desejada=1):
    """
    Calcula chance de sucesso, materiais e custos para o Miracle 7.4.
    O dicionário 'ingredientes' deve conter: {'Item': {'qtd': x, 'preco': y, 'consome_na_falha': bool}}
    """
    
    # 1. Fórmula original do Miracle 7.4
    chance_real = 10 + ((skill_atual - 10) * multiplicador)
    
    # 2. CAP de 100% para exibição e cálculos (Não existe mais de 100% de chance lógica)
    chance_exibicao = min(chance_real, 100)
    
    # 3. Cálculo de Tentativas Necessárias
    # Se a chance for 100%, tentativas = quantidade_desejada.
    # Se for 50%, tentativas = quantidade_desejada * 2.
    chance_decimal = max(chance_exibicao / 100, 0.01) 
    tentativas_estimadas = quantidade_desejada / chance_decimal
    
    materiais_totais = {}
    custo_total_estimado = 0
    
    # 4. Processamento dos Ingredientes (Integrando a alteração sugerida)
    for nome_item, dados in ingredientes.items():
        # Verificação da regra de consumo (Ex: Onyx não se perde na falha)
        if dados.get('consome_na_falha', True):
            # Itens normais: quantidade multiplicada pela média de tentativas
            qtd_total = round(tentativas_estimadas * dados['qtd'], 2)
        else:
            # Itens especiais (Onyx): você só precisa da quantidade da receita original uma única vez
            qtd_total = dados['qtd']
            
        materiais_totais[nome_item] = qtd_total
        
        # O preço 'y' aqui será o valor que o usuário inseriu no Discord
        custo_total_estimado += qtd_total * dados['preco']

    return {
        "chance_sucesso": chance_exibicao,
        "tentativas_para_meta": round(tentativas_estimadas, 1),
        "materiais_necessarios": materiais_totais,
        "custo_total": round(custo_total_estimado, 2)
    }