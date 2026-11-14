"""Moteur pur de la section PNJ : recherche (nom, zone, coordonnées, zaap) et commandes /zaap + /travel.

Aucune dépendance Qt ni réseau : testable seul (tests/test_pnj_engine.py). Même logique que
`features/pnj/lib/engine.ts` du site. Ce module ne simule aucune frappe : il fabrique seulement du texte à copier.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, replace
from typing import Optional

LANGS = ["fr", "en", "es", "de", "pt"]

COPY_MODES = ["route", "travel", "zaap", "pos", "name"]
MODE_LABEL = {
    "route": "trajet",
    "travel": "/travel",
    "zaap": "/zaap",
    "pos": "position",
    "name": "nom",
}


@dataclass(frozen=True)
class Zaap:
    x: int
    y: int
    sa: int  # zone (clé de `areas`)


@dataclass(frozen=True)
class Result:
    key: str
    kind: str  # 'pnj' | 'zaap' | 'pos'
    name: str
    area: str
    x: int
    y: int
    zaap: Optional[Zaap]  # zaap conseillé ; None si la position est un zaap lui-même
    npc_id: Optional[int] = None
    quest: Optional[str] = None
    sa: Optional[int] = None  # zone de la position (pour recalculer le zaap après correction)


@dataclass
class PnjData:
    version: str
    langs: list
    npcs: list
    quests: list
    zaaps: list
    areas: dict
    _by_id: Optional[dict] = None

    @classmethod
    def from_json(cls, raw: dict) -> "PnjData":
        return cls(
            version=str(raw.get("version", "")),
            langs=list(raw.get("langs") or LANGS),
            npcs=list(raw.get("npcs") or []),
            quests=list(raw.get("quests") or []),
            zaaps=[Zaap(int(z["x"]), int(z["y"]), int(z["sa"])) for z in raw.get("zaaps") or []],
            areas=dict(raw.get("areas") or {}),
        )

    def npc(self, npc_id: int):
        if self._by_id is None:
            self._by_id = {n["id"]: n for n in self.npcs}
        return self._by_id.get(npc_id)

    def area_name(self, sa, lang: int = 0) -> str:
        names = self.areas.get(str(sa)) or []
        return names[lang] if lang < len(names) else (names[0] if names else "")


def norm(s: str) -> str:
    """Sans accents ni casse (« Brâkmar » -> « brakmar »)."""
    d = unicodedata.normalize("NFD", s)
    return "".join(c for c in d if unicodedata.category(c) != "Mn").lower().strip()


_COORDS = re.compile(r"^\s*\[?\s*(-?\d{1,3})\s*[,; ]\s*(-?\d{1,3})\s*\]?\s*$")


def parse_coords(q: str):
    m = _COORDS.match(q)
    return (int(m.group(1)), int(m.group(2))) if m else None


def nearest_zaap(x: int, y: int, zaaps: list) -> Optional[Zaap]:
    """Zaap le plus proche, distance de Manhattan (on traverse les cartes une à une)."""
    best, bd = None, float("inf")
    for z in zaaps:
        d = abs(z.x - x) + abs(z.y - y)
        if d < bd:
            bd, best = d, z
    return best


def zaap_for(x: int, y: int, sa: int, zaaps: list) -> Optional[Zaap]:
    """Zaap de la même zone s'il existe, sinon le plus proche."""
    for z in zaaps:
        if z.sa == sa:
            return z
    return nearest_zaap(x, y, zaaps)


def command(r: Result, mode: str, anti_lag: bool = True) -> str:
    travel = f"/travel {r.x},{r.y}"
    zaap = f"/zaap {r.zaap.x},{r.zaap.y}" if r.zaap else ""
    if mode == "route":
        if not r.zaap:
            return f"/zaap {r.x},{r.y}"
        return ";".join([zaap, zaap, travel] if anti_lag else [zaap, travel])
    if mode == "travel":
        return travel
    if mode == "zaap":
        return zaap or f"/zaap {r.x},{r.y}"
    if mode == "pos":
        return f"[{r.x},{r.y}]"
    if mode == "name":
        return r.name
    raise ValueError(f"mode de copie inconnu : {mode}")


