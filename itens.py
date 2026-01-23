# itens.py - Database de Itens e Receitas

CONSTANTES_SKILLS = {
    "knight": {"melee": 50, "distance": 140, "shielding": 100},
    "paladin": {"melee": 120, "distance": 25, "shielding": 100},
    "druid": {"melee": 200, "distance": 200, "shielding": 100},
    "sorcerer": {"melee": 200, "distance": 200, "shielding": 100}
}

ALCHEMY_DATA = {
    "converter": { "charges": 100, "cost": 500, "base_chance": 10, "skill_factor": 0.2 },
    "crystals": { "Spark Crystal": {"base_chance": 20}, "Lightning Crystal": {"base_chance": 15}, "Inferno Crystal": {"base_chance": 10} }
}

ALCHEMY_RUNES = {
    "Sudden Death": {"min": 55, "base": 22.72, "pro": True}, "Explosion": {"min": 28, "base": 27.77, "pro": True},
    "Great Fireball": {"min": 22, "base": 41.66, "pro": False}, "Heavy Magic Missile": {"min": 13, "base": 71.42, "pro": False},
    "Light Magic Missile": {"min": 10, "base": 100.0, "pro": False}, "Fireball": {"min": 16, "base": 83.33, "pro": False},
    "Ultimate Healing": {"min": 22, "base": 50.0, "pro": True}, "Intense Healing": {"min": 13, "base": 83.33, "pro": False}
}

MINING_PICKS = {
    "Pick (Normal)": {"bonus_break": 0, "bonus_collect": 0.0}, "Modified Pick": {"bonus_break": 2, "bonus_collect": 0.25},
    "Advanced Pick": {"bonus_break": 4, "bonus_collect": 0.50}, "Enhanced Pick": {"bonus_break": 6, "bonus_collect": 1.00}
}

ALCHEMY_MENU_CATS = {
    "cat_atk": ["Sudden Death", "Explosion", "Great Fireball", "Heavy Magic Missile", "Light Magic Missile", "Fireball", "Ultimate Healing", "Intense Healing", "Envenom"],
    "cat_sup": ["Paralyze", "Magic Wall", "Energy Bomb", "Energy Wall", "Fire Bomb", "Fire Wall", "Poison Bomb", "Poison Wall", "Soulfire", "Animate Dead", "Convince Creature", "Chameleon", "Desintegrate", "Destroy Field"]
}

