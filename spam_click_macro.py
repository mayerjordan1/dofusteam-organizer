"""
DofusTeam — spam_click_macro.py
Macro "Spam clic" : un clic gauche (à la position actuelle du curseur), puis
switch de fenêtre, puis clic gauche à nouveau, etc. sur tous les persos actifs.
Même pattern que recall_macro.quick_recall_potion / inventaire_macro.quick_inventaire,
déclenché via un raccourci clavier dédié (à définir dans Raccourcis) plutôt
qu'un bouton à maintenir.
"""
import time, threading

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    PYAUTOGUI_OK = True
except ImportError:
    PYAUTOGUI_OK = False

try:
    import win32gui
    WINDOWS = True
except ImportError:
    WINDOWS = False


def quick_spam_click(config, logic, on_status=None, on_done=None):
    """Pour chaque perso actif : focus (avec confirmation) + clic gauche à la
    position actuelle du curseur. Revient sur le chef à la fin."""
    if not PYAUTOGUI_OK:
        if on_status: on_status("❌ module pyautogui manquant")
        if on_done: on_done()
        return

    def _run():
        try:
            accounts = logic.get_cycle_list()
            if not accounts:
                if on_status: on_status("⚠ Aucun compte actif")
                return

            if on_status: on_status(f"🖱 Spam clic sur {len(accounts)} perso(s)...")
            # _focus_lock : cette macro ne bloque pas le clavier/souris (pas de
            # BlockInput comme les macros zaap), donc un Tab (switch_next) pressé
            # pendant son exécution tombait en pleine course avec son propre
            # focus_window() — les deux threads se marchaient dessus sur
            # SetForegroundWindow, d'où des gels/sautes de fenêtre ressentis
            # comme moins fluides qu'un switch Tab seul seul.
            with logic._focus_lock:
                for acc in accounts:
                    hwnd = acc["hwnd"]
                    logic.focus_window(hwnd)
                    for _ in range(15):
                        try:
                            if win32gui.GetForegroundWindow() == hwnd: break
                        except Exception:
                            pass
                        time.sleep(0.1)
                    time.sleep(0.08)
                    try:
                        pyautogui.click()
                    except Exception as e:
                        if on_status: on_status(f"⚠ Spam clic {acc['name']}: {e}")
                    time.sleep(0.15)

            logic.switch_to_leader()
            if on_status: on_status("✅ Spam clic envoyé à tous !")
        finally:
            if on_done: on_done()

    threading.Thread(target=_run, daemon=True).start()
