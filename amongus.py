#!/usr/bin/env python3
"""
Among Us - versión para un jugador hecha con Pygame.

Juegas contra bots en una nave espacial. Como tripulante debes completar
tus tareas y descubrir a los impostores; como impostor debes eliminar a
la tripulación sin que te descubran.

Ejecuta:  python amongus.py
"""
import math
import random
import sys
from collections import deque

import pygame

# --------------------------------------------------------------------------
# Configuración general
# --------------------------------------------------------------------------
SCREEN_W, SCREEN_H = 1280, 720
FPS = 60
TS = 48                      # tamaño de cada casilla del mapa en píxeles
MAP_W, MAP_H = 64, 38        # tamaño del mapa en casillas

NUM_PLAYERS = 8
NUM_IMPOSTORS = 2
TASKS_PER_PLAYER = 5

PLAYER_SPEED = 230
BOT_SPEED = 185
RADIUS = 15                  # radio de colisión de los personajes

KILL_COOLDOWN = 25.0
FIRST_KILL_COOLDOWN = 12.0
VOTE_TIME = 40.0

CREW_VISION = 5.5 * TS
IMPOSTOR_VISION = 7.5 * TS
INTERACT_DIST = 1.3 * TS
KILL_DIST = 1.6 * TS
REPORT_DIST = 2.4 * TS
DARKNESS = 235

PLAYER_COLORS = [
    ("Rojo", (197, 17, 17)),
    ("Azul", (19, 46, 209)),
    ("Verde", (17, 127, 45)),
    ("Rosa", (237, 84, 186)),
    ("Naranja", (239, 125, 13)),
    ("Amarillo", (245, 245, 87)),
    ("Negro", (63, 71, 78)),
    ("Blanco", (214, 224, 240)),
    ("Morado", (107, 47, 187)),
    ("Cian", (56, 254, 220)),
]

# --------------------------------------------------------------------------
# Mapa: habitaciones y pasillos (x, y, ancho, alto) en casillas
# --------------------------------------------------------------------------
ROOMS = {
    "Cafetería": (26, 2, 14, 10),
    "Armas": (46, 3, 9, 7),
    "O2": (44, 14, 7, 6),
    "Navegación": (56, 14, 7, 8),
    "Escudos": (46, 26, 9, 7),
    "Comunicaciones": (36, 30, 8, 6),
    "Almacén": (24, 20, 11, 12),
    "Electricidad": (14, 21, 8, 7),
    "Motor inferior": (2, 26, 8, 8),
    "Reactor": (2, 14, 7, 9),
    "Motor superior": (2, 2, 8, 8),
    "Enfermería": (14, 10, 7, 7),
    "Administración": (36, 18, 7, 6),
}

CORRIDORS = [
    (10, 5, 16, 3),   # Cafetería - Motor superior
    (16, 8, 3, 2),    # Pasillo - Enfermería
    (4, 10, 3, 4),    # Motor superior - Reactor
    (4, 23, 3, 3),    # Reactor - Motor inferior
    (10, 29, 14, 3),  # Motor inferior - Almacén
    (17, 28, 3, 1),   # Pasillo - Electricidad
    (29, 12, 3, 8),   # Cafetería - Almacén
    (40, 5, 6, 3),    # Cafetería - Armas
    (47, 10, 3, 4),   # Armas - O2
    (51, 16, 5, 3),   # O2 - Navegación
    (57, 22, 3, 5),   # Navegación - Escudos
    (55, 27, 5, 3),
    (44, 30, 2, 3),   # Escudos - Comunicaciones
    (35, 20, 1, 3),   # Almacén - Administración
    (35, 30, 1, 2),   # Almacén - Comunicaciones
    (43, 18, 1, 2),   # Administración - O2
]

ROOM_COLORS = {
    "Cafetería": (150, 156, 168),
    "Armas": (120, 128, 140),
    "O2": (110, 150, 150),
    "Navegación": (110, 125, 160),
    "Escudos": (135, 130, 150),
    "Comunicaciones": (125, 135, 120),
    "Almacén": (140, 130, 110),
    "Electricidad": (130, 130, 100),
    "Motor inferior": (120, 115, 120),
    "Reactor": (115, 120, 140),
    "Motor superior": (120, 115, 120),
    "Enfermería": (125, 160, 170),
    "Administración": (130, 140, 120),
}
CORRIDOR_COLOR = (95, 100, 110)
WALL_COLOR = (55, 60, 78)
WALL_FACE = (85, 92, 112)

TASK_NAMES = {
    "wires": "Arreglar cables",
    "download": "Descargar datos",
    "sequence": "Desbloquear colectores",
    "calibrate": "Calibrar distribuidor",
}

TASK_SPOTS = [
    ("Cafetería", "wires", (27, 3)),
    ("Cafetería", "download", (38, 10)),
    ("Armas", "calibrate", (53, 4)),
    ("O2", "sequence", (45, 15)),
    ("Navegación", "download", (61, 17)),
    ("Navegación", "calibrate", (61, 20)),
    ("Escudos", "sequence", (53, 31)),
    ("Comunicaciones", "download", (42, 34)),
    ("Almacén", "wires", (25, 30)),
    ("Almacén", "sequence", (33, 21)),
    ("Electricidad", "wires", (15, 22)),
    ("Electricidad", "calibrate", (20, 26)),
    ("Motor inferior", "calibrate", (3, 32)),
    ("Reactor", "sequence", (3, 18)),
    ("Motor superior", "calibrate", (3, 3)),
    ("Enfermería", "download", (19, 15)),
    ("Administración", "wires", (41, 19)),
]

VENT_GROUPS = [
    [(8, 8), (7, 21), (8, 27)],          # Motores y reactor
    [(15, 15), (18, 23)],                # Enfermería y electricidad
    [(47, 8), (57, 15), (47, 27)],       # Armas, navegación y escudos
    [(37, 3), (38, 22)],                 # Cafetería y administración
]

BUTTON_TILE = (33, 7)


def build_grid():
    grid = [[1] * MAP_W for _ in range(MAP_H)]
    for (x, y, w, h) in list(ROOMS.values()) + CORRIDORS:
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                grid[yy][xx] = 0
    return grid


GRID = build_grid()


def is_wall(tx, ty):
    return tx < 0 or ty < 0 or tx >= MAP_W or ty >= MAP_H or GRID[ty][tx] == 1


def room_at_tile(tx, ty):
    for name, (x, y, w, h) in ROOMS.items():
        if x <= tx < x + w and y <= ty < y + h:
            return name
    return "Pasillo"


