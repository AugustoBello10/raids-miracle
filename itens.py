# itens.py

RECEITAS = {
    # --- RELÍQUIAS ---
    "Giant Ruby": {
        "multiplicador": 5,
        "ingredientes": {"Small Ruby": 10},
        "perde_na_falha": True
    },
    "Giant Emerald": {
        "multiplicador": 5,
        "ingredientes": {"Small Emerald": 10},
        "perde_na_falha": True
    },
    "Giant Sapphire": {
        "multiplicador": 5,
        "ingredientes": {"Small Sapphire": 10},
        "perde_na_falha": True
    },
    "Giant Amethyst": {
        "multiplicador": 5,
        "ingredientes": {"Small Amethyst": 10},
        "perde_na_falha": True
    },

    # --- FERRAMENTAS ---
    "Modified Pick": {
        "multiplicador": 2,
        "ingredientes": {"Pick": 1, "Steel": 5},
        "perde_na_falha": True
    },
    "Advanced Pick": {
        "multiplicador": 1.5,
        "ingredientes": {"Pick": 1, "Steel": 10},
        "perde_na_falha": True
    },
    "Enhanced Pick": {
        "multiplicador": 1,
        "ingredientes": {"Pick": 1, "Steel": 20},
        "perde_na_falha": True
    },

    # --- RUNAS MÍSTICAS (Regra: Onyx não se perde) ---
    "Ember Rune": {
        "multiplicador": 1,
        "ingredientes": {"Ember Fragment": 5, "Pulverized Ore": 3, "Onyx": 1},
        "nao_perde": ["Onyx"] # Regra especial: Onyx não gasta na falha
    },
    "Protector Rune": {
        "multiplicador": 1,
        "ingredientes": {"Protector Fragment": 5, "Pulverized Ore": 3, "Onyx": 1},
        "nao_perde": ["Onyx"]
    },
    "Obsidian Rune": {
        "multiplicador": 1,
        "ingredientes": {"Obsidian Fragment": 5, "Pulverized Ore": 3, "Onyx": 1},
        "nao_perde": ["Onyx"]
    },
    "Aegis Rune": {
        "multiplicador": 1,
        "ingredientes": {"Aegis Fragment": 5, "Pulverized Ore": 3, "Onyx": 1},
        "nao_perde": ["Onyx"]
    },
    "Astral Rune": {
        "multiplicador": 1,
        "ingredientes": {"Astral Fragment": 5, "Pulverized Ore": 3, "Onyx": 1},
        "nao_perde": ["Onyx"]
    },
    "Molten Rune": {
        "multiplicador": 1,
        "ingredientes": {"Molten Fragment": 5, "Pulverized Ore": 3, "Onyx": 1},
        "nao_perde": ["Onyx"]
    },

    # --- VARAS DE PESCA ---
    "Reinforced Rod": {
        "multiplicador": 2,
        "ingredientes": {"Fishing Rod": 1, "Steel": 5},
        "perde_na_falha": True
    },
    "Engineered Fishing Rod": {
        "multiplicador": 1.5,
        "ingredientes": {"Fishing Rod": 1, "Steel": 10, "Draconian Steel": 1},
        "perde_na_falha": True
    },
    "Volcanic Fishing Rod": {
        "multiplicador": 1,
        "ingredientes": {
            "Fishing Rod": 1, 
            "Steel": 20, 
            "Glimmering Soil": 10, 
            "Draconian Steel": 5, 
            "Hell Steel": 3
        },
        "perde_na_falha": True
    },
    "Golden Fishing Rod": {
        "multiplicador": 0.5,
        "ingredientes": {
            "Fishing Rod": 1, 
            "Steel": 40, 
            "Draconian Steel": 10, 
            "Gold Ingot": 3, 
            "Hell Steel": 3
        },
        "perde_na_falha": True
    },

    # --- OUTROS ---
    "Fiery Stone": {
        "multiplicador": 0.5,
        "ingredientes": {"Glimmering Soil": 5},
        "perde_na_falha": True
    },
    "10x Steel Bolts": {
        "multiplicador": 0.4,
        "ingredientes": {"Bolt": 5, "Steel": 1, "Natural Soil": 1},
        "perde_na_falha": True
    },
    "Diamond Knife": {
        "multiplicador": 1,
        "ingredientes": {"Combat Knife": 1, "Small Diamond": 10, "Hell Steel": 5},
        "perde_na_falha": True
    }
}