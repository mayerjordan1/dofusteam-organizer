# AGENTS.md — DofusTeam Organizer (Python Desktop) + Hunt Tool

## Contexte général
Jordan, entrepreneur basé à Strasbourg. Joueur Dofus Unity multi-compte (8 persos simultanés).
Ce repo contient **DofusTeam Organizer** — gestionnaire multi-compte Python/PyQt6 pour Dofus 3 Unity.
DA partagée avec le site DofusTeam : Space Mono + #c8f135 (vert citron) + #0d1117 fond.

---

## PROJET 1 — DofusTeam Organizer (Python Desktop)

### Stack
- **Python 3.14** (installé via Microsoft Store)
- **PyQt6** — UI principale
- **pywin32** — gestion fenêtres Windows (win32gui, win32api, win32con, win32process)
- **keyboard** — raccourcis globaux (`suppress=False` OBLIGATOIRE — suppress=True corrompt l'état clavier)
- **pyautogui** — automation souris/clavier
- **pyperclip** — clipboard
- **Pillow** — traitement images (suppression fond noir des PNG)
- **pygame** — sons (optionnel)
- **tkinter** — roue radiale (fenêtre overlay)

### Structure fichiers
```
DofusTeam_Beta_V1.01/
├── main.py              # UI principale PyQt6 + logique app
├── logic.py             # Détection fenêtres Dofus + gestion comptes
├── calibrator.py        # Overlay calibration zaap/chat (PyQt6 overlay sur fenêtre Dofus)
├── zaap_macro.py        # Macros auto-zaap (Phase 1: H sur tous, Phase 2: clics)
├── zaap_favorites.py    # Fenêtre favoris zaap + macro destination complète
├── zaap_data.py         # 43 destinations zaap Dofus 3 Unity (base de données)
├── invite_dialog.py     # Fenêtre invitation groupe (/invite Pseudo)
├── zaap_dialog.py       # Fenêtre auto-zaap (calibration + exécution 3 phases)
├── char_selector.py     # Sélecteur personnage rectangulaire 3x3 (logo DofusTeam centre)
├── settings.json        # Config persistante (auto-sauvegardée)
├── skin/                # Images PNG classes (fond transparent) + logo.png
│   ├── logo.png         # Œuf cosmique DofusTeam (fond noir supprimé par PIL)
│   ├── cra.png, zobal.png, etc.  # 19 classes Dofus (transparence PIL)
│   └── character.png, zaap.png, etc.
├── install.bat          # Installation dépendances (setuptools upgrade avant pygame)
├── start.bat            # Lancement (python main.py || py main.py)
└── build.bat            # Compilation .exe PyInstaller
```

### Design System (DA DofusTeam)
```python
BG   = "#0d1117"    # fond principal
BG2  = "#161b22"    # fond cartes/headers
BG3  = "#1c2128"    # fond boutons
ACC  = "#c8f135"    # accent vert citron
BLUE = "#4fa3e0"    # bleu
RED  = "#e05c5c"    # rouge
TEXT = "#e8e9ed"    # texte principal
MUT  = "#7a7d8a"    # texte secondaire
GOLD = "#c8a000"    # or (chef, zaap)
# Font titre : Space Mono (mono(18, True))
# Font UI    : Segoe UI 13px
```

### Settings.json — structure complète
```json
{
  "prev_key": "<",
  "next_key": "tab",
  "leader_key": "",
  "toggle_app_key": "f10",
  "refresh_key": "f5",
  "calib_key": "f4",
  "sort_taskbar_key": "",
  "auto_zaap_key": "",
  "invite_group_key": "",
  "selector_key": "",
  "game_haven_key": "h",
  "game_version": "Unity",
  "leader_name": "Jamaal",
  "accounts_state": {"Jamaal": true, "Zyrrh": true},
  "accounts_team": {"Jamaal": "Team 1"},
  "current_mode": "ALL",
  "classes": {"Jamaal": "Cra", "Zyrrh": "Zobal"},
  "custom_order": ["Jamaal", "Zyrrh", "Morthys", "Pickless"],
  "macro_positions": {
    "chat_position": [794, 2025],
    "zaaps": {
      "Jamaal": [0.291, 0.348],
      "Zyrrh":  [0.291, 0.348]
    }
  },
  "cycle_row_binds": ["ctrl+F1","ctrl+F2","ctrl+F3","ctrl+F4","ctrl+F5","ctrl+F6","ctrl+F7","ctrl+F8"],
  "zaap_open_delay": 1.0,
  "zaap_click_delay": 0.3,
  "zaap_paste_delay": 0.35,
  "volume_level": 50,
  "spam_click_interval": 0.1,
  "mini_toolbar_x": 100,
  "mini_toolbar_y": 100,
  "zaap_favorites": [],
  "presets": [],
  "selector_key": ""
}
```

---

### Architecture UI — MainWindow (main.py)

**Layout vertical :**
1. `_mk_header()` — Logo 52px + "DofusTeam" Space Mono 22pt + badge EN JEU + bouton RACCOURCIS ON/OFF
2. `_mk_action_bar()` — ◀▶ nav + AUTO ZAAP + ★ FAVORIS + INVITER + CALIB ZAAP F4 + CALIB CHAT + SCANNER (accent) + TRIER
3. **Main content** (QHBoxLayout) :
   - Gauche (60%) : `_mk_accounts_panel()` — liste comptes live
   - Droite (40%) : `_mk_side_panel()` — config + presets + actions rapides
4. `_mk_shortcuts_bar()` — grille 3×3 raccourcis clavier configurables
5. `_mk_status_bar()` — message statut + "Mini-toolbar ↗"

**AccountRow** — chaque ligne compte :
- Numéro position | ● dot live | Avatar 38px (PNG transparent) | Nom + Classe (HTML label) | ⭐ (ACC bg 65%) | T1 badge | ★ chef | ✕ rouge

**MiniToolbar** — fenêtre flottante (WindowStaysOnTopHint) :
- 👥 Afficher | ◀ Précédent | ▶ Suivant | ★ Chef | 🎒 Havresac+Zaap | 📋 Coller | 🖱 Spam
- Après scan : icônes personnages ajoutées dynamiquement avec surbrillance du perso actif
- Clic droit sur 🎒 → menu zaap favoris
- Draggable, position sauvegardée

**PresetPanel** — dans le side panel :
- Presets d'initiative nommés
- Chaque preset = ordre custom des persos
- Appliquer → réorganise `custom_order` + `sort_taskbar()`

---

### Logique Windows — DofusLogic (main.py + logic.py)

**Détection Dofus Unity :**
```python
# Titre fenêtre Unity : "PseudoPerso - Classe"
# Class Windows : "UnityWndClass"
if win32gui.GetClassName(hwnd) == "UnityWndClass":
    parts = title.split(" - ")
    pseudo = parts[0]  # nom du perso
    classe = parts[1]  # classe détectée auto
```

**Focus window — méthode AttachThreadInput (sans Alt = pas de Alt+Tab) :**
```python
fg = win32gui.GetForegroundWindow()
fg_tid  = ctypes.windll.user32.GetWindowThreadProcessId(fg, None)
cur_tid = ctypes.windll.user32.GetWindowThreadProcessId(hwnd, None)
ctypes.windll.user32.AttachThreadInput(fg_tid, cur_tid, True)
ctypes.windll.user32.AllowSetForegroundWindow(0xFFFFFFFF)
win32gui.SetForegroundWindow(hwnd)
win32gui.BringWindowToTop(hwnd)
ctypes.windll.user32.AttachThreadInput(fg_tid, cur_tid, False)
```

**RÈGLE CRITIQUE — suppress=False :**
```python
keyboard.add_hotkey(key, fn, suppress=False)
# suppress=True corrompt l'état clavier Windows — impossible de taper du texte après
```

**Sort taskbar :**
```python
for a in active: win32gui.ShowWindow(a["hwnd"], SW_HIDE)
time.sleep(0.3)
for a in active: win32gui.ShowWindow(a["hwnd"], SW_SHOW); time.sleep(0.1)
```

---

### Macros — zaap_macro.py

**Macro Havre-sac + Zaap (2 phases) :**
```python
# Phase 1 : H rapide sur toutes les fenêtres (chargement parallèle)
for acc in accounts:
    logic.focus_window(acc["hwnd"])
    # Attendre focus confirmé (GetForegroundWindow == hwnd)
    for _ in range(15): ...wait 0.1s...
    # Envoyer H via SendInput (méthode la plus fiable)
    _send_key_sendinput(haven_key)  # ctypes SendInput
    time.sleep(0.12)  # switch rapide

time.sleep(1.0)  # havre-sacs chargent en parallèle

# Phase 2 : Clic zaap calibré sur chaque fenêtre
for acc in accounts:
    logic.focus_window(hwnd)
    # clic à position relative (rx, ry) dans la fenêtre
    rect = win32gui.GetWindowRect(hwnd)
    pyautogui.click(rect[0] + w*rx, rect[1] + h*ry)
```

**SendInput (plus fiable que keybd_event) :**
```python
def _send_key_sendinput(key_char):
    class KEYBDINPUT(ctypes.Structure):
        _fields_=[('wVk',ctypes.c_ushort),('wScan',ctypes.c_ushort),
                  ('dwFlags',ctypes.c_ulong),('time',ctypes.c_ulong),
                  ('dwExtraInfo',ctypes.c_void_p)]
    class INPUT(ctypes.Structure):
        class _I(ctypes.Union): _fields_=[('ki',KEYBDINPUT)]
        _anonymous_=('_i',); _fields_=[('type',ctypes.c_ulong),('_i',_I)]
    vk = ord(key_char.upper())
    inp = INPUT(type=1); inp.ki.wVk = vk; inp.ki.dwFlags = 0
    ctypes.windll.user32.SendInput(1, ctypes.pointer(inp), ctypes.sizeof(inp))
    time.sleep(0.06)
    inp.ki.dwFlags = 0x0002  # KEYEVENTF_KEYUP
    ctypes.windll.user32.SendInput(1, ctypes.pointer(inp), ctypes.sizeof(inp))
```

**Macro Coller destination (Ctrl+V + Entrée sur tous) :**
```python
# random.uniform(0.07, 0.13) — anti-détection Ankama
for acc in accounts:
    logic.focus_window(acc["hwnd"])
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.08)
    pyautogui.press("enter")
    time.sleep(random.uniform(0.07, 0.13))
```

**Macro Invite groupe :**
```python
# Délai aléatoire — 7 invites en ~1.2s
for friend in friends:
    pyautogui.click(chat_x, chat_y)
    time.sleep(0.04)
    pyperclip.copy(f"/invite {friend}")
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.03)
    pyautogui.press("enter")
    time.sleep(random.uniform(0.08, 0.14))
```

---

### Calibration — calibrator.py

**Overlay PyQt6 centré à l'écran (pas sur la fenêtre Dofus) :**
```python
screen = QApplication.primaryScreen().geometry()
self.move((screen.width()-self.width())//2, (screen.height()-self.height())//2)
```

**Workflow calibration :**
1. Mode `zaap` : pour chaque perso connecté → focus fenêtre → overlay "Calibrer Zaap → Havre-sac" → attendre clic → `abs_to_rel(hwnd, ax, ay)` → sauvegarde
2. Mode `chat` : focus chef → overlay "Calibration Chat" → attendre clic → sauvegarde position absolue `[x, y]`
3. Mode `all` : zaap puis chat

**Attente du clic :**
```python
def _wait_click(self, hwnd, timeout=30):
    # Attendre relâchement bouton actuel
    while win32api.GetAsyncKeyState(0x01) & 0x8000: time.sleep(0.02)
    time.sleep(0.15)
    while self._running and time.time()-start < timeout:
        if self.overlay._skip_requested: return None
        if win32api.GetAsyncKeyState(0x01) & 0x8000:
            x, y = win32api.GetCursorPos()
            while win32api.GetAsyncKeyState(0x01) & 0x8000: time.sleep(0.02)
            return x, y
        time.sleep(0.02)
```

---

### Zaap Favoris — zaap_favorites.py + zaap_data.py

**43 destinations pré-chargées** (zaap_data.py) :
```python
ZAAPS = [
    {"name": "Cité d'Astrub",    "region": "Astrub",         "coords": [5, -18]},
    {"name": "Village d'Amakna", "region": "Amakna",         "coords": [-2, 0]},
    {"name": "La Cuirasse",      "region": "Brâkmar",        "coords": [-26, 37]},
    # ... 40 autres
]
```

**Macro complète vers destination :**
```
Phase 1 : H à N fenêtres (rapide)
Phase 2 : clic zaap à N (après 1s)
Phase 3 : pyperclip.copy(destination_name) + Ctrl+A + Ctrl+V + Entrée à N
```

---

### Char Selector — char_selector.py

**Grille rectangulaire 3×3 :**
- 8 persos dans les 8 cases (positions (0,0)(0,1)(0,2)(1,0)(1,2)(2,0)(2,1)(2,2))
- Logo DofusTeam au centre (1,1)
- Centré à l'écran, fenêtre transparente
- Surlignage ACC du perso actif
- Signal `char_selected` → `logic.switch_to_name()`

---

## PROJET 2 — Hunt Tool (Chasse au trésor Dofus)

### Contexte
Outil HTML/JS standalone pour la chasse au trésor in-game Dofus.
Reverse-engineeré depuis dofusdb.fr via Chrome MCP extension.

### APIs confirmées (CORS natif, pas de proxy)

**Endpoint 1 — Indices de chasse :**
```
GET https://api.dofusdb.fr/treasure-hunt
  ?x=4&y=-15&direction=0&$limit=50&lang=fr

Réponse :
{
  total: N,
  data: [{
    id: mapId,          // ID de la map
    posX: 4, posY: -15,
    distance: 1,        // nombre de maps depuis position
    pois: [{ id, name: { fr: "Zaap" } }]
  }]
}

Directions : 0=Est  1=Sud  2=Ouest  3=Nord
```

**Endpoint 2 — Zaap le plus proche d'une map :**
```
GET https://api.dofusdb.fr/transport-from-maps
  ?id=MAPID&$sort=distance&lang=fr

Réponse :
{
  total: N,
  data: [{
    hint: { x, y, name: { fr: "Cité d'Astrub" }, img: "URL" },
    distance: 3
  }]
}
```

### Architecture Hunt Tool

**Fichiers :**
```
hunt/
├── api.js      # fetchHints(x,y,dir) + fetchNearestZaap(mapId)
├── engine.js   # copyTravel(x,y) → commande /travel
├── ui.js       # initUI(container) → interface complète
├── hints.js    # Dictionnaire {id: "Nom du POI"} — 228 indices
└── style.css   # DA DofusTeam
```

**api.js — fetchHints :**
```javascript
export async function fetchHints(x, y, direction) {
  const params = new URLSearchParams({ x, y, direction, '$limit': 50, lang: 'fr' });
  const res = await fetch(`https://api.dofusdb.fr/treasure-hunt?${params}`);
  const data = await res.json();

  // Flatten : une entrée par POI par map
  const hints = [];
  for (const map of data.data) {
    for (const poi of (map.pois || [])) {
      hints.push({
        mapId: map.id, x: map.posX, y: map.posY,
        dist: map.distance, poiId: poi.id,
        poiName: poi.name?.fr ?? `Indice #${poi.id}`
      });
    }
  }
  return hints.sort((a,b) => a.dist - b.dist);
}