# --- LISTA MESTRA DE RECEITAS ---
RECEITAS = {
    "Giant Ruby": { "multiplicador": 5, "ingredientes": {"Small Ruby": 10}, "perde_na_falha": True },
    "Giant Emerald": { "multiplicador": 5, "ingredientes": {"Small Emerald": 10}, "perde_na_falha": True },
    "Giant Sapphire": { "multiplicador": 5, "ingredientes": {"Small Sapphire": 10}, "perde_na_falha": True },
    "Giant Amethyst": { "multiplicador": 5, "ingredientes": {"Small Amethyst": 10}, "perde_na_falha": True },
    "Modified Pick": { "multiplicador": 2, "ingredientes": {"Pick": 1, "Steel": 5}, "perde_na_falha": True },
    "Advanced Pick": { "multiplicador": 1.5, "ingredientes": {"Pick": 1, "Steel": 10}, "perde_na_falha": True },
    "Enhanced Pick": { "multiplicador": 1, "ingredientes": {"Pick": 1, "Steel": 20}, "perde_na_falha": True },
    "Diamond Knife": { "multiplicador": 1, "ingredientes": {"Combat Knife": 1, "Small Diamond": 10, "Hell Steel": 5}, "perde_na_falha": True },
    "Ember Rune": { "multiplicador": 1, "ingredientes": {"Ember Fragment": 5, "Pulverized Ore": 3, "Onyx": 1}, "nao_perde": ["Onyx"] },
    "Protector Rune": { "multiplicador": 1, "ingredientes": {"Protector Fragment": 5, "Pulverized Ore": 3, "Onyx": 1}, "nao_perde": ["Onyx"] },
    "Obsidian Rune": { "multiplicador": 1, "ingredientes": {"Obsidian Fragment": 5, "Pulverized Ore": 3, "Onyx": 1}, "nao_perde": ["Onyx"] },
    "Aegis Rune": { "multiplicador": 1, "ingredientes": {"Aegis Fragment": 5, "Pulverized Ore": 3, "Onyx": 1}, "nao_perde": ["Onyx"] },
    "Astral Rune": { "multiplicador": 1, "ingredientes": {"Astral Fragment": 5, "Pulverized Ore": 3, "Onyx": 1}, "nao_perde": ["Onyx"] },
    "Molten Rune": { "multiplicador": 1, "ingredientes": {"Molten Fragment": 5, "Pulverized Ore": 3, "Onyx": 1}, "nao_perde": ["Onyx"] },
    "Fiery Stone": { "multiplicador": 0.5, "ingredientes": {"Glimmering Soil": 5}, "perde_na_falha": True },
    "Reinforced Rod": { "multiplicador": 2, "ingredientes": {"Fishing Rod": 1, "Steel": 5}, "perde_na_falha": True },
    "Engineered Fishing Rod": { "multiplicador": 1.5, "ingredientes": {"Fishing Rod": 1, "Steel": 10, "Draconian Steel": 1}, "perde_na_falha": True },
    "Volcanic Fishing Rod": { "multiplicador": 1, "ingredientes": { "Fishing Rod": 1, "Steel": 20, "Glimmering Soil": 10, "Draconian Steel": 5, "Hell Steel": 3 }, "perde_na_falha": True },
    "Golden Fishing Rod": { "multiplicador": 0.5, "ingredientes": { "Fishing Rod": 1, "Steel": 40, "Draconian Steel": 10, "Gold Ingot": 3, "Hell Steel": 3 }, "perde_na_falha": True },
    "10x Steel Bolts": { "multiplicador": 0.4, "ingredientes": {"Bolt": 5, "Steel": 1, "Natural Soil": 1}, "perde_na_falha": True },
}

ESTRUTURA_MENU = {
    "crafting": {
        "relics": ["Giant Ruby", "Giant Emerald", "Giant Sapphire", "Giant Amethyst"],
        "runes": ["Aegis Rune", "Astral Rune", "Ember Rune", "Molten Rune", "Obsidian Rune", "Protector Rune", "Fiery Stone"],
        "tools": ["Advanced Pick", "Diamond Knife", "Enhanced Pick", "Modified Pick"],
        "fishing": ["Engineered Fishing Rod", "Golden Fishing Rod", "Reinforced Rod", "Volcanic Fishing Rod"],
        "ammo": ["10x Steel Bolts"]
    }
}

RASHID_SCHEDULE = {
    0: {"city": "Thais", "desc": "Ao lado direito do DP.", "url": "https://tibiamaps.io/map#32359,32226,6:3"},
    1: {"city": "Venore", "desc": "Loja ao sul/direita do DP.", "url": "https://tibiamaps.io/map#32945,32110,6:3"},
    2: {"city": "Ab'Dendriel", "desc": "Na taverna.", "url": None},
    3: {"city": "Ankrahmun", "desc": "Acima do Post Office.", "url": "https://tibiamaps.io/map#33069,32882,6:4"},
    4: {"city": "Darashia", "desc": "Na taverna.", "url": "https://tibiamaps.io/map#33235,32485,7:3"},
    5: {"city": "Edron", "desc": "Na taverna acima do DP.", "url": "https://tibiamaps.io/map#33170,31812,6:3"},
    6: {"city": "Carlin", "desc": "Primeiro andar do DP.", "url": "https://tibiamaps.io/map#32334,31782,6:3"}
}

WIKI_MONSTER_URL = "https://www.tibiawiki.com.br/wiki/"
