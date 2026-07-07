"""
DofusTeam — zaap_data.py
Liste complète des zaaps Dofus 3 Unity
"""

ZAAPS = [
    {"name": "Arche de Vili",                  "region": "Profondeurs d'Astrub",   "coords": [15, -20]},
    {"name": "Bord de la forêt maléfique",      "region": "Amakna",                 "coords": [-1, 13]},
    {"name": "Champs de Cania",                 "region": "Plaines de Cania",       "coords": [-27, -36]},
    {"name": "Château d'Amakna",                "region": "Amakna",                 "coords": [3, -5]},
    {"name": "Cimetière primitif",              "region": "Montagne des Koalaks",   "coords": [-12, 19]},
    {"name": "Cité d'Astrub",                   "region": "Astrub",                 "coords": [5, -18]},
    {"name": "Coin des Bouftous",               "region": "Amakna",                 "coords": [5, 7]},
    {"name": "Crocuzko",                        "region": "Archipel des Écailles",  "coords": [-83, -15]},
    {"name": "Cœur immaculé",                   "region": "Bonta",                  "coords": [-31, -56]},
    {"name": "Dunes des ossements",             "region": "Saharach",               "coords": [15, -58]},
    {"name": "Entrée du château de Harebourg",  "region": "Île de Frigost",         "coords": [-67, -77]},
    {"name": "Foire du Trool",                  "region": "Foire du Trool",         "coords": [-11, -36]},
    {"name": "Futaie enneigée",                 "region": "Archipel de Valonia",    "coords": [39, -82]},
    {"name": "Île de la Cawotte",               "region": "Île des Wabbits",        "coords": [25, -4]},
    {"name": "La Bourgade",                     "region": "Île de Frigost",         "coords": [-78, -41]},
    {"name": "La Cuirasse",                     "region": "Brâkmar",                "coords": [-26, 37]},
    {"name": "Laboratoires abandonnés",         "region": "Île des Wabbits",        "coords": [27, -14]},
    {"name": "Lac de Cania",                    "region": "Plaines de Cania",       "coords": [-3, -42]},
    {"name": "Massif de Cania",                 "region": "Plaines de Cania",       "coords": [-13, -28]},
    {"name": "Mont des Tombeaux",               "region": "Île de Grobe",           "coords": [40, -44]},
    {"name": "Montagne des Craqueleurs",        "region": "Amakna",                 "coords": [-5, -8]},
    {"name": "Nimotopia",                       "region": "Nimotopia",              "coords": [-67, 29]},
    {"name": "Plage de la Tortue",              "region": "Île de Moon",            "coords": [35, 12]},
    {"name": "Plaine des Porkass",              "region": "Plaines de Cania",       "coords": [-5, -23]},
    {"name": "Plaine des Scarafeuilles",        "region": "Amakna",                 "coords": [-1, 24]},
    {"name": "Plaines Rocheuses",               "region": "Plaines de Cania",       "coords": [-17, -47]},
    {"name": "Port de Madrestam",               "region": "Amakna",                 "coords": [7, -4]},
    {"name": "Rivage sufokien",                 "region": "Baie de Sufokia",        "coords": [10, 22]},
    {"name": "Route des Roulottes",             "region": "Landes de Sidimote",     "coords": [-25, 12]},
    {"name": "Routes Rocailleuses",             "region": "Plaines de Cania",       "coords": [-20, -20]},
    {"name": "Sufokia",                         "region": "Baie de Sufokia",        "coords": [13, 26]},
    {"name": "Tainéla",                         "region": "Astrub",                 "coords": [1, -32]},
    {"name": "Temple des alliances",            "region": "Baie de Sufokia",        "coords": [13, 35]},
    {"name": "Terres Désacrées",                "region": "Landes de Sidimote",     "coords": [-15, 25]},
    {"name": "Village côtier",                  "region": "Île d'Otomaï",           "coords": [-46, 18]},
    {"name": "Village d'Amakna",               "region": "Amakna",                 "coords": [-2, 0]},
    {"name": "Village de Pandala",              "region": "Île de Pandala",         "coords": [20, -29]},
    {"name": "Village de la Canopée",           "region": "Île d'Otomaï",           "coords": [-54, 16]},
    {"name": "Village des Brigandins",          "region": "Plaines de Cania",       "coords": [-16, -24]},
    {"name": "Village des Dopeuls",             "region": "Plaines de Cania",       "coords": [-34, -8]},
    {"name": "Village des Éleveurs",            "region": "Montagne des Koalaks",   "coords": [-16, 1]},
    {"name": "Village des Kanigs",              "region": "Plaines de Cania",       "coords": [0, -56]},
    {"name": "Village enseveli",                "region": "Île de Frigost",         "coords": [-77, -73]},
]

def get_favorites(config):
    """Returns list of favorited zaap names."""
    return config.get("zaap_favorites", [])

def toggle_favorite(config, name):
    """Toggle a zaap as favorite."""
    favs = config.get("zaap_favorites", [])
    if name in favs:
        favs.remove(name)
    else:
        favs.append(name)
    config.set("zaap_favorites", favs)
    config.save()
    return favs
