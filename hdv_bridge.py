"""Pont local entre l'Organizer et le site DofusTeam (page « Contribution au marché »).

L'Organizer cadre la zone des prix de l'HDV à l'écran et envoie chaque capture à la page du site ouverte dans le
navigateur : le site lit les prix (même lecture que le dépôt de fichiers) et renvoie le résultat, affiché ici en
animation. Rien n'est enregistré côté communauté tant que tu ne valides pas la liste sur le site.

Sécurité : le serveur n'écoute que sur 127.0.0.1 et refuse toute page dont l'origine n'est pas dans la liste.
Protocole (JSON) :
  site → app  {"type": "hello", "site": "dofusteam"}
  app → site  {"type": "capture", "id": "...", "image": "data:image/png;base64,..."}
  site → app  {"type": "result", "id": "...", "status": "found|notfound|ambiguous|error", "name": "...",
               "icon": "https://...", "prices": {"1": 0, "10": 0, ...}, "total": N}
"""
import asyncio, base64, json, threading

from PyQt6.QtCore import QObject, pyqtSignal

PORT = 47653
DEFAULT_ORIGINS = [
    "https://dofusteam.fr", "https://www.dofusteam.fr",
    "http://localhost:3000", "http://127.0.0.1:3000",
]

try:
    from websockets.asyncio.server import serve as _serve
    WEBSOCKETS_OK = True
except Exception:  # bibliothèque absente ou trop ancienne
    _serve = None
    WEBSOCKETS_OK = False


class HdvBridge(QObject):
    """Serveur WebSocket local (thread dédié). Les signaux sont émis depuis ce thread : Qt les remet dans le bon fil."""
    connection_changed = pyqtSignal(int)   # nombre de pages du site connectées
    result_received    = pyqtSignal(dict)  # résultat de lecture d'une capture
    failed             = pyqtSignal(str)

    def __init__(self, origins=None, parent=None):
        super().__init__(parent)
        self._origins = list(origins or DEFAULT_ORIGINS)
        self._loop = None
        self._thread = None
        self._clients = []          # ordre de connexion : la page la plus récente reçoit les captures
        self._stop = None

    @property
    def running(self):
        return self._thread is not None and self._thread.is_alive()

    def start(self):
        if not WEBSOCKETS_OK:
            self.failed.emit("Module « websockets » manquant : lance install.bat pour l'installer.")
            return False
        if self.running:
            return True
        self._thread = threading.Thread(target=self._run, name="hdv-bridge", daemon=True)
        self._thread.start()
        return True

    def stop(self):
        if self._loop and self._stop is not None:
            self._loop.call_soon_threadsafe(self._stop.set)
        self._thread = None

    # ── Envoi d'une capture (appelable depuis n'importe quel fil) ─────────────
    def send_capture(self, capture_id, png_bytes):
        if not self._loop or not self._clients:
            return False
        payload = json.dumps({
            "type": "capture", "id": capture_id,
            "image": "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii"),
        })
        asyncio.run_coroutine_threadsafe(self._broadcast(payload), self._loop)
        return True

    @property
    def client_count(self):
        return len(self._clients)

    # ── Interne ───────────────────────────────────────────────────────────────
    async def _broadcast(self, payload):
        # Une seule page reçoit chaque capture (la plus récemment ouverte), sinon deux onglets lisent la même image
        while self._clients:
            ws = self._clients[-1]
            try:
                await ws.send(payload)
                break
            except Exception:
                self._remove(ws)
        self.connection_changed.emit(len(self._clients))

    def _remove(self, ws):
        if ws in self._clients:
            self._clients.remove(ws)

    async def _handler(self, ws):
        self._clients.append(ws)
        self.connection_changed.emit(len(self._clients))
        try:
            async for raw in ws:
                try:
                    msg = json.loads(raw)
                except Exception:
                    continue
                if msg.get("type") == "result":
                    self.result_received.emit(msg)
        except Exception:
            pass
        finally:
            self._remove(ws)
            self.connection_changed.emit(len(self._clients))

    async def _main(self):
        self._stop = asyncio.Event()
        try:
            async with _serve(self._handler, "127.0.0.1", PORT, origins=self._origins, max_size=16 * 1024 * 1024):
                await self._stop.wait()
        except OSError:
            self.failed.emit(f"Le port {PORT} est déjà utilisé (une autre instance de l'Organizer est peut-être ouverte).")

    def _run(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._main())
        finally:
            self._loop.close()
            self._loop = None
