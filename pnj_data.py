"""Données de la section PNJ : téléchargement versionné, copie locale, chargement.

Les fichiers (pnj.json, pnj-packs.json, vignettes) sont publiés par le site et jamais recopiés à la main.
Au lancement on compare `version` à la copie locale ; hors ligne on garde la copie locale. Les vignettes
sont téléchargées à la demande puis gardées en cache. Tout le réseau est appelé depuis un thread
(voir PnjSync) : ces fonctions peuvent bloquer, jamais le thread d'interface.
"""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path
from typing import Optional

from paths import APP_DIR, PNJ_SEED_DIR
from pnj_engine import PnjData

BASE_URL = "https://www.dofusteam.fr"
CACHE_DIR = APP_DIR / "pnj_cache"
TIMEOUT = 10

# Tant que le site n'est pas poussé en ligne : copie locale du dépôt du site (développement uniquement).
DEV_SITE_PUBLIC = Path(os.environ.get("DOFUSTEAM_SITE_PUBLIC", Path.home() / "Documents" / "dofus-team" / "public"))

DATA_FILES = {"pnj": "data/pnj.json", "packs": "data/pnj-packs.json"}


def _cache_path(rel: str) -> Path:
    return CACHE_DIR / rel


def _read_json(path: Path) -> Optional[dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _http_get(rel: str, version: str = "") -> Optional[bytes]:
    url = f"{BASE_URL}/{rel}" + (f"?v={version}" if version else "")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "DofusTeamOrganizer"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.read() if r.status == 200 else None
    except Exception:
        return None


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)


def local_version(kind: str) -> str:
    raw = _read_json(_cache_path(DATA_FILES[kind]))
    return str(raw.get("version", "")) if raw else ""


def refresh(kind: str) -> bool:
    """Retélécharge le fichier si sa version a changé. True si la copie locale a été mise à jour."""
    rel = DATA_FILES[kind]
    have = local_version(kind)
    body = _http_get(rel, have)  # ?v=<version connue> : contourne le cache ; la nouvelle version vient du contenu
    if not body:
        return False
    try:
        new = json.loads(body.decode("utf-8"))
    except ValueError:
        return False
    if not isinstance(new, dict) or not new.get("version") or str(new["version"]) == have:
        return False
    _write(_cache_path(rel), body)
    return True


def _load_raw(kind: str) -> Optional[dict]:
    """Copie locale du cache, sinon (développement) copie du dépôt du site, sinon la copie embarquée (pnj_seed)."""
    raw = _read_json(_cache_path(DATA_FILES[kind]))
    if raw is None:
        raw = _read_json(DEV_SITE_PUBLIC / DATA_FILES[kind])
    if raw is None:
        raw = _read_json(PNJ_SEED_DIR / DATA_FILES[kind])
    return raw


def load_pnj() -> Optional[PnjData]:
    raw = _load_raw("pnj")
    return PnjData.from_json(raw) if raw else None


def load_packs() -> list:
    """Liste de packs (dicts bruts du site) ; vide si rien n'est disponible."""
    raw = _load_raw("packs")
    return list(raw.get("packs") or []) if raw else []


def packs_version() -> str:
    raw = _load_raw("packs")
    return str(raw.get("version", "")) if raw else ""


def image_path(rel: str) -> Optional[Path]:
    """Chemin local d'une image du site (ex. 'pnj/1005.webp') ; None si absente (repli à prévoir côté UI).

    Ne télécharge pas : voir fetch_image() pour le thread de fond.
    """
    p = _cache_path(rel)
    if p.exists():
        return p
    for base in (DEV_SITE_PUBLIC, PNJ_SEED_DIR):
        if (base / rel).exists():
            return base / rel
    return None


def fetch_image(rel: str) -> Optional[Path]:
    """Télécharge une image si elle n'est pas encore en cache (thread de fond). None si indisponible."""
    p = image_path(rel)
    if p:
        return p
    body = _http_get(rel)
    if not body:
        return None
    _write(_cache_path(rel), body)
    return _cache_path(rel)


def npc_image_rel(npc_id: int) -> str:
    return f"pnj/{npc_id}.webp"


def pack_image_rel(icon: str) -> str:
    return f"pnj-packs/{icon}"
