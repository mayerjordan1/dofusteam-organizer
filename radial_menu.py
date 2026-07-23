"""DofusTeam — radial_menu.py
Menu circulaire pour changer de personnage rapidement (Alt + clic gauche).
Fenetre tkinter transparente superposee au jeu, dessinee sur un Canvas.
"""
import math
import os
import queue
import tkinter as tk

try:
    import win32api
    WINDOWS = True
except Exception:
    WINDOWS = False

from PIL import Image, ImageTk

BG_SLICE = "#1b2130"
BG_ACTIVE = "#21324a"
BG_HOVER = "#ff8a1e"
BORDER = "#2a303a"
BORDER_HOVER = "#ff8a1e"
TEXT = "#f3f4f6"
TEXT_HOVER = "#0f1115"
CENTER_BG = "#151922"


class RadialMenu:
    """Roue circulaire : un slice par personnage actif, survol = surbrillance,
    relachement du clic = focus du personnage sous le curseur."""

    def __init__(self, tk_root, skin_dir, on_select):
        self.on_select = on_select
        self.skin_dir = skin_dir
        self.size = 320
        self.center = self.size / 2
        self.radius_outer = 150
        self.radius_inner = 38

        self.window = tk.Toplevel(tk_root)
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.attributes("-transparentcolor", "magenta")
        self.canvas = tk.Canvas(self.window, width=self.size, height=self.size,
                                 bg="magenta", highlightthickness=0)
        self.canvas.pack()

        self.items = []
        self.slices = []
        self.hovered_index = -1
        self.is_open = False
        self._image_cache = {}
        self._logo_image = None

        logo_path = self.skin_dir / "logo.png"
        if logo_path.exists():
            try:
                img = Image.open(str(logo_path)).resize((40, 40), Image.Resampling.LANCZOS)
                self._logo_image = ImageTk.PhotoImage(img)
            except Exception:
                self._logo_image = None

        self.window.withdraw()

    def _load_class_icon(self, classe):
        if classe in self._image_cache:
            return self._image_cache[classe]
        path = self.skin_dir / f"{classe.lower()}.png"
        if not path.exists():
            return None
        try:
            img = Image.open(str(path)).resize((34, 34), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._image_cache[classe] = photo
            return photo
        except Exception:
            return None

    def show(self, x, y, accounts, current_name=None):
        if not accounts:
            return
        self.items = accounts
        self.current_name = current_name
        self._draw()
        pos_x = int(x - self.center)
        pos_y = int(y - self.center)
        self.window.geometry(f"+{pos_x}+{pos_y}")
        self.window.deiconify()
        self.is_open = True
        self.hovered_index = -1
        self._poll_hover()

    def hide(self):
        if not self.is_open:
            return
        self.is_open = False
        self.window.withdraw()
        if 0 <= self.hovered_index < len(self.items):
            self.on_select(self.items[self.hovered_index]["name"])

    def _draw(self):
        self.canvas.delete("all")
        self.slices.clear()
        n = len(self.items)
        angle_per_item = 360 / n
        bbox = (self.center - self.radius_outer, self.center - self.radius_outer,
                self.center + self.radius_outer, self.center + self.radius_outer)

        for i, item in enumerate(self.items):
            start = 90 - (i + 1) * angle_per_item
            is_active = item["name"] == self.current_name
            fill = BG_ACTIVE if is_active else BG_SLICE
            slice_id = self.canvas.create_arc(bbox, start=start, extent=angle_per_item,
                                               fill=fill, outline=BORDER, width=2)
            self.slices.append(slice_id)

            mid_angle = math.radians(start + angle_per_item / 2)
            cx = self.center + math.cos(mid_angle) * (self.radius_outer * 0.65)
            cy = self.center - math.sin(mid_angle) * (self.radius_outer * 0.65)

            icon = self._load_class_icon(item.get("classe", ""))
            if icon:
                self.canvas.create_image(cx, cy - 12, image=icon)
            label = item["name"][:10]
            self.canvas.create_text(cx, cy + 18, text=label, fill=TEXT,
                                     font=("Segoe UI", 9, "bold"))

        self.canvas.create_oval(self.center - self.radius_inner, self.center - self.radius_inner,
                                 self.center + self.radius_inner, self.center + self.radius_inner,
                                 fill=CENTER_BG, outline=BORDER, width=2)
        if self._logo_image:
            self.canvas.create_image(self.center, self.center, image=self._logo_image)

    def _poll_hover(self):
        if not self.is_open:
            return
        if WINDOWS:
            mx, my = win32api.GetCursorPos()
        else:
            mx, my = self.window.winfo_pointerxy()
        cx = self.window.winfo_rootx() + self.center
        cy = self.window.winfo_rooty() + self.center
        dist = math.hypot(mx - cx, my - cy)

        if dist < self.radius_inner or dist > self.radius_outer:
            self._highlight(-1)
        else:
            dx = mx - cx
            dy = my - cy
            angle = (math.degrees(math.atan2(dx, -dy)) + 360) % 360
            angle_per_item = 360 / len(self.items)
            self._highlight(int(angle // angle_per_item))

        self.window.after(15, self._poll_hover)

    def _highlight(self, index):
        if index == self.hovered_index:
            return
        self.hovered_index = index
        for i, slice_id in enumerate(self.slices):
            is_active = self.items[i]["name"] == self.current_name
            base_fill = BG_ACTIVE if is_active else BG_SLICE
            fill = BG_HOVER if i == index else base_fill
            outline = BORDER_HOVER if i == index else BORDER
            self.canvas.itemconfig(slice_id, fill=fill, outline=outline)


class RadialMenuController:
    """Ecoute Alt + clic gauche global et ouvre la roue au niveau du curseur.

    Le hook `mouse` tourne sur son propre thread d'ecoute (pas le thread tkinter),
    donc les clics detectes sont juste pousses dans une queue. Le pompage reel
    (show/hide sur le Canvas) se fait dans `poll()`, appele depuis la meme
    boucle que `tk_root.update()` pour rester thread-safe avec tkinter.
    """

    def __init__(self, tk_root, config, logic, skin_dir):
        self.config = config
        self.logic = logic
        self.menu = RadialMenu(tk_root, skin_dir, on_select=self._on_select)
        self._mouse_hook = None
        self._active = False
        self._events = queue.Queue()

    def _on_select(self, name):
        self.logic.switch_to_name(name)

    def enable(self):
        if self._active or not self.config.get("radial_menu_active", True):
            return
        try:
            import mouse
        except ImportError:
            print("[radial] module 'mouse' manquant — pip install mouse")
            return
        try:
            import keyboard
        except ImportError:
            print("[radial] module 'keyboard' manquant")
            return
        self._mouse = mouse
        self._keyboard = keyboard

        def _on_click(event):
            if isinstance(event, mouse.ButtonEvent) and event.button == "left":
                if event.event_type == "down" and keyboard.is_pressed("alt"):
                    self._events.put(("show", mouse.get_position()))
                elif event.event_type == "up":
                    self._events.put(("hide", None))

        self._mouse_hook = mouse.hook(_on_click)
        self._active = True

    def poll(self):
        """A appeler depuis la boucle tkinter (meme thread que tk_root.update())."""
        while True:
            try:
                action, payload = self._events.get_nowait()
            except queue.Empty:
                break
            if action == "show":
                x, y = payload
                accounts = self.logic.get_cycle_list()
                fg_name = None
                for a in accounts:
                    if a["hwnd"] == self.logic.leader_hwnd:
                        fg_name = a["name"]
                self.menu.show(x, y, accounts, current_name=fg_name)
            elif action == "hide" and self.menu.is_open:
                self.menu.hide()

    def disable(self):
        if not self._active:
            return
        try:
            self._mouse.unhook(self._mouse_hook)
        except Exception:
            pass
        self._active = False