export async function fetchNearestZaap(mapId) {
  const params = new URLSearchParams({ id: mapId, '$sort': 'distance', lang: 'fr' });
  const res = await fetch(`https://api.dofusdb.fr/transport-from-maps?${params}`);
  const data = await res.json();
  const entry = data?.data?.[0];
  if (!entry) return null;
  return {
    name: entry.hint?.name?.fr,
    x: entry.hint?.x, y: entry.hint?.y,
    dist: entry.distance, img: entry.hint?.img
  };
}
```

**engine.js — commande travel :**
```javascript
export function copyTravel(x, y) {
  const cmd = `/travel ${x},${y}`;
  navigator.clipboard.writeText(cmd);
}
```

**ui.js — flux principal :**
```javascript
// 1. User entre X, Y → direction → hint dropdown apparaît
// 2. User sélectionne l'indice dans le dropdown
// 3. fetchHints(x, y, dir) → liste d'indices filtrée par search
// 4. User valide → fetchNearestZaap(mapId) → affiche zaap + commande /travel
// 5. Copie /travel dans le clipboard au clic
```

**hints.js — dictionnaire POI :**
```javascript
export const HINTS = {
  0: "Zaap",
  1: "Zaapi",
  2: "Atelier du sculpteur",
  // ... 228 entrées (IDs numériques → noms français)
  80: "Zaap",
  81: "Zaapi",
  // à compléter avec les 228 entrées réelles du jeu
};
```

---

## Règles techniques communes

### Suppression fond noir images PNG (Pillow)
```python
from PIL import Image
import numpy as np
from scipy import ndimage