def _name(n: dict, lang: int) -> str:
    names = n["n"]
    return (names[lang] if lang < len(names) else "") or names[0]


def _quest(data: PnjData, qi, lang: int):
    if qi is None or qi < 0 or qi >= len(data.quests):
        return None
    q = data.quests[qi]
    return (q[lang] if lang < len(q) else "") or q[0]


def _pnj_result(data: PnjData, n: dict, i: int, lang: int) -> Result:
    x, y, sa, qi = n["p"][i][:4]
    return Result(
        key=f"pnj:{n['id']}:{i}", kind="pnj", npc_id=n["id"], name=_name(n, lang),
        area=data.area_name(sa, lang), quest=_quest(data, qi, lang), x=x, y=y, sa=sa,
        zaap=zaap_for(x, y, sa, data.zaaps),
    )


def search(query: str, data: PnjData, lang: int = 0, limit: int = 60) -> list:
    q = norm(query)
    if not q:
        return []
    c = parse_coords(query)
    if c:
        x, y = c
        z = next((z for z in data.zaaps if z.x == x and z.y == y), None)
        return [Result(
            key=f"pos:{x},{y}", kind="zaap" if z else "pos",
            name=f"Zaap {data.area_name(z.sa, lang)}" if z else f"[{x},{y}]",
            area="", x=x, y=y, zaap=None if z else nearest_zaap(x, y, data.zaaps),
            sa=z.sa if z else None,
        )]
    out = []
    wants_zaap = q.startswith("zaap")
    rest = q[4:].strip() if wants_zaap else q
    for z in data.zaaps:
        name = data.area_name(z.sa, lang)
        hit = (not rest or rest in norm(name)) if wants_zaap else q in norm(name)
        if hit:
            out.append(Result(key=f"zaap:{z.x},{z.y}", kind="zaap", name=f"Zaap {name}", area=name,
                              x=z.x, y=z.y, zaap=None, sa=z.sa))
    if wants_zaap:
        return out[:limit]
    pnj = []
    for n in data.npcs:
        at = norm(_name(n, lang)).find(q)
        if at < 0:
            continue
        for i in range(len(n["p"])):
            pnj.append((0 if at == 0 else 1, _pnj_result(data, n, i, lang)))
    pnj.sort(key=lambda t: (t[0], t[1].name.casefold()))
    return (out + [r for _, r in pnj])[:limit]


def npc_result(data: PnjData, npc_id: int, lang: int = 0) -> Optional[Result]:
    """Fiche d'un PNJ à sa position principale (la première) ; None s'il n'est pas localisé."""
    n = data.npc(npc_id)
    if not n or not n.get("p"):
        return None
    return _pnj_result(data, n, 0, lang)


def popular(data: PnjData, lang: int = 0, count: int = 12) -> list:
    """PNJ les plus cités par les quêtes, proposés avant toute saisie."""
    top = sorted(data.npcs, key=lambda n: -n.get("w", 0))[:count]
    return [r for r in (npc_result(data, n["id"], lang) for n in top) if r]


def zone_hue(name: str) -> int:
    """Teinte stable par zone (même formule que le site) pour la pastille colorée."""
    h = 0
    for ch in name:
        h = (h * 31 + ord(ch)) % 360
    return h


# ── Corrections locales (position / zaap d'un PNJ), jamais envoyées au site ─────
def apply_correction(r: Result, corr: Optional[dict], zaaps: list) -> Result:
    """corr = {"x":…, "y":…} et/ou {"zaap": [zx, zy]}. Retourne la carte corrigée."""
    if not corr:
        return r
    x, y = corr.get("x", r.x), corr.get("y", r.y)
    zaap = r.zaap
    if corr.get("zaap"):
        zx, zy = corr["zaap"]
        zaap = next((z for z in zaaps if z.x == zx and z.y == zy), Zaap(int(zx), int(zy), -1))
    elif "x" in corr and "y" in corr:
        zaap = zaap_for(x, y, r.sa, zaaps) if r.sa is not None else nearest_zaap(x, y, zaaps)
    return replace(r, x=int(x), y=int(y), zaap=zaap)


