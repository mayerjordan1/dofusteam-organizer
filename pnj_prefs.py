"""Préférences et données personnelles de la section PNJ (stockées dans settings.json, clé « pnj »).

Tout reste en local : favoris, positions perso, corrections, packs perso, cases « fait ». Rien n'est envoyé au site.
"""
from __future__ import annotations

import copy

from pnj_engine import CONVOI_TIMINGS

DEFAULTS = {
    "lang": 0,                 # indice dans LANGS (fr, en, es, de, pt)
    "theme": "dofusteam",
    "opacity": 95,             # 30 à 100
    "geometry": None,          # [x, y, w, h] (fenêtre complète)
    "geometry_compact": None,  # [x, y, w, h] (mode pack discret)
    "compact": True,           # un pack ouvert devient une petite liste de PNJ, sans recherche ni favoris
    "mode": "route",           # mode de copie courant
    "anti_lag": True,
    "favs": [None] * 6,        # 6 emplacements : dict {"kind","key","npc_id"|None,"x","y","name",...} ou None
    "custom_pos": [],          # [{"id", "name", "x", "y", "icon"}]
    "corrections": {},         # {result_key: {"x","y","zaap":[zx,zy]}}
    "done": {},                # {pack_id: [npc_id,…]}
    "custom_packs": [],        # [{"id","name","npcs":[id…]}]
    # convoi : délais de la macro (secondes), touche de suivi, /travel pour tous ; click_launches = un clic sur une tuile lance le convoi
    "convoi": dict(CONVOI_TIMINGS, click_launches=True),
}


class PnjPrefs:
    def __init__(self, config):
        self.config = config
        raw = config.get("pnj", None) or {}
        self.d = copy.deepcopy(DEFAULTS)
        self.d.update({k: v for k, v in raw.items() if k in DEFAULTS})
        self.d["convoi"] = {**DEFAULTS["convoi"], **(raw.get("convoi") or {})}
        if len(self.d["favs"]) != 6:
            self.d["favs"] = (list(self.d["favs"]) + [None] * 6)[:6]

    def __getitem__(self, k):
        return self.d[k]

    def __setitem__(self, k, v):
        self.d[k] = v

    def save(self):
        self.config.set("pnj", self.d)
        self.config.save()

    # Corrections ──────────────────────────────────────────────────────────────
    def correction(self, key):
        return self.d["corrections"].get(key)

    def set_correction(self, key, corr):
        if corr:
            self.d["corrections"][key] = corr
        else:
            self.d["corrections"].pop(key, None)
        self.save()

    # Cases « fait » ───────────────────────────────────────────────────────────
    def is_done(self, pack_id, npc_id):
        return npc_id in self.d["done"].get(pack_id, [])

    def set_done(self, pack_id, npc_id, value):
        lst = self.d["done"].setdefault(pack_id, [])
        if value and npc_id not in lst:
            lst.append(npc_id)
        elif not value and npc_id in lst:
            lst.remove(npc_id)
        self.save()

    def reset_done(self, pack_id):
        self.d["done"].pop(pack_id, None)
        self.save()
