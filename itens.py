# --- CONFIGURAÇÕES GERAIS ---
CONSTANTES_SKILLS = {
    "knight":    {"melee": 50,  "distance": 140, "shielding": 100},
    "paladin":   {"melee": 120, "distance": 25,  "shielding": 100},
    "druid":     {"melee": 200, "distance": 200, "shielding": 100},
    "sorcerer":  {"melee": 200, "distance": 200, "shielding": 100}
}

ARMAS_TREINO = {
    "Normal / Nenhuma":        {"speed": 2.0, "charges": 999999999},
    "Weapon (-5% Atk Speed)":  {"speed": 1.9,  "charges": 999999999},
    "Weapon (-6% Atk Speed)":  {"speed": 1.88, "charges": 999999999},
    "Spark Weapon (3.6k)":     {"speed": 1.8, "charges": 3600},
    "Spark Shield (7.2k)":     {"speed": 1.8, "charges": 7200},
    "Lightning Weapon (7.2k)": {"speed": 1.7, "charges": 7200},
    "Lightning Shield (14.4k)": {"speed": 1.7, "charges": 14400},
    "Inferno Weapon (10.8k)":  {"speed": 1.6, "charges": 10800},
    "Inferno Shield (21.6k)":  {"speed": 1.6, "charges": 21600},
}

ALCHEMY_DATA = {
    "converter": { "charges": 100, "cost": 500, "base_chance": 10, "skill_factor": 0.2 },
    "crystals": {
        "Spark Crystal":     {"base_chance": 20},
        "Lightning Crystal": {"base_chance": 15},
        "Inferno Crystal":   {"base_chance": 10}
    }
}

ALCHEMY_RUNES = {
    "Sudden Death":         {"min": 55, "base": 22.72, "pro": True},
    "Explosion":            {"min": 28, "base": 27.77, "pro": True},
    "Great Fireball":       {"min": 22, "base": 41.66, "pro": False},
    "Heavy Magic Missile":  {"min": 13, "base": 71.42, "pro": False},
    "Light Magic Missile":  {"min": 10, "base": 100.0, "pro": False},
    "Fireball":             {"min": 16, "base": 83.33, "pro": False},
    "Ultimate Healing":     {"min": 22, "base": 50.0,  "pro": True},
    "Intense Healing":      {"min": 13, "base": 83.33, "pro": False},
    "Antidote Rune":        {"min": 10, "base": 100.0, "pro": False},
    "Envenom":              {"min": 22, "base": 50.0,  "pro": False},
    "Paralyze":             {"min": 64, "base": 8.33,  "pro": True},
    "Magic Wall":           {"min": 37, "base": 20.0,  "pro": True},
    "Energy Bomb":          {"min": 40, "base": 22.72, "pro": False},
    "Energy Wall":          {"min": 37, "base": 20.0,  "pro": False},
    "Energy Field":         {"min": 19, "base": 62.5,  "pro": False},
    "Fire Bomb":            {"min": 25, "base": 33.33, "pro": False},
    "Fire Wall":            {"min": 28, "base": 25.0,  "pro": False},
    "Fire Field":           {"min": 13, "base": 83.33, "pro": False},
    "Poison Bomb":          {"min": 22, "base": 38.46, "pro": False},
    "Poison Wall":          {"min": 25, "base": 31.25, "pro": False},
    "Poison Field":         {"min": 10, "base": 100.0, "pro": False},
    "Soulfire":             {"min": 31, "base": 33.33, "pro": False},
    "Animate Dead":         {"min": 22, "base": 16.66, "pro": False},
    "Convince Creature":    {"min": 25, "base": 50.0,  "pro": False},
    "Chameleon":            {"min": 22, "base": 33.33, "pro": False},
    "Desintegrate":         {"min": 22, "base": 50.0,  "pro": False},
    "Destroy Field":        {"min": 19, "base": 83.33, "pro": False},
}

MINING_PICKS = {
    "Pick (Normal)":        {"bonus_break": 0, "bonus_collect": 0.0},
    "Modified Pick":        {"bonus_break": 2, "bonus_collect": 0.25},
    "Advanced Pick":        {"bonus_break": 4, "bonus_collect": 0.50},
    "Enhanced Pick":        {"bonus_break": 6, "bonus_collect": 1.00}
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

# --- URLs WIKI (CORRIGIDAS) ---
WIKI_MONSTER_URL = "https://www.tibiawiki.com.br/wiki/"
BASE_MIRACLE_URL = "https://miracle74.com/"
MIRACLE_ITEMS_URL = "https://miracle74.com/?subtopic=items"
MIRACLE_ITEM_ID_URL = "https://miracle74.com/?subtopic=items&id="