img = Image.open(path).convert('RGBA')
data = np.array(img)
r,g,b,a = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]
mask = (r.astype(int)<30) & (g.astype(int)<30) & (b.astype(int)<30)
# Flood fill depuis les bords (ne supprime que le fond, pas l'intérieur)
seed = np.zeros(mask.shape, bool)
seed[0,:] = seed[-1,:] = seed[:,0] = seed[:,-1] = True
bg = seed & mask; changed = True
while changed:
    exp = ndimage.binary_dilation(bg) & mask; changed = (exp!=bg).any(); bg=exp
data[bg, 3] = 0
Image.fromarray(data).save(path)
```

### Classes Dofus (19)
```
Cra, Ecaflip, Eliotrope, Eniripsa, Enutrof, Feca, Forgelance,
Huppermage, Iop, Osamodas, Ouginak, Pandawa, Roublard, Sacrieur,
Sadida, Sram, Steamer, Xelor, Zobal
```

### Teams (5)
```python
TEAMS = ["", "Team 1", "Team 2", "Team 3", "Team 4"]
```

### Format kamas (JS)
```javascript
function fmtN(v) {
  if(v>=1000000) return (v/1000000).toFixed(2)+' M';
  if(v>=1000)    return (v/1000).toFixed(1)+' k';
  return Math.round(v)+'';
}
```

---

## Problèmes connus & solutions

| Problème | Cause | Solution |
|----------|-------|----------|
| Alt+Tab quand Tab hotkey | Ancienne méthode Alt+Down dans focus_window | AttachThreadInput sans Alt |
| Plus possible de taper texte | `suppress=True` sur hotkeys | **Toujours `suppress=False`** |
| Fenêtre non détectée | Titre pas "Pseudo - Classe" ou mauvaise classe | Debug button liste toutes fenêtres visibles |
| H key ignorée par Unity | Focus pas confirmé avant envoi | Boucle GetForegroundWindow() + SendInput |
| Doublons dans scan | Même perso matche 2 titres | Dédoublonnage par nom avant tri |
| pygame ne s'installe pas | setuptools obsolète | `pip install --upgrade setuptools wheel` avant pygame |

---

*Dernière mise à jour : DofusTeam Beta V1.01 — mai 2026*