# ── Convoi : plan d'étapes pour plusieurs personnages ──────────────────────────
def convoi_steps(r: Result, names: list, leader: str, anti_lag: bool = True) -> list:
    """Étapes dans l'ordre de passage : suiveurs d'abord, chef en dernier.

    Chaque étape est {"kind": "copy"|"reminder", "who": nom|None, "text": commande|rappel, "label": …}.
    Une étape « copy » = on copie la commande et on met la fenêtre du perso au premier plan ; le joueur colle et
    valide lui-même. Rien n'est envoyé au jeu par ce module.
    """
    followers = [n for n in names if n != leader]
    order = followers + ([leader] if leader in names else [])
    zaap_cmd = f"/zaap {r.zaap.x},{r.zaap.y}" if r.zaap else f"/zaap {r.x},{r.y}"
    steps = [{"kind": "copy", "who": n, "text": zaap_cmd, "label": "zaap"} for n in order]
    if r.zaap:  # si la destination est elle-même un zaap, il n'y a pas de /travel
        steps.append({"kind": "reminder", "who": None, "label": "suivi",
                      "text": "Réactive le suivi automatique (raccourci du jeu), puis passe à l'étape suivante."})
        travel = f"/travel {r.x},{r.y}"
        steps += [{"kind": "copy", "who": n, "text": travel, "label": "travel"} for n in order]
    return steps


# ── Convoi automatique : plan d'exécution (le même enchaînement que la macro /zaap de l'Organizer) ──────────────
CONVOI_TIMINGS = {"arrival_delay": 4.0, "follow_delay": 1.0, "between_delay": 0.35, "follow_key": "ctrl+w", "travel_all": False}


def convoi_macro_steps(r: Result, followers: list, leader: str, timings: Optional[dict] = None) -> list:
    """Plan de la macro convoi : /zaap sur chaque suiveur (un par un), /zaap sur le chef, attente d'arrivée,
    touche de suivi automatique sur le chef, attente, puis /travel (sur le chef ; sur tous si `travel_all`).

    Syntaxes confirmées en jeu : `/zaap x y` (SANS virgule) et `/travel x,y` (AVEC virgule).
    Étapes : {"do": "paste", "who", "text"} | {"do": "key", "who", "key"} | {"do": "wait", "s", "label"}.
    Si la destination est elle-même un zaap, il n'y a ni suivi ni /travel.
    """
    t = dict(CONVOI_TIMINGS, **(timings or {}))
    zx, zy = (r.zaap.x, r.zaap.y) if r.zaap else (r.x, r.y)
    zaap = f"/zaap {zx} {zy}"
    steps = []
    for n in followers:
        steps.append({"do": "paste", "who": n, "text": zaap})
        steps.append({"do": "wait", "s": t["between_delay"], "label": "entre deux persos"})
    steps.append({"do": "paste", "who": leader, "text": zaap})
    if not r.zaap:
        return steps
    steps.append({"do": "wait", "s": t["arrival_delay"], "label": "arrivée au zaap"})
    steps.append({"do": "key", "who": leader, "key": t["follow_key"]})
    steps.append({"do": "wait", "s": t["follow_delay"], "label": "suivi automatique"})
    travel = f"/travel {r.x},{r.y}"
    for n in ([leader] + followers if t["travel_all"] else [leader]):
        steps.append({"do": "paste", "who": n, "text": travel})
        if t["travel_all"]:
            steps.append({"do": "wait", "s": t["between_delay"], "label": "entre deux persos"})
    return steps
