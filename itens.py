# itens.py

RECEITAS = {
    # --- RELICS ---
    "Giant Ruby": { "multiplicador": 5, "ingredientes": {"Small Ruby": 10}, "perde_na_falha": True },
    "Giant Emerald": { "multiplicador": 5, "ingredientes": {"Small Emerald": 10}, "perde_na_falha": True },
    "Giant Sapphire": { "multiplicador": 5, "ingredientes": {"Small Sapphire": 10}, "perde_na_falha": True },
    "Giant Amethyst": { "multiplicador": 5, "ingredientes": {"Small Amethyst": 10}, "perde_na_falha": True },

    # --- TOOLS ---
    "Modified Pick": { "multiplicador": 2, "ingredientes": {"Pick": 1, "Steel": 5}, "perde_na_falha": True },
    "Advanced Pick": { "multiplicador": 1.5, "ingredientes": {"Pick": 1, "Steel": 10}, "perde_na_falha": True },
    "Enhanced Pick": { "multiplicador": 1, "ingredientes": {"Pick": 1, "Steel": 20}, "perde_na_falha": True },
    "Diamond Knife": { "multiplicador": 1, "ingredientes": {"Combat Knife": 1, "Small Diamond": 10, "Hell Steel": 5}, "perde_na_falha": True },

    # --- RUNES ---
    "Ember Rune": { "multiplicador": 1, "ingredientes": {"Ember Fragment": 5, "Pulverized Ore": 3, "Onyx": 1}, "nao_perde": ["Onyx"] },
    "Protector Rune": { "multiplicador": 1, "ingredientes": {"Protector Fragment": 5, "Pulverized Ore": 3, "Onyx": 1}, "nao_perde": ["Onyx"] },
    "Obsidian Rune": { "multiplicador": 1, "ingredientes": {"Obsidian Fragment": 5, "Pulverized Ore": 3, "Onyx": 1}, "nao_perde": ["Onyx"] },
    "Aegis Rune": { "multiplicador": 1, "ingredientes": {"Aegis Fragment": 5, "Pulverized Ore": 3, "Onyx": 1}, "nao_perde": ["Onyx"] },
    "Astral Rune": { "multiplicador": 1, "ingredientes": {"Astral Fragment": 5, "Pulverized Ore": 3, "Onyx": 1}, "nao_perde": ["Onyx"] },
    "Molten Rune": { "multiplicador": 1, "ingredientes": {"Molten Fragment": 5, "Pulverized Ore": 3, "Onyx": 1}, "nao_perde": ["Onyx"] },
    "Fiery Stone": { "multiplicador": 0.5, "ingredientes": {"Glimmering Soil": 5}, "perde_na_falha": True },

    # --- FISHING ---
    "Reinforced Rod": { "multiplicador": 2, "ingredientes": {"Fishing Rod": 1, "Steel": 5}, "perde_na_falha": True },
    "Engineered Fishing Rod": { "multiplicador": 1.5, "ingredientes": {"Fishing Rod": 1, "Steel": 10, "Draconian Steel": 1}, "perde_na_falha": True },
    "Volcanic Fishing Rod": { "multiplicador": 1, "ingredientes": { "Fishing Rod": 1, "Steel": 20, "Glimmering Soil": 10, "Draconian Steel": 5, "Hell Steel": 3 }, "perde_na_falha": True },
    "Golden Fishing Rod": { "multiplicador": 0.5, "ingredientes": { "Fishing Rod": 1, "Steel": 40, "Draconian Steel": 10, "Gold Ingot": 3, "Hell Steel": 3 }, "perde_na_falha": True },

    # --- AMMO ---
    "10x Steel Bolts": { "multiplicador": 0.4, "ingredientes": {"Bolt": 5, "Steel": 1, "Natural Soil": 1}, "perde_na_falha": True }
}

# Use códigos simples aqui. A tradução será feita pelo idiomas.py
CATEGORIAS = {
    "relics": ["Giant Ruby", "Giant Emerald", "Giant Sapphire", "Giant Amethyst"],
    "runes": ["Aegis Rune", "Astral Rune", "Ember Rune", "Molten Rune", "Obsidian Rune", "Protector Rune", "Fiery Stone"],
    "tools": ["Advanced Pick", "Diamond Knife", "Enhanced Pick", "Modified Pick"],
    "fishing": ["Engineered Fishing Rod", "Golden Fishing Rod", "Reinforced Rod", "Volcanic Fishing Rod"],
    "ammo": ["10x Steel Bolts"]
}
