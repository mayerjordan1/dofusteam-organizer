"""Mise en forme visuelle des guides niveau 200 : icônes d'états du jeu (skin/etat_*.png)
insérées dans le texte + galeries d'images (carte du combat, schémas des sorts/mécaniques,
fiches de stats des monstres) issues de dofuspourlesnoobs.com (cf. donjon_gallery_200.py).
Toutes les images sont cliquables (zoom:<fichier>, cf. BossNotesDialog._on_guide_link)."""
import re

from pages.donjon_gallery_200 import GALLERY_200

GOLD, ORANGE = "#c8a000", "#ff8a1e"

# mot (insensible à la casse) -> icône d'état
_STATE_ICONS = {
    r"Invulnérables?": "etat_invulnerable.png",
    r"Indéplaçables?": "etat_indeplacable.png",
    r"Inébranlables?": "etat_inebranlable.png",
    r"Pesanteur": "etat_pesanteur.png",
    r"Lourds?": "etat_lourd.png",
    r"Pacifistes?": "etat_pacifiste.png",
    r"Insoignables?": "etat_insoignable.png",
    r"Affaibli": "etat_affaibli.png",
    r"Enracinée?s?": "etat_enracine.png",
    r"Télefrag|Téléfrag": "etat_telefrag.png",
    r"Mort en sursis": "etat_mort_en_sursis.png",
}
_ICON_RE = re.compile(r"\b(" + "|".join(_STATE_ICONS) + r")\b", re.I)


def _icon_tag(word):
    for pat, f in _STATE_ICONS.items():
        if re.fullmatch(pat, word, re.I):
            return (f'<img src="{f}" width="16" height="16" '
                    f'style="vertical-align:-4px; margin:0 2px;">')
    return ""


def add_state_icons(html):
    """Ajoute l'icône de l'état avant chaque mention (texte uniquement, jamais dans une balise)."""
    parts = re.split(r"(<[^>]+>)", html)
    for i, seg in enumerate(parts):
        if seg.startswith("<") or not seg.strip():
            continue
        parts[i] = _ICON_RE.sub(lambda m: _icon_tag(m.group(1)) + m.group(1), seg)
    return "".join(parts)


def _fig(rec, width):
    f, w, h, cap = rec
    dw = min(width, w)
    dh = round(h * dw / w)
    return (f'<a href="zoom:{f}"><img src="{f}" width="{dw}" height="{dh}"></a>'
            f'<br><span style="font-size:10px; color:#7a7d8a;">{cap}</span>')


def _grid(recs):
    """Images étroites (≤450 px) par 2 en tableau, larges en pleine largeur."""
    out, pend = [], []

    def flush():
        if not pend:
            return
        cells = "".join(f'<td style="padding:0 8px 10px 0; vertical-align:top;">{_fig(r, 232)}</td>' for r in pend)
        out.append(f'<table style="margin:0 0 4px 0;"><tr>{cells}</tr></table>')
        pend.clear()

    for r in recs:
        if r[1] <= 450:
            pend.append(r)
            if len(pend) == 2:
                flush()
        else:
            flush()
            out.append(f'<p style="margin:0 0 10px 0;">{_fig(r, 480)}</p>')
    flush()
    return "".join(out)


def _h(title, color=GOLD):
    return (f'<h3 style="color:{color}; font-size:13px; margin:10px 0 6px 0; '
            f'letter-spacing:.3px;">{title}</h3>')


def compose(key, html):
    """Carte du combat + texte (avec icônes d'états) + galeries."""
    g = GALLERY_200.get(key) or {}
    top = (f'<p style="margin:0 0 4px 0;">{_fig(list(g["map"][:3]) + ["Carte du combat"], 480)}</p>'
           if g.get("map") else "")
    tail = ""
    if g.get("schemas"):
        tail += _h("Sorts du boss & schémas du combat") + _grid(g["schemas"])
    if g.get("monstres"):
        tail += _h("Monstres — caractéristiques", ORANGE) + "".join(
            f'<p style="margin:0 0 8px 0;">{_fig(r, 480)}</p>' for r in g["monstres"])
    if g.get("sorts_monstres"):
        tail += _h("Sorts des monstres (zones)", ORANGE) + _grid(g["sorts_monstres"])
    return top + add_state_icons(html) + tail