def room_at(px, py):
    return room_at_tile(int(px // TS), int(py // TS))


def tile_center(t):
    return ((t[0] + 0.5) * TS, (t[1] + 0.5) * TS)


def room_center(name):
    x, y, w, h = ROOMS[name]
    return (x + w // 2, y + h // 2)


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def shade(color, f):
    return tuple(max(0, min(255, int(c * f))) for c in color)


def bfs(start, goal):
    """Camino más corto entre dos casillas (movimiento en 4 direcciones)."""
    if start == goal:
        return [start]
    prev = {start: None}
    q = deque([start])
    while q:
        cur = q.popleft()
        if cur == goal:
            break
        x, y = cur
        for nxt in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if nxt not in prev and not is_wall(*nxt):
                prev[nxt] = cur
                q.append(nxt)
    if goal not in prev:
        return []
    path = []
    c = goal
    while c is not None:
        path.append(c)
        c = prev[c]
    path.reverse()
    return path


for _room, _kind, _t in TASK_SPOTS:
    assert not is_wall(*_t) and room_at_tile(*_t) == _room, (_room, _t)
for _g in VENT_GROUPS:
    for _t in _g:
        assert not is_wall(*_t), _t


# --------------------------------------------------------------------------
# Dibujo de los personajes
# --------------------------------------------------------------------------
_bean_cache = {}


def bean_surface(color, facing=1, leg=0, kind="alive"):
    """Devuelve la superficie de un tripulante ('alive', 'ghost' o 'dead')."""
    key = (color, facing, leg, kind)
    if key in _bean_cache:
        return _bean_cache[key]
    s = pygame.Surface((60, 64), pygame.SRCALPHA)
    dark = shade(color, 0.6)
    outline = (15, 15, 22)
    visor = (140, 200, 225)
    if kind == "dead":
        pygame.draw.rect(s, dark, (6, 34, 12, 12), border_radius=4)
        pygame.draw.rect(s, outline, (6, 34, 12, 12), 2, border_radius=4)
        pygame.draw.rect(s, color, (16, 44, 11, 12), border_radius=5)
        pygame.draw.rect(s, outline, (16, 44, 11, 12), 2, border_radius=5)
        pygame.draw.rect(s, color, (31, 44, 11, 12), border_radius=5)
        pygame.draw.rect(s, outline, (31, 44, 11, 12), 2, border_radius=5)
        pygame.draw.rect(s, color, (13, 30, 32, 18), border_bottom_left_radius=10,
                         border_bottom_right_radius=10)
        pygame.draw.rect(s, outline, (13, 30, 32, 18), 2, border_bottom_left_radius=10,
                         border_bottom_right_radius=10)
        pygame.draw.ellipse(s, (170, 20, 20), (15, 27, 28, 8))
        bone = (240, 238, 225)
        pygame.draw.rect(s, bone, (26, 18, 7, 12))
        pygame.draw.circle(s, bone, (26, 18), 4)
        pygame.draw.circle(s, bone, (33, 18), 4)
    else:
        pygame.draw.rect(s, dark, (5, 18, 13, 24), border_radius=5)
        pygame.draw.rect(s, outline, (5, 18, 13, 24), 2, border_radius=5)
        if kind == "alive":
            l1, l2 = leg, -leg
            pygame.draw.rect(s, color, (15, 38 + l1, 12, 15), border_radius=5)
            pygame.draw.rect(s, outline, (15, 38 + l1, 12, 15), 2, border_radius=5)
            pygame.draw.rect(s, color, (31, 38 + l2, 12, 15), border_radius=5)
            pygame.draw.rect(s, outline, (31, 38 + l2, 12, 15), 2, border_radius=5)
            pygame.draw.rect(s, color, (13, 4, 32, 44), border_radius=15)
            pygame.draw.rect(s, outline, (13, 4, 32, 44), 2, border_radius=15)
        else:
            pygame.draw.rect(s, color, (13, 4, 32, 40), border_top_left_radius=15,
                             border_top_right_radius=15)
            for i in range(4):
                pygame.draw.circle(s, color, (17 + i * 8, 44), 5)
            pygame.draw.rect(s, outline, (13, 4, 32, 40), 2, border_top_left_radius=15,
                             border_top_right_radius=15)
        pygame.draw.rect(s, shade(color, 0.8), (16, 30, 8, 14), border_radius=4)
        pygame.draw.ellipse(s, visor, (26, 11, 23, 15))
        pygame.draw.ellipse(s, outline, (26, 11, 23, 15), 2)
        pygame.draw.ellipse(s, (235, 250, 255), (36, 14, 9, 5))
    if facing < 0:
        s = pygame.transform.flip(s, True, False)
    if kind == "ghost":
        s.set_alpha(120)
    _bean_cache[key] = s
    return s


# --------------------------------------------------------------------------
# Personajes
# --------------------------------------------------------------------------
class Crewmate:
    def __init__(self, name, color, is_player=False):
        self.name = name
        self.color = color
        self.is_player = is_player
        self.x = self.y = 0.0
        self.alive = True
        self.ejected = False
        self.impostor = False
        self.facing = 1
        self.anim = 0.0
        self.moving = False
        self.tasks = []
        self.done = set()
        self.path = []
        self.wait = 0.0
        self.doing = None
        self.goal_task = None
        self.kill_cd = FIRST_KILL_COOLDOWN
        self.vent_cd = 0.0
        self.target = None
        self.chase_t = 0.0
        self.repath_t = 0.0
        self.risky = False
        self.emergency = 1
        self.suspicion = {}
        self.memory = []
        self.speed = BOT_SPEED * random.uniform(0.9, 1.1)

    @property
    def pos(self):
        return (self.x, self.y)

    def tile(self):
        return (int(self.x // TS), int(self.y // TS))

    def label(self):
        return "Tú" if self.is_player else self.name


# --------------------------------------------------------------------------
# Minijuegos de tareas
# --------------------------------------------------------------------------
class MiniGame:
    W, H = 660, 440

    def __init__(self, title):
        self.rect = pygame.Rect((SCREEN_W - self.W) // 2, (SCREEN_H - self.H) // 2,
                                self.W, self.H)
        self.title = title
        self.complete = False
        self.close_t = 0.8
        self.flash = 0.0

    def handle(self, e):
        pass

    def update(self, dt):
        self.flash = max(0.0, self.flash - dt)
        if self.complete:
            self.close_t -= dt

    def draw_base(self, s, fonts):
        shadow = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 150))
        s.blit(shadow, (0, 0))
        pygame.draw.rect(s, (48, 52, 64), self.rect, border_radius=14)
        border = (230, 60, 60) if self.flash > 0 else (20, 22, 30)
        pygame.draw.rect(s, border, self.rect, 4, border_radius=14)
        t = fonts["small"].render(self.title, True, (240, 240, 240))
        s.blit(t, (self.rect.x + 20, self.rect.y + 14))
        h = fonts["tiny"].render("ESC para salir", True, (170, 170, 180))
        s.blit(h, (self.rect.right - h.get_width() - 20, self.rect.y + 18))

    def draw_complete(self, s, fonts):
        if self.complete:
            t = fonts["mid"].render("¡TAREA COMPLETADA!", True, (90, 255, 120))
            s.blit(t, t.get_rect(center=(self.rect.centerx, self.rect.bottom - 40)))


class WiresGame(MiniGame):
    COLS = [(220, 40, 40), (40, 90, 230), (240, 220, 40), (230, 80, 200)]

    def __init__(self, title):
        super().__init__(title)
        self.right = random.sample(range(4), 4)
        self.connected = set()
        self.sel = None

    def lpos(self, i):
        return (self.rect.x + 90, self.rect.y + 100 + i * 70)

    def rpos(self, j):
        return (self.rect.right - 90, self.rect.y + 100 + j * 70)

    def _left_at(self, p):
        for i in range(4):
            if dist(p, self.lpos(i)) < 28 and i not in self.connected:
                return i
        return None

    def _right_at(self, p):
        for j in range(4):
            if dist(p, self.rpos(j)) < 28:
                return j
        return None

    def handle(self, e):
        if self.complete:
            return
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            i = self._left_at(e.pos)
            if i is not None:
                self.sel = i
                return
            j = self._right_at(e.pos)
            if j is not None and self.sel is not None:
                self._try_connect(j)
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1 and self.sel is not None:
            j = self._right_at(e.pos)
            if j is not None:
                self._try_connect(j)
            elif self._left_at(e.pos) != self.sel:
                self.sel = None

    def _try_connect(self, j):
        if self.right[j] == self.sel:
            self.connected.add(self.sel)
            if len(self.connected) == 4:
                self.complete = True
        else:
            self.flash = 0.3
        self.sel = None

    def draw(self, s, fonts):
        self.draw_base(s, fonts)
        for i, c in enumerate(self.COLS):
            p = self.lpos(i)
            pygame.draw.rect(s, (30, 30, 35), (p[0] - 60, p[1] - 12, 50, 24))
            pygame.draw.rect(s, c, (p[0] - 60, p[1] - 9, 50, 18))
            pygame.draw.circle(s, c, p, 14)
        for j, ci in enumerate(self.right):
            p = self.rpos(j)
            c = self.COLS[ci]
            pygame.draw.rect(s, (30, 30, 35), (p[0] + 10, p[1] - 12, 50, 24))
            pygame.draw.rect(s, c, (p[0] + 10, p[1] - 9, 50, 18))
            pygame.draw.circle(s, c, p, 14)
        for i in self.connected:
            j = self.right.index(i)
            pygame.draw.line(s, self.COLS[i], self.lpos(i), self.rpos(j), 12)
        if self.sel is not None:
            pygame.draw.line(s, self.COLS[self.sel], self.lpos(self.sel),
                             pygame.mouse.get_pos(), 12)
        h = fonts["tiny"].render("Une cada cable con el de su mismo color", True,
                                 (200, 200, 210))
        s.blit(h, h.get_rect(center=(self.rect.centerx, self.rect.y + 60)))
        self.draw_complete(s, fonts)


class DownloadGame(MiniGame):
    def __init__(self, title):
        super().__init__(title)
        self.progress = 0.0
        self.running = False
        self.button = pygame.Rect(0, 0, 220, 60)
        self.button.center = (self.rect.centerx, self.rect.y + 300)

    def handle(self, e):
        if (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1
                and self.button.collidepoint(e.pos) and not self.running):
            self.running = True

    def update(self, dt):
        super().update(dt)
        if self.running and not self.complete:
            self.progress = min(1.0, self.progress + dt / 6.0)
            if self.progress >= 1.0:
                self.complete = True

    def draw(self, s, fonts):
        self.draw_base(s, fonts)
        r = self.rect
        # carpetas
        for k, x in enumerate((r.x + 120, r.right - 180)):
            pygame.draw.rect(s, (230, 190, 70), (x, r.y + 90, 60, 45), border_radius=4)
            pygame.draw.rect(s, (200, 160, 50), (x, r.y + 82, 26, 12), border_radius=3)
        if self.running and not self.complete:
            t = (pygame.time.get_ticks() / 600.0) % 1.0
            fx = r.x + 160 + t * (r.width - 340)
            pygame.draw.rect(s, (240, 240, 240), (fx, r.y + 100, 18, 22))
        bar = pygame.Rect(r.x + 60, r.y + 190, r.width - 120, 34)
        pygame.draw.rect(s, (20, 20, 25), bar, border_radius=6)
        fill = bar.copy()
        fill.width = int(bar.width * self.progress)
        pygame.draw.rect(s, (70, 220, 100), fill, border_radius=6)
        pct = fonts["tiny"].render(f"{int(self.progress * 100)}%", True, (255, 255, 255))
        s.blit(pct, pct.get_rect(center=bar.center))
        if not self.running:
            pygame.draw.rect(s, (60, 140, 220), self.button, border_radius=10)
            t = fonts["small"].render("Descargar", True, (255, 255, 255))
            s.blit(t, t.get_rect(center=self.button.center))
        self.draw_complete(s, fonts)


class SequenceGame(MiniGame):
    def __init__(self, title):
        super().__init__(title)
        self.nums = random.sample(range(1, 11), 10)
        self.next = 1
        self.buttons = []
        for i in range(10):
            col, row = i % 5, i // 5
            rr = pygame.Rect(0, 0, 90, 90)
            rr.topleft = (self.rect.x + 70 + col * 106, self.rect.y + 110 + row * 110)
            self.buttons.append(rr)

    def handle(self, e):
        if self.complete or not (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1):
            return
        for rr, n in zip(self.buttons, self.nums):
            if rr.collidepoint(e.pos):
                if n == self.next:
                    self.next += 1
                    if self.next > 10:
                        self.complete = True
                elif n >= self.next:
                    self.next = 1
                    self.flash = 0.35

    def draw(self, s, fonts):
        self.draw_base(s, fonts)
        h = fonts["tiny"].render("Pulsa los números del 1 al 10 en orden", True,
                                 (200, 200, 210))
        s.blit(h, h.get_rect(center=(self.rect.centerx, self.rect.y + 70)))
        for rr, n in zip(self.buttons, self.nums):
            on = n < self.next
            pygame.draw.rect(s, (60, 200, 90) if on else (90, 100, 120), rr, border_radius=8)
            pygame.draw.rect(s, (20, 20, 30), rr, 3, border_radius=8)
            t = fonts["mid"].render(str(n), True, (255, 255, 255))
            s.blit(t, t.get_rect(center=rr.center))
        self.draw_complete(s, fonts)


class CalibrateGame(MiniGame):
    def __init__(self, title):
        super().__init__(title)
        self.row = 0
        self.t = 0.0
        self.speeds = [random.uniform(0.7, 1.0), random.uniform(1.0, 1.3),
                       random.uniform(1.3, 1.6)]
        self.zones = [random.uniform(0.2, 0.8) for _ in range(3)]
        self.zone_w = 0.16

    def marker(self):
        return (math.sin(self.t * self.speeds[self.row] * math.pi) + 1) / 2

    def press(self):
        if self.complete:
            return
        if abs(self.marker() - self.zones[self.row]) <= self.zone_w / 2:
            self.row += 1
            self.t = 0.0
            if self.row >= 3:
                self.row = 2
                self.complete = True
        else:
            self.flash = 0.35

    def handle(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
            self.press()
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self.press()

    def update(self, dt):
        super().update(dt)
        if not self.complete:
            self.t += dt

    def draw(self, s, fonts):
        self.draw_base(s, fonts)
        h = fonts["tiny"].render("Pulsa ESPACIO (o clic) cuando el indicador esté en la zona verde",
                                 True, (200, 200, 210))
        s.blit(h, h.get_rect(center=(self.rect.centerx, self.rect.y + 70)))
        for i in range(3):
            bar = pygame.Rect(self.rect.x + 70, self.rect.y + 120 + i * 85, self.W - 140, 40)
            pygame.draw.rect(s, (25, 25, 30), bar, border_radius=6)
            z = pygame.Rect(0, bar.y, int(bar.width * self.zone_w), bar.height)
            z.centerx = bar.x + int(bar.width * self.zones[i])
            pygame.draw.rect(s, (60, 200, 90), z)
            done = i < self.row or self.complete
            if i == self.row and not self.complete:
                mx = bar.x + int(bar.width * self.marker())
                pygame.draw.rect(s, (255, 255, 255), (mx - 4, bar.y - 6, 8, bar.height + 12))
            if done:
                t = fonts["small"].render("OK", True, (90, 255, 120))
                s.blit(t, (bar.right + 10, bar.y + 8))
            pygame.draw.rect(s, (15, 15, 20), bar, 3, border_radius=6)
        self.draw_complete(s, fonts)


MINIGAMES = {
    "wires": WiresGame,
    "download": DownloadGame,
    "sequence": SequenceGame,
    "calibrate": CalibrateGame,
}


# --------------------------------------------------------------------------
# Juego
# --------------------------------------------------------------------------
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Among Us - Pygame")
        self.clock = pygame.time.Clock()
        self.fonts = {
            "huge": pygame.font.Font(None, 110),
            "big": pygame.font.Font(None, 72),
            "mid": pygame.font.Font(None, 44),
            "small": pygame.font.Font(None, 32),
            "tiny": pygame.font.Font(None, 24),
        }
        self.stars = [(random.randrange(SCREEN_W), random.randrange(SCREEN_H),
                       random.choice((1, 1, 2))) for _ in range(160)]
        self.map_surf = self.render_map()
        self.light_cache = {}
        self.state = "menu"
        self.players = []
        self.player = None
        self.time = 0.0

    # ------------------------------------------------------------------ setup
    def render_map(self):
        surf = pygame.Surface((MAP_W * TS, MAP_H * TS))
        surf.fill((6, 6, 18))
        rnd = random.Random(7)
        for _ in range(900):
            surf.set_at((rnd.randrange(MAP_W * TS), rnd.randrange(MAP_H * TS)),
                        (200, 200, 220))
        for ty in range(MAP_H):
            for tx in range(MAP_W):
                r = pygame.Rect(tx * TS, ty * TS, TS, TS)
                if not is_wall(tx, ty):
                    col = ROOM_COLORS.get(room_at_tile(tx, ty), CORRIDOR_COLOR)
                    if (tx + ty) % 2:
                        col = shade(col, 0.93)
                    pygame.draw.rect(surf, col, r)
                    pygame.draw.rect(surf, shade(col, 0.85), r, 1)
                else:
                    near = any(not is_wall(tx + dx, ty + dy)
                               for dx in (-1, 0, 1) for dy in (-1, 0, 1))
                    if near:
                        pygame.draw.rect(surf, WALL_COLOR, r)
                        if not is_wall(tx, ty + 1):
                            pygame.draw.rect(surf, WALL_FACE, (r.x, r.y + TS // 3, TS, TS * 2 // 3))
                            pygame.draw.line(surf, shade(WALL_FACE, 1.25), (r.x, r.y + TS // 3),
                                             (r.right, r.y + TS // 3), 3)
        font = pygame.font.Font(None, 40)
        for name, (x, y, w, h) in ROOMS.items():
            t = font.render(name.upper(), True, (255, 255, 255))
            t.set_alpha(90)
            surf.blit(t, t.get_rect(center=((x + w / 2) * TS, (y + h / 2) * TS)))
        for _room, _kind, t in TASK_SPOTS:
            cx, cy = tile_center(t)
            pygame.draw.rect(surf, (70, 75, 90), (cx - 18, cy - 20, 36, 32), border_radius=4)
            pygame.draw.rect(surf, (60, 190, 210), (cx - 13, cy - 15, 26, 16), border_radius=2)
            pygame.draw.rect(surf, (25, 25, 35), (cx - 18, cy - 20, 36, 32), 2, border_radius=4)
        for group in VENT_GROUPS:
            for t in group:
                cx, cy = tile_center(t)
                vr = pygame.Rect(0, 0, 38, 26)
                vr.center = (cx, cy)
                pygame.draw.rect(surf, (60, 64, 70), vr, border_radius=4)
                for i in range(4):
                    pygame.draw.line(surf, (30, 32, 36), (vr.x + 6 + i * 8, vr.y + 4),
                                     (vr.x + 6 + i * 8, vr.bottom - 4), 3)
                pygame.draw.rect(surf, (25, 25, 30), vr, 2, border_radius=4)
        bx, by = tile_center(BUTTON_TILE)
        pygame.draw.circle(surf, (110, 115, 130), (int(bx), int(by)), 34)
        pygame.draw.circle(surf, (40, 40, 50), (int(bx), int(by)), 34, 3)
        pygame.draw.circle(surf, (210, 30, 30), (int(bx), int(by)), 15)
        pygame.draw.circle(surf, (255, 120, 120), (int(bx) - 4, int(by) - 4), 5)
        return surf

    def spawn_positions(self):
        cx, cy = tile_center(BUTTON_TILE)
        for i, c in enumerate(self.players):
            a = i / len(self.players) * math.tau
            c.x = cx + math.cos(a) * 2.4 * TS
            c.y = cy + math.sin(a) * 2.2 * TS
            c.path = []
            c.wait = 0.0
            c.doing = None
            c.goal_task = None
            c.target = None

    def new_game(self, role):
        colors = random.sample(PLAYER_COLORS, NUM_PLAYERS)
        self.players = [Crewmate(n, c, i == 0) for i, (n, c) in enumerate(colors)]
        self.player = self.players[0]
        bots = self.players[1:]
        if role == "impostor":
            imps = [self.player] + random.sample(bots, NUM_IMPOSTORS - 1)
        elif role == "crew":
            imps = random.sample(bots, NUM_IMPOSTORS)
        else:
            imps = random.sample(self.players, NUM_IMPOSTORS)
        for c in imps:
            c.impostor = True
        for c in self.players:
            c.tasks = random.sample(range(len(TASK_SPOTS)), TASKS_PER_PLAYER)
        self.tasks_total = sum(len(c.tasks) for c in self.players if not c.impostor)
        self.tasks_done = 0
        self.bodies = []
        self.toasts = []
        self.minigame = None
        self.show_map = False
        self.death_timer = 0.0
        self.killer_of_player = None
        self.meeting = None
        self.time = 0.0
        self.spawn_positions()
        self.state = "reveal"
        self.reveal_t = 4.0

    # ---------------------------------------------------------------- helpers
    def toast(self, text, t=2.5):
        self.toasts.append([text, t])

    def alive_crew(self):
        return [c for c in self.players if c.alive and not c.impostor]

    def alive_impostors(self):
        return [c for c in self.players if c.alive and c.impostor]

    def collides(self, x, y):
        for ty in range(int((y - RADIUS) // TS), int((y + RADIUS) // TS) + 1):
            for tx in range(int((x - RADIUS) // TS), int((x + RADIUS) // TS) + 1):
                if is_wall(tx, ty):
                    return True
        return False

    def move_player(self, c, dx, dy):
        if not c.alive:
            c.x = max(TS, min(MAP_W * TS - TS, c.x + dx))
            c.y = max(TS, min(MAP_H * TS - TS, c.y + dy))
            return
        c.x += dx
        if self.collides(c.x, c.y):
            c.x -= dx
        c.y += dy
        if self.collides(c.x, c.y):
            c.y -= dy

    def nearest_vent(self, c, maxd):
        best, bd = None, maxd
        for gi, group in enumerate(VENT_GROUPS):
            for vi, t in enumerate(group):
                d = dist(c.pos, tile_center(t))
                if d < bd:
                    best, bd = (gi, vi), d
        return best

    def near_task(self, c):
        if c.impostor:
            return None
        for ti in c.tasks:
            if ti not in c.done and dist(c.pos, tile_center(TASK_SPOTS[ti][2])) < INTERACT_DIST:
                return ti
        return None

    def near_button(self, c):
        return c.alive and dist(c.pos, tile_center(BUTTON_TILE)) < INTERACT_DIST * 1.3

    def near_body(self, c):
        for b in self.bodies:
            if dist(c.pos, (b["x"], b["y"])) < REPORT_DIST:
                return b
        return None

    def kill_target(self, c):
        best, bd = None, KILL_DIST
        for o in self.alive_crew():
            d = dist(c.pos, o.pos)
            if d < bd:
                best, bd = o, d
        return best

    # ------------------------------------------------------------- acciones
    def kill(self, killer, victim):
        victim.alive = False
        victim.path = []
        victim.wait = 0.0
        victim.doing = None
        victim.goal_task = None
        room = room_at(victim.x, victim.y)
        self.bodies.append({"victim": victim, "x": victim.x, "y": victim.y, "room": room})
        killer.kill_cd = KILL_COOLDOWN
        killer.x, killer.y = victim.x, victim.y
        for o in self.alive_crew():
            if not o.is_player and dist(o.pos, killer.pos) < 6 * TS:
                o.suspicion[killer] = o.suspicion.get(killer, 0) + 100
                o.memory.append(f"¡Vi a {killer.label()} matar a {victim.label()} en {room}!")
        if victim.is_player:
            self.minigame = None
            self.show_map = False
            self.death_timer = 3.0
            self.killer_of_player = killer
        self.check_win()

    def do_vent(self, c, vent):
        gi, vi = vent
        group = VENT_GROUPS[gi]
        src = tile_center(group[vi])
        dst_t = group[(vi + 1) % len(group)]
        dst = tile_center(dst_t)
        for o in self.alive_crew():
            if not o.is_player and (dist(o.pos, src) < 5 * TS or dist(o.pos, dst) < 5 * TS):
                o.suspicion[c] = o.suspicion.get(c, 0) + 100
                o.memory.append(f"¡Vi a {c.label()} usar una ventila en {room_at(*dst)}!")
        c.x, c.y = dst
        c.path = []
        c.vent_cd = 1.0

    def use(self):
        p = self.player
        if self.near_button(p) and self.state == "play":
            if p.emergency > 0:
                p.emergency -= 1
                self.start_meeting(p, None)
            else:
                self.toast("Ya usaste tu reunión de emergencia")
            return
        ti = self.near_task(p)
        if ti is not None:
            room, kind, _t = TASK_SPOTS[ti]
            self.minigame = (MINIGAMES[kind](f"{TASK_NAMES[kind]} - {room}"), ti)

    # ------------------------------------------------------------- reuniones
    def start_meeting(self, reporter, body):
        self.state = "meeting"
        self.minigame = None
        self.show_map = False
        alive = [c for c in self.players if c.alive]
        lines = []
        if body:
            v = body["victim"]
            lines.append((reporter, f"¡Encontré el cuerpo de {v.label()} en {body['room']}!"))
            for b in alive:
                if b.is_player:
                    continue
                for o in alive:
                    if (o is not b and o is not reporter
                            and dist(o.pos, (body["x"], body["y"])) < 6 * TS):
                        b.suspicion[o] = b.suspicion.get(o, 0) + 15
        else:
            lines.append((reporter, "¡Reunión de emergencia! Tenemos que hablar."))
        room_names = list(ROOMS.keys())
        for b in random.sample(alive, len(alive)):
            if b.is_player:
                continue
            if b.memory:
                for m in b.memory:
                    lines.append((b, m))
            elif random.random() < 0.6:
                room = room_at(b.x, b.y)
                if b.impostor and random.random() < 0.5:
                    room = random.choice(room_names)
                if room == "Pasillo":
                    room = random.choice(room_names)
                lines.append((b, random.choice([
                    f"Yo estaba en {room}.",
                    f"Estaba haciendo tareas en {room}.",
                    f"Vengo de {room}, no vi nada raro.",
                ])))
            else:
                others = [o for o in alive if o is not b]
                sus = random.choice(others)
                if random.random() < 0.5:
                    b.suspicion[sus] = b.suspicion.get(sus, 0) + 10
                    lines.append((b, f"{sus.label()} me parece sospechoso..."))
                else:
                    lines.append((b, random.choice(["No vi nada.", "¿Quién fue?",
                                                    "Saltemos el voto si no hay pruebas.",
                                                    "Yo soy inocente, lo juro."])))
            b.memory = []
        self.meeting = {
            "reporter": reporter,
            "body": body,
            "lines": lines,
            "shown": 1,
            "line_t": 1.2,
            "timer": VOTE_TIME,
            "votes": {},
            "vote_at": {b: random.uniform(8, VOTE_TIME * 0.75) for b in alive if not b.is_player},
            "phase": "vote",
            "result_t": 0.0,
        }

    def bot_vote(self, b):
        m = self.meeting
        alive = [c for c in self.players if c.alive and c is not b]
        tally = {}
        for t in m["votes"].values():
            if t != "skip":
                tally[t] = tally.get(t, 0) + 1
        if b.impostor:
            crew_votes = [(n, t) for t, n in tally.items() if not t.impostor]
            if crew_votes and random.random() < 0.7:
                return max(crew_votes, key=lambda x: x[0])[1]
            if random.random() < 0.3:
                return random.choice([c for c in alive if not c.impostor])
            return "skip"
        if not alive:
            return "skip"
        score, best = max(((b.suspicion.get(c, 0), c) for c in alive), key=lambda x: x[0])
        if score >= 50:
            return best
        if score >= 10 and random.random() < 0.5:
            return best
        if tally and random.random() < 0.35:
            return max(tally.items(), key=lambda x: x[1])[0]
        return "skip"

    def player_vote(self, pos):
        m = self.meeting
        p = self.player
        if m["phase"] != "vote" or not p.alive or p in m["votes"]:
            return
        if self.skip_rect().collidepoint(pos):
            m["votes"][p] = "skip"
            return
        for c, rect in self.card_rects():
            if rect.collidepoint(pos) and c.alive and c is not p:
                m["votes"][p] = c
                return

    def do_eject(self):
        tally = {}
        for t in self.meeting["votes"].values():
            tally[t] = tally.get(t, 0) + 1
        ejected = None
        if tally:
            top = max(tally.values())
            tops = [k for k, n in tally.items() if n == top]
            if len(tops) == 1 and tops[0] != "skip":
                ejected = tops[0]
        if ejected:
            ejected.alive = False
            ejected.ejected = True
            who = "Fuiste expulsado." if ejected.is_player else ""
            role = "era un impostor." if ejected.impostor else "no era un impostor."
            self.eject_text = f"{ejected.label()} {role}"
            self.eject_sub = who
        else:
            self.eject_text = "Nadie fue expulsado. (Empate o voto saltado)"
            self.eject_sub = ""
        n = len(self.alive_impostors())
        self.eject_sub2 = f"Queda{'n' if n != 1 else ''} {n} impostor{'es' if n != 1 else ''}."
        self.ejected = ejected
        self.state = "eject"
        self.eject_t = 5.0

    def end_meeting(self):
        self.bodies = []
        self.meeting = None
        self.spawn_positions()
        for c in self.players:
            if c.impostor:
                c.kill_cd = max(c.kill_cd, KILL_COOLDOWN * 0.6)
        self.state = "play"
        self.check_win()

    def check_win(self):
        if self.state in ("gameover", "menu"):
            return
        imps = len(self.alive_impostors())
        crew = len(self.alive_crew())
        if imps == 0:
            self.game_over("crew", "Todos los impostores fueron expulsados.")
        elif imps >= crew:
            self.game_over("impostor", "Los impostores eliminaron a la tripulación.")
        elif self.tasks_done >= self.tasks_total:
            self.game_over("crew", "La tripulación completó todas las tareas.")

    def game_over(self, winner, reason):
        if self.state in ("meeting", "eject") and self.meeting is not None:
            return  # se comprobará al terminar la reunión
        self.state = "gameover"
        self.winner = winner
        self.win_reason = reason
        self.minigame = None

    # ------------------------------------------------------------------ bots
    def follow_path(self, b, dt):
        if not b.path:
            b.moving = False
            return
        tx, ty = tile_center(b.path[0])
        dx, dy = tx - b.x, ty - b.y
        d = math.hypot(dx, dy)
        step = b.speed * dt
        if d <= step:
            b.x, b.y = tx, ty
            b.path.pop(0)
        else:
            b.x += dx / d * step
            b.y += dy / d * step
        if abs(dx) > 1:
            b.facing = 1 if dx > 0 else -1
        b.moving = True
        b.anim += dt * 12

    def bot_routine(self, b, dt):
        """Rutina de tareas (real para tripulantes, falsa para impostores)."""
        if b.wait > 0:
            b.wait -= dt
            b.moving = False
            if b.wait <= 0 and b.doing is not None:
                if b.doing not in b.done:
                    b.done.add(b.doing)
                    if not b.impostor:
                        self.tasks_done += 1
                b.doing = None
            return
        if b.path:
            self.follow_path(b, dt)
            if not b.path:
                if b.goal_task is not None:
                    b.doing = b.goal_task
                    b.goal_task = None
                    b.wait = random.uniform(3.0, 6.0)
                else:
                    b.wait = random.uniform(0.5, 3.0)
            return
        pending = [t for t in b.tasks if t not in b.done]
        if b.impostor and not pending:
            b.done.clear()
            pending = list(b.tasks)
        if pending:
            t = random.choice(pending)
            b.goal_task = t
            b.path = bfs(b.tile(), TASK_SPOTS[t][2])
        else:
            b.path = bfs(b.tile(), room_center(random.choice(list(ROOMS))))

    def update_bot(self, b, dt):
        if b.impostor and b.alive:
            self.update_impostor(b, dt)
        else:
            self.bot_routine(b, dt)

    def update_impostor(self, b, dt):
        if b.target is not None:
            t = b.target
            b.chase_t -= dt
            if not t.alive or b.chase_t <= 0:
                b.target = None
                b.path = []
                return
            if dist(b.pos, t.pos) < KILL_DIST * 0.7:
                witnesses = [o for o in self.alive_crew()
                             if o is not t and dist(o.pos, b.pos) < 6 * TS]
                b.target = None
                b.path = []
                if witnesses and not b.risky:
                    b.kill_cd = 4.0
                    return
                self.kill(b, t)
                if self.state != "play":
                    return
                vent = self.nearest_vent(b, 3.5 * TS)
                if vent and random.random() < 0.5:
                    self.do_vent(b, vent)
                return
            b.repath_t -= dt
            if b.repath_t <= 0 or not b.path:
                b.path = bfs(b.tile(), t.tile())
                b.repath_t = 0.4
            self.follow_path(b, dt)
            return
        if b.kill_cd <= 0:
            crew = self.alive_crew()
            for t in sorted(crew, key=lambda c: dist(c.pos, b.pos)):
                if dist(t.pos, b.pos) > 6 * TS:
                    break
                others = [o for o in crew if o is not t and dist(o.pos, t.pos) < 7 * TS]
                if not others:
                    b.target = t
                    b.chase_t = 7.0
                    b.risky = random.random() < 0.15
                    b.wait = 0
                    b.doing = None
                    b.goal_task = None
                    b.path = []
                    return
        self.bot_routine(b, dt)

    # ---------------------------------------------------------------- eventos
    def handle_event(self, e):
        if self.state == "menu":
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                roles = {pygame.K_1: "random", pygame.K_KP1: "random",
                         pygame.K_RETURN: "random", pygame.K_2: "crew",
                         pygame.K_KP2: "crew", pygame.K_3: "impostor", pygame.K_KP3: "impostor"}
                if e.key in roles:
                    self.new_game(roles[e.key])
        elif self.state == "reveal":
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.reveal_t = 0
        elif self.state == "play":
            if self.minigame:
                mg, _ti = self.minigame
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    self.minigame = None
                else:
                    mg.handle(e)
                return
            if e.type != pygame.KEYDOWN:
                return
            p = self.player
            if e.key == pygame.K_ESCAPE:
                if self.show_map:
                    self.show_map = False
                else:
                    self.state = "menu"
            elif e.key == pygame.K_m or e.key == pygame.K_TAB:
                self.show_map = not self.show_map
            elif e.key == pygame.K_e:
                self.use()
            elif e.key == pygame.K_r and p.alive:
                body = self.near_body(p)
                if body:
                    self.start_meeting(p, body)
            elif e.key == pygame.K_q and p.alive and p.impostor and p.kill_cd <= 0:
                t = self.kill_target(p)
                if t:
                    self.kill(p, t)
            elif e.key == pygame.K_v and p.alive and p.impostor and p.vent_cd <= 0:
                vent = self.nearest_vent(p, INTERACT_DIST)
                if vent:
                    self.do_vent(p, vent)
        elif self.state == "meeting":
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                self.player_vote(e.pos)
        elif self.state == "eject":
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.eject_t = 0
        elif self.state == "gameover":
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE,
                                                       pygame.K_ESCAPE):
                self.state = "menu"

    # ---------------------------------------------------------------- update
    def update(self, dt):
        self.time += dt
        if self.state == "reveal":
            self.reveal_t -= dt
            if self.reveal_t <= 0:
                self.state = "play"
                self.toast("¡Buena suerte!")
        elif self.state == "play":
            self.update_play(dt)
        elif self.state == "meeting":
            self.update_meeting(dt)
        elif self.state == "eject":
            self.eject_t -= dt
            if self.eject_t <= 0:
                self.end_meeting()

    def update_play(self, dt):
        for c in self.players:
            c.kill_cd = max(0.0, c.kill_cd - dt)
            c.vent_cd = max(0.0, c.vent_cd - dt)
        for tst in self.toasts:
            tst[1] -= dt
        self.toasts = [t for t in self.toasts if t[1] > 0]
        self.death_timer = max(0.0, self.death_timer - dt)

        p = self.player
        if self.minigame:
            mg, ti = self.minigame
            mg.update(dt)
            if mg.complete and mg.close_t <= 0:
                if ti not in p.done:
                    p.done.add(ti)
                    self.tasks_done += 1
                self.minigame = None
                self.toast("Tarea completada")
        else:
            keys = pygame.key.get_pressed()
            dx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
            dy = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
            if dx or dy:
                n = math.hypot(dx, dy)
                speed = PLAYER_SPEED * (1.25 if not p.alive else 1.0)
                self.move_player(p, dx / n * speed * dt, dy / n * speed * dt)
                if dx:
                    p.facing = 1 if dx > 0 else -1
                p.moving = True
                p.anim += dt * 12
            else:
                p.moving = False

        for b in self.players[1:]:
            self.update_bot(b, dt)
            if self.state != "play":
                return

        # los tripulantes vivos reportan cadáveres que ven
        for b in self.players[1:]:
            if not b.alive or b.impostor:
                continue
            for body in self.bodies:
                d = dist(b.pos, (body["x"], body["y"]))
                if d < 2 * TS or (d < 4.5 * TS and room_at(b.x, b.y) == body["room"]):
                    self.start_meeting(b, body)
                    return
        self.check_win()

    def update_meeting(self, dt):
        m = self.meeting
        if m["phase"] == "vote":
            m["timer"] -= dt
            m["line_t"] -= dt
            if m["line_t"] <= 0 and m["shown"] < len(m["lines"]):
                m["shown"] += 1
                m["line_t"] = 1.3
            elapsed = VOTE_TIME - m["timer"]
            for b, t in m["vote_at"].items():
                if b.alive and b not in m["votes"] and elapsed >= t:
                    m["votes"][b] = self.bot_vote(b)
            alive = [c for c in self.players if c.alive]
            if m["timer"] <= 0 or all(c in m["votes"] for c in alive):
                m["phase"] = "results"
                m["result_t"] = 4.0
                m["shown"] = len(m["lines"])
        else:
            m["result_t"] -= dt
            if m["result_t"] <= 0:
                self.do_eject()

    # ------------------------------------------------------------------ draw
    def draw(self):
        s = self.screen
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "reveal":
            self.draw_reveal()
        elif self.state == "play":
            self.draw_world()
            self.draw_hud()
            if self.show_map:
                self.draw_minimap()
            if self.minigame:
                self.minigame[0].draw(s, self.fonts)
            if self.death_timer > 0:
                self.draw_death()
        elif self.state == "meeting":
            self.draw_meeting()
        elif self.state == "eject":
            self.draw_eject()
        elif self.state == "gameover":
            self.draw_gameover()

    def draw_space(self):
        self.screen.fill((4, 4, 14))
        for x, y, r in self.stars:
            xx = (x - self.time * 20 * r) % SCREEN_W
            pygame.draw.circle(self.screen, (220, 220, 240), (int(xx), y), r)

    def text(self, txt, font, color, center=None, topleft=None, shadow=True):
        f = self.fonts[font]
        img = f.render(txt, True, color)
        rect = img.get_rect()
        if center:
            rect.center = center
        if topleft:
            rect.topleft = topleft
        if shadow:
            sh = f.render(txt, True, (0, 0, 0))
            self.screen.blit(sh, rect.move(2, 2))
        self.screen.blit(img, rect)
        return rect

    def draw_bean(self, c, x, y, kind=None, scale=1.0):
        if kind is None:
            kind = "alive" if c.alive else "ghost"
        leg = int(round(math.sin(c.anim) * 3)) if (c.moving and kind == "alive") else 0
        img = bean_surface(c.color, c.facing, leg, kind)
        if scale != 1.0:
            img = pygame.transform.smoothscale(img, (int(60 * scale), int(64 * scale)))
        self.screen.blit(img, (x - img.get_width() // 2, y - int(38 * scale)))

    def get_light(self, radius):
        radius = int(radius)
        if radius not in self.light_cache:
            size = radius * 2
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            surf.fill((0, 0, 0, DARKNESS))
            inner = radius * 0.7
            for r in range(radius, 0, -3):
                a = DARKNESS if r >= radius else max(0, DARKNESS * (r - inner) / (radius - inner))
                pygame.draw.circle(surf, (0, 0, 0, int(a)), (radius, radius), r)
            self.light_cache[radius] = surf
        return self.light_cache[radius]

    def draw_world(self):
        s = self.screen
        p = self.player
        cam_x = max(0, min(MAP_W * TS - SCREEN_W, p.x - SCREEN_W / 2))
        cam_y = max(0, min(MAP_H * TS - SCREEN_H, p.y - SCREEN_H / 2))
        self.cam = (cam_x, cam_y)
        s.blit(self.map_surf, (0, 0), pygame.Rect(cam_x, cam_y, SCREEN_W, SCREEN_H))

        # marcadores de tareas pendientes
        if not p.impostor:
            near = self.near_task(p)
            for ti in p.tasks:
                if ti in p.done:
                    continue
                cx, cy = tile_center(TASK_SPOTS[ti][2])
                sx, sy = cx - cam_x, cy - cam_y
                if -50 < sx < SCREEN_W + 50 and -50 < sy < SCREEN_H + 50:
                    col = (255, 240, 60)
                    pygame.draw.rect(s, col, (sx - 20, sy - 22, 40, 36), 3, border_radius=5)
                    if ti == near:
                        pygame.draw.rect(s, (255, 255, 255), (sx - 24, sy - 26, 48, 44), 2,
                                         border_radius=7)
                    bob = math.sin(self.time * 5) * 4
                    self.text("!", "mid", col, center=(sx, sy - 40 + bob))
        if self.near_button(p):
            bx, by = tile_center(BUTTON_TILE)
            pygame.draw.circle(s, (255, 240, 60), (int(bx - cam_x), int(by - cam_y)), 38, 3)

        vision = IMPOSTOR_VISION if p.impostor else CREW_VISION

        def visible(x, y):
            return not p.alive or dist(p.pos, (x, y)) < vision + 30

        for b in self.bodies:
            if visible(b["x"], b["y"]):
                img = bean_surface(b["victim"].color, 1, 0, "dead")
                s.blit(img, (b["x"] - cam_x - 30, b["y"] - cam_y - 38))

        drawables = []
        for c in self.players:
            if c.ejected and not c.is_player:
                continue
            if not c.alive and not c.is_player and p.alive:
                continue  # los fantasmas solo los ven otros fantasmas
            if c is not p and not visible(c.x, c.y):
                continue
            drawables.append(c)
        drawables.sort(key=lambda c: c.y)
        for c in drawables:
            sx, sy = c.x - cam_x, c.y - cam_y
            if not (-60 < sx < SCREEN_W + 60 and -60 < sy < SCREEN_H + 60):
                continue
            if c.alive:
                sh = pygame.Rect(0, 0, 36, 12)
                sh.center = (sx, sy + 18)
                pygame.draw.ellipse(s, (45, 45, 55), sh)
            self.draw_bean(c, sx, sy)
            name_col = (255, 255, 255)
            if p.impostor and c.impostor:
                name_col = (255, 60, 60)
            self.text(c.label(), "tiny", name_col, center=(sx, sy - 48))

        if p.alive:
            dark = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            dark.fill((0, 0, 0, DARKNESS))
            light = self.get_light(vision)
            dark.blit(light, (p.x - cam_x - vision, p.y - cam_y - vision),
                      special_flags=pygame.BLEND_RGBA_MIN)
            s.blit(dark, (0, 0))

    def draw_button(self, label, key, x, y, enabled, extra=None):
        r = pygame.Rect(x, y, 110, 70)
        col = (235, 235, 235) if enabled else (90, 90, 95)
        pygame.draw.rect(self.screen, (20, 20, 26), r, border_radius=12)
        pygame.draw.rect(self.screen, col, r, 3, border_radius=12)
        self.text(label, "tiny", col, center=(r.centerx, r.centery - 10))
        self.text(f"[{key}]", "tiny", col, center=(r.centerx, r.centery + 14))
        if extra:
            self.text(extra, "mid", (255, 90, 90), center=r.center)

    def draw_hud(self):
        s = self.screen
        p = self.player
        # barra de tareas
        bar = pygame.Rect(20, 16, 420, 28)
        pygame.draw.rect(s, (25, 30, 25), bar, border_radius=4)
        fill = bar.copy()
        fill.width = int(bar.width * (self.tasks_done / max(1, self.tasks_total)))
        pygame.draw.rect(s, (60, 210, 90), fill, border_radius=4)
        pygame.draw.rect(s, (10, 10, 10), bar, 3, border_radius=4)
        self.text("TAREAS TOTALES", "tiny", (255, 255, 255), center=bar.center)

        # lista de tareas
        panel = pygame.Surface((420, 30 + 26 * len(p.tasks)), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 130))
        s.blit(panel, (20, 52))
        y = 60
        if p.impostor:
            self.text("IMPOSTOR: mata a los tripulantes.", "tiny", (255, 80, 80), topleft=(30, y))
            y += 26
            for ti in p.tasks:
                room, kind, _ = TASK_SPOTS[ti]
                self.text(f"(Falsa) {room}: {TASK_NAMES[kind]}", "tiny", (200, 160, 160),
                          topleft=(30, y))
                y += 26
        else:
            title = "Tareas (eres un fantasma)" if not p.alive else "Tareas:"
            self.text(title, "tiny", (220, 220, 255), topleft=(30, y))
            y += 26
            for ti in p.tasks:
                room, kind, _ = TASK_SPOTS[ti]
                col = (90, 240, 110) if ti in p.done else (255, 255, 255)
                self.text(f"{room}: {TASK_NAMES[kind]}", "tiny", col, topleft=(30, y))
                y += 26

        # habitación actual y vivos
        room = room_at(p.x, p.y)
        self.text(room, "small", (255, 255, 255), center=(SCREEN_W // 2, SCREEN_H - 30))

        # botones de acción
        bx = SCREEN_W - 130
        by = SCREEN_H - 90
        self.draw_button("USAR", "E", bx, by,
                         self.near_button(p) or self.near_task(p) is not None)
        self.draw_button("REPORTAR", "R", bx - 120, by, p.alive and self.near_body(p) is not None)
        if p.impostor and p.alive:
            cd = f"{int(math.ceil(p.kill_cd))}" if p.kill_cd > 0 else None
            self.draw_button("MATAR", "Q", bx - 240, by,
                             p.kill_cd <= 0 and self.kill_target(p) is not None, cd)
            self.draw_button("VENTILA", "V", bx - 360, by,
                             self.nearest_vent(p, INTERACT_DIST) is not None)
        self.draw_button("MAPA", "M", bx, by - 80, True)

        # mensajes
        for i, (txt, _t) in enumerate(self.toasts[-3:]):
            self.text(txt, "small", (255, 255, 120), center=(SCREEN_W // 2, 90 + i * 34))

    def draw_minimap(self):
        s = self.screen
        k = 14
        w, h = MAP_W * k, MAP_H * k
        ox, oy = (SCREEN_W - w) // 2, (SCREEN_H - h) // 2
        shadow = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        shadow.fill((0, 0, 20, 200))
        s.blit(shadow, (0, 0))
        for ty in range(MAP_H):
            for tx in range(MAP_W):
                if not is_wall(tx, ty):
                    pygame.draw.rect(s, (70, 110, 160), (ox + tx * k, oy + ty * k, k, k))
        for name, (x, y, rw, rh) in ROOMS.items():
            self.text(name, "tiny", (255, 255, 255),
                      center=(ox + (x + rw / 2) * k, oy + (y + rh / 2) * k))
        if not self.player.impostor:
            for ti in self.player.tasks:
                if ti not in self.player.done:
                    tx, ty = TASK_SPOTS[ti][2]
                    pygame.draw.circle(s, (255, 230, 50), (ox + tx * k + k // 2, oy + ty * k + k // 2), 6)
        if self.player.impostor:
            for group in VENT_GROUPS:
                for tx, ty in group:
                    pygame.draw.rect(s, (40, 40, 40), (ox + tx * k + 2, oy + ty * k + 2, k - 4, k - 4))
        p = self.player
        pygame.draw.circle(s, p.color, (int(ox + p.x / TS * k), int(oy + p.y / TS * k)), 8)
        pygame.draw.circle(s, (255, 255, 255), (int(ox + p.x / TS * k), int(oy + p.y / TS * k)), 8, 2)
        self.text("MAPA  (M para cerrar)", "small", (255, 255, 255), center=(SCREEN_W // 2, oy - 20))

    def draw_death(self):
        s = self.screen
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((60, 0, 0, 170))
        s.blit(ov, (0, 0))
        self.text("¡TE HAN ASESINADO!", "big", (255, 60, 60), center=(SCREEN_W // 2, 200))
        k = self.killer_of_player
        if k:
            self.draw_bean(k, SCREEN_W // 2 - 120, 380, "alive", 2.0)
            self.text(k.label(), "small", (255, 255, 255), center=(SCREEN_W // 2 - 120, 460))
        img = pygame.transform.smoothscale(bean_surface(self.player.color, 1, 0, "dead"), (120, 128))
        s.blit(img, (SCREEN_W // 2 + 60, 300))
        self.text("Ahora eres un fantasma: puedes atravesar paredes y terminar tus tareas.",
                  "small", (255, 255, 255), center=(SCREEN_W // 2, 560))

    # ---------------------------------------------------------- reuniones UI
    def card_rects(self):
        out = []
        for i, c in enumerate(self.players):
            col, row = i % 2, i // 2
            out.append((c, pygame.Rect(40 + col * 395, 120 + row * 82, 380, 72)))
        return out

    def skip_rect(self):
        rows = (len(self.players) + 1) // 2
        return pygame.Rect(40, 120 + rows * 82 + 10, 200, 52)

    def draw_meeting(self):
        s = self.screen
        m = self.meeting
        s.fill((30, 40, 75))
        pygame.draw.rect(s, (200, 210, 230), (20, 20, SCREEN_W - 40, SCREEN_H - 40), border_radius=20)
        pygame.draw.rect(s, (60, 70, 100), (28, 28, SCREEN_W - 56, SCREEN_H - 56), border_radius=16)
        if m["body"]:
            title = "¡CADÁVER REPORTADO!"
        else:
            title = "REUNIÓN DE EMERGENCIA"
        self.text(title, "mid", (255, 90, 90), center=(420, 60))
        if m["phase"] == "vote":
            self.text(f"¿Quién es el impostor?   Tiempo: {int(m['timer'])}s", "small",
                      (255, 255, 255), center=(420, 98))
        else:
            self.text("Resultados de la votación", "small", (255, 255, 255), center=(420, 98))

        p = self.player
        my_vote = m["votes"].get(p)
        results = m["phase"] == "results"
        mouse = pygame.mouse.get_pos()
        for c, r in self.card_rects():
            base = (230, 232, 240) if c.alive else (120, 120, 130)
            if (not results and p.alive and p not in m["votes"] and c.alive
                    and c is not p and r.collidepoint(mouse)):
                base = (255, 255, 200)
            pygame.draw.rect(s, base, r, border_radius=10)
            border = (255, 210, 0) if my_vote is c else (30, 30, 40)
            pygame.draw.rect(s, border, r, 4 if my_vote is c else 2, border_radius=10)
            kind = "alive" if c.alive else "dead"
            img = pygame.transform.smoothscale(bean_surface(c.color, 1, 0, kind), (45, 48))
            s.blit(img, (r.x + 8, r.y + 12))
            name_col = (200, 0, 0) if (p.impostor and c.impostor) else (20, 20, 30)
            self.text(c.label(), "small", name_col, topleft=(r.x + 64, r.y + 10), shadow=False)
            if c is m["reporter"]:
                self.text("REPORTÓ", "tiny", (200, 40, 40), topleft=(r.x + 64, r.y + 42), shadow=False)
            if not c.alive:
                pygame.draw.line(s, (200, 0, 0), (r.x + 10, r.y + 12), (r.x + 50, r.y + 60), 5)
                pygame.draw.line(s, (200, 0, 0), (r.x + 50, r.y + 12), (r.x + 10, r.y + 60), 5)
            elif not results and c in m["votes"]:
                self.text("VOTÓ", "tiny", (30, 130, 30), topleft=(r.right - 60, r.y + 10), shadow=False)
            if results:
                voters = [v for v, t in m["votes"].items() if t is c]
                for k, v in enumerate(voters):
                    pygame.draw.circle(s, v.color, (r.x + 180 + k * 26, r.y + 50), 10)
                    pygame.draw.circle(s, (0, 0, 0), (r.x + 180 + k * 26, r.y + 50), 10, 2)
        sk = self.skip_rect()
        pygame.draw.rect(s, (230, 232, 240), sk, border_radius=10)
        pygame.draw.rect(s, (255, 210, 0) if my_vote == "skip" else (30, 30, 40), sk, 3,
                         border_radius=10)
        self.text("SALTAR VOTO", "small", (20, 20, 30), center=sk.center, shadow=False)
        if results:
            voters = [v for v, t in m["votes"].items() if t == "skip"]
            for k, v in enumerate(voters):
                pygame.draw.circle(s, v.color, (sk.right + 20 + k * 26, sk.centery), 10)
                pygame.draw.circle(s, (0, 0, 0), (sk.right + 20 + k * 26, sk.centery), 10, 2)
        if not p.alive:
            self.text("Estás muerto: no puedes votar.", "tiny", (255, 200, 200),
                      topleft=(sk.right + 20, sk.centery - 8))
        elif p not in m["votes"] and not results:
            self.text("Haz clic en un jugador para votar", "tiny", (255, 255, 200),
                      topleft=(sk.right + 20, sk.centery - 8))

        # chat
        chat = pygame.Rect(830, 40, SCREEN_W - 870, SCREEN_H - 80)
        pygame.draw.rect(s, (235, 238, 245), chat, border_radius=12)
        self.text("Chat", "small", (40, 40, 60), topleft=(chat.x + 14, chat.y + 10), shadow=False)
        y = chat.y + 46
        lines = m["lines"][:m["shown"]]
        rendered = []
        for who, msg in lines:
            rendered.append((who, self.wrap(msg, chat.width - 70)))
        total = sum(22 + 22 * len(w) for _, w in rendered)
        while rendered and total > chat.height - 60:
            _, w = rendered.pop(0)
            total -= 22 + 22 * len(w)
        for who, wrapped in rendered:
            img = pygame.transform.smoothscale(bean_surface(who.color, 1, 0, "alive"), (28, 30))
            s.blit(img, (chat.x + 10, y))
            self.text(who.label(), "tiny", shade(who.color, 0.7) if sum(who.color) > 500 else who.color,
                      topleft=(chat.x + 46, y), shadow=False)
            y += 22
            for ln in wrapped:
                self.text(ln, "tiny", (30, 30, 40), topleft=(chat.x + 46, y), shadow=False)
                y += 22
            y += 6

    def wrap(self, msg, width):
        words = msg.split()
        lines, cur = [], ""
        for w in words:
            test = (cur + " " + w).strip()
            if self.fonts["tiny"].size(test)[0] > width and cur:
                lines.append(cur)
                cur = w
            else:
                cur = test
        if cur:
            lines.append(cur)
        return lines

    def draw_eject(self):
        self.draw_space()
        t = 5.0 - self.eject_t
        if self.ejected:
            x = -80 + t / 4.0 * (SCREEN_W + 160)
            img = bean_surface(self.ejected.color, 1, 0, "alive")
            img = pygame.transform.rotozoom(img, -t * 120, 2.0)
            self.screen.blit(img, img.get_rect(center=(x, SCREEN_H // 2 - 40)))
        n = int(min(len(self.eject_text), t * 25))
        self.text(self.eject_text[:n], "mid", (255, 255, 255), center=(SCREEN_W // 2, SCREEN_H // 2 + 90))
        if t > 2.0:
            self.text(self.eject_sub2, "small", (220, 220, 220), center=(SCREEN_W // 2, SCREEN_H // 2 + 140))
            if self.eject_sub:
                self.text(self.eject_sub, "small", (255, 120, 120),
                          center=(SCREEN_W // 2, SCREEN_H // 2 + 180))

    # -------------------------------------------------------------- pantallas
    def draw_menu(self):
        self.draw_space()
        self.text("AMONG US", "huge", (255, 255, 255), center=(SCREEN_W // 2, 120))
        self.text("versión Pygame para un jugador", "small", (200, 200, 220),
                  center=(SCREEN_W // 2, 185))
        for i, (_n, col) in enumerate(PLAYER_COLORS[:8]):
            x = 200 + i * 125
            y = 290 + math.sin(self.time * 2 + i) * 10
            img = bean_surface(col, 1 if i % 2 else -1, 0, "alive")
            img = pygame.transform.smoothscale(img, (90, 96))
            self.screen.blit(img, img.get_rect(center=(x, y)))
        opts = ["[1] / ENTER  -  Rol aleatorio", "[2]  -  Jugar como tripulante",
                "[3]  -  Jugar como impostor"]
        for i, o in enumerate(opts):
            self.text(o, "mid", (255, 255, 120), center=(SCREEN_W // 2, 400 + i * 50))
        ctl = ["WASD / Flechas: moverse     E: usar / tareas / botón de emergencia",
               "R: reportar cadáver     Q: matar (impostor)     V: ventila (impostor)",
               "M: mapa     ESC: salir de tarea / menú"]
        for i, c in enumerate(ctl):
            self.text(c, "tiny", (200, 200, 220), center=(SCREEN_W // 2, 580 + i * 28))

    def draw_reveal(self):
        self.screen.fill((0, 0, 0))
        p = self.player
        if p.impostor:
            self.text("IMPOSTOR", "huge", (255, 40, 40), center=(SCREEN_W // 2, 150))
            mates = [c for c in self.players if c.impostor]
            for i, c in enumerate(mates):
                x = SCREEN_W // 2 + (i - (len(mates) - 1) / 2) * 180
                self.draw_bean(c, x, 380, "alive", 2.4)
                self.text(c.label(), "small", (255, 80, 80), center=(x, 480))
            self.text("Mata a la tripulación sin que te descubran.", "small", (255, 255, 255),
                      center=(SCREEN_W // 2, 580))
        else:
            self.text("TRIPULANTE", "huge", (100, 200, 255), center=(SCREEN_W // 2, 150))
            n = NUM_IMPOSTORS
            self.text(f"Hay {n} impostor{'es' if n != 1 else ''} entre nosotros",
                      "mid", (255, 255, 255), center=(SCREEN_W // 2, 230))
            for i, c in enumerate(self.players):
                x = SCREEN_W // 2 + (i - (len(self.players) - 1) / 2) * 120
                self.draw_bean(c, x, 400, "alive", 1.6 if c.is_player else 1.2)
            self.text("Completa tus tareas y descubre a los impostores.", "small",
                      (255, 255, 255), center=(SCREEN_W // 2, 580))
        self.text("ENTER para continuar", "tiny", (150, 150, 150), center=(SCREEN_W // 2, 660))

    def draw_gameover(self):
        self.screen.fill((0, 0, 0))
        won = (self.winner == "impostor") == self.player.impostor
        self.text("¡VICTORIA!" if won else "DERROTA", "huge",
                  (90, 200, 255) if won else (255, 50, 50), center=(SCREEN_W // 2, 140))
        side = "Ganan los impostores" if self.winner == "impostor" else "Gana la tripulación"
        self.text(side, "mid", (255, 255, 255), center=(SCREEN_W // 2, 220))
        self.text(self.win_reason, "small", (210, 210, 210), center=(SCREEN_W // 2, 265))
        winners = [c for c in self.players if c.impostor == (self.winner == "impostor")]
        for i, c in enumerate(winners):
            x = SCREEN_W // 2 + (i - (len(winners) - 1) / 2) * 140
            self.draw_bean(c, x, 420, "alive" if c.alive else "ghost", 1.8)
            self.text(c.label(), "small", (255, 255, 255), center=(x, 500))
        imps = ", ".join(c.label() for c in self.players if c.impostor)
        self.text(f"Impostores: {imps}", "small", (255, 120, 120), center=(SCREEN_W // 2, 580))
        self.text("ENTER para volver al menú", "tiny", (160, 160, 160), center=(SCREEN_W // 2, 650))

    # ------------------------------------------------------------------- run
    def run(self):
        while True:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                self.handle_event(e)
            self.update(dt)
            self.draw()
            pygame.display.flip()


if __name__ == "__main__":
    Game().run()
