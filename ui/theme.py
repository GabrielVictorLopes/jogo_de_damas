"""Paleta e tipografia."""
import random
import pygame
from .transform import Transform2D

BG = (17, 20, 28)
SURFACE = (29, 33, 45)
SURFACE_HI = (44, 50, 66)
TEXT = (236, 239, 245)
MUTED = (146, 154, 172)
ACCENT = (82, 160, 255)
GOLD = (246, 192, 72)
DANGER = (236, 96, 96)
SQ_LIGHT = (238, 226, 204)
SQ_DARK = (126, 92, 68)
P_LIGHT = (246, 244, 238)
P_LIGHT_EDGE = (196, 190, 178)
P_DARK = (44, 44, 54)
P_DARK_EDGE = (16, 16, 22)

_cache: dict = {}


def font(size: int, bold: bool = False) -> pygame.font.Font:
    key = (size, bold)
    if key not in _cache:
        _cache[key] = pygame.font.SysFont("segoeui,helveticaneue,roboto,arial", size, bold=bold)
    return _cache[key]


def text(surf, msg, size, color, center=None, bold=False, **pos):
    img = font(size, bold).render(str(msg), True, color)
    rect = img.get_rect(center=center) if center else img.get_rect(**pos)
    surf.blit(img, rect)
    return rect


# ---------- Tabuleiros ----------
# Cada tabuleiro tem um ESTILO próprio (textura desenhada por código), não só um par de cores.
# "pieces" (opcional) troca as cores das peças para combinar com o tabuleiro.
BOARD_THEMES = [
    {"name": "Madeira", "style": "madeira", "light": (236, 214, 176), "dark": (140, 94, 58),
     "frame": (74, 48, 30), "rim": (190, 150, 100)},
    {"name": "Mármore", "style": "marmore", "light": (240, 240, 244), "dark": (120, 126, 146),
     "frame": (52, 56, 70), "rim": (200, 204, 214)},
    {"name": "Neon", "style": "neon", "light": (26, 22, 54), "dark": (66, 38, 128),
     "frame": (12, 10, 26), "rim": (130, 90, 255),
     "pieces": {"light": ((150, 245, 255), (40, 160, 200)), "dark": ((255, 110, 210), (150, 30, 110))}},
    {"name": "Gelo", "style": "gelo", "light": (226, 240, 250), "dark": (100, 150, 196),
     "frame": (30, 54, 86), "rim": (170, 210, 240),
     "pieces": {"light": ((250, 252, 255), (150, 190, 220)), "dark": ((36, 60, 110), (14, 26, 56))}},
    {"name": "Pedra", "style": "pedra", "light": (190, 186, 176), "dark": (98, 96, 92),
     "frame": (46, 44, 42), "rim": (150, 146, 138)},
    {"name": "Feltro", "style": "feltro", "light": (232, 224, 190), "dark": (40, 112, 76),
     "frame": (22, 58, 40), "rim": (214, 176, 84)},
    {"name": "Retrô", "style": "retro", "light": (252, 216, 168), "dark": (92, 64, 160),
     "frame": (30, 22, 52), "rim": (252, 216, 168),
     "pieces": {"light": ((255, 248, 160), (200, 160, 40)), "dark": ((226, 70, 84), (110, 20, 40))}},
    {"name": "Pergaminho", "style": "pergaminho", "light": (242, 230, 196), "dark": (180, 140, 96),
     "frame": (88, 58, 36), "rim": (222, 196, 140)},
]


def _shade(color, k):
    return tuple(max(0, min(255, int(v * k))) for v in color[:3])


def _squares(cell):
    """Percorre as 64 casas: (retângulo, é_escura)."""
    for r in range(8):
        for c in range(8):
            yield pygame.Rect(c * cell, r * cell, cell, cell), (r + c) % 2 == 1


def _paint_madeira(s, cell, th, rng):
    for rect, dark in _squares(cell):
        col = th["dark"] if dark else th["light"]
        pygame.draw.rect(s, col, rect)
        for y in range(rect.top + 1, rect.bottom - 1, 3):  # veios da madeira
            k = rng.uniform(0.90, 1.07)
            y2 = y + rng.uniform(-2, 2)
            pygame.draw.line(s, _shade(col, k), (rect.left, y), (rect.right, y2), 1)
        pygame.draw.line(s, _shade(col, 1.15), rect.topleft, rect.topright, 1)    # relevo
        pygame.draw.line(s, _shade(col, 1.15), rect.topleft, rect.bottomleft, 1)
        pygame.draw.line(s, _shade(col, 0.78), rect.bottomleft, rect.bottomright, 1)
        pygame.draw.line(s, _shade(col, 0.78), rect.topright, rect.bottomright, 1)


def _paint_marmore(s, cell, th, rng):
    for rect, dark in _squares(cell):
        col = th["dark"] if dark else th["light"]
        pygame.draw.rect(s, col, rect)
        for _ in range(3):  # veios de pedra
            pts = [(rect.left + rng.uniform(0, cell), rect.top)]
            for i in range(1, 4):
                pts.append((rect.left + rng.uniform(0, cell), rect.top + cell * i / 3))
            k = rng.choice((0.86, 0.92, 1.08))
            pygame.draw.lines(s, _shade(col, k), False, pts, rng.choice((1, 1, 2)))
        pygame.draw.rect(s, _shade(col, 0.94), rect, 1)


def _paint_neon(s, cell, th, rng):
    s.fill((12, 10, 26))
    glow = pygame.Surface(s.get_size(), pygame.SRCALPHA)
    for rect, dark in _squares(cell):
        pygame.draw.rect(s, th["dark"] if dark else th["light"], rect)
        edge = (150, 90, 255) if dark else (60, 200, 230)
        for i, a in enumerate((26, 60, 140)):  # brilho em camadas
            pygame.draw.rect(glow, (*edge, a), rect.inflate(-2 - i * 3, -2 - i * 3), 1)
    s.blit(glow, (0, 0))


def _paint_gelo(s, cell, th, rng):
    for rect, dark in _squares(cell):
        col = th["dark"] if dark else th["light"]
        for y in range(cell):  # degradê vertical
            pygame.draw.line(s, _shade(col, 1.10 - 0.20 * y / cell), (rect.left, rect.top + y), (rect.right - 1, rect.top + y))
        for _ in range(2):  # rachaduras
            x, y = rect.left + rng.uniform(0, cell), rect.top + rng.uniform(0, cell)
            pts = [(x, y)] + [(x + rng.uniform(-cell / 3, cell / 3), y + rng.uniform(-cell / 3, cell / 3)) for _ in range(2)]
            pygame.draw.lines(s, _shade(col, 1.22), False, [(min(max(px, rect.left), rect.right - 1), min(max(py, rect.top), rect.bottom - 1)) for px, py in pts], 1)
        pygame.draw.line(s, (255, 255, 255), (rect.left + 2, rect.top + 1), (rect.right - 3, rect.top + 1), 1)
        pygame.draw.rect(s, _shade(col, 0.85), rect, 1)


def _paint_pedra(s, cell, th, rng):
    for rect, dark in _squares(cell):
        col = th["dark"] if dark else th["light"]
        pygame.draw.rect(s, col, rect)
        for _ in range(cell * cell // 14):  # granulado
            x, y = rect.left + rng.randrange(cell), rect.top + rng.randrange(cell)
            pygame.draw.rect(s, _shade(col, rng.uniform(0.82, 1.15)), (x, y, rng.choice((1, 2)), rng.choice((1, 2))))
        pygame.draw.rect(s, _shade(col, 0.62), rect, 1)  # rejunte


def _paint_feltro(s, cell, th, rng):
    for rect, dark in _squares(cell):
        col = th["dark"] if dark else th["light"]
        pygame.draw.rect(s, col, rect)
        for _ in range(cell * cell // 10):  # fibras do feltro
            x, y = rect.left + rng.randrange(cell), rect.top + rng.randrange(cell)
            pygame.draw.line(s, _shade(col, rng.uniform(0.88, 1.12)), (x, y), (x + rng.choice((0, 1, 2)), y), 1)
    pygame.draw.rect(s, th["rim"], s.get_rect(), 2)  # filete dourado


def _paint_retro(s, cell, th, rng):
    step = max(2, cell // 16)
    for rect, dark in _squares(cell):
        col = th["dark"] if dark else th["light"]
        pygame.draw.rect(s, col, rect)
        alt = _shade(col, 0.88)
        for y in range(0, cell, step):  # pontilhado 8-bit
            for x in range((y // step) % 2 * step, cell, step * 2):
                pygame.draw.rect(s, alt, (rect.left + x, rect.top + y, step, step))
        pygame.draw.rect(s, (20, 14, 34), rect, 2)


def _paint_pergaminho(s, cell, th, rng):
    for rect, dark in _squares(cell):
        col = th["dark"] if dark else th["light"]
        pygame.draw.rect(s, col, rect)
        for _ in range(cell // 2):  # fibras do papel
            x, y = rect.left + rng.randrange(cell), rect.top + rng.randrange(cell)
            pygame.draw.line(s, _shade(col, rng.uniform(0.92, 1.06)), (x, y), (x + rng.randrange(-4, 5), y + rng.randrange(-2, 3)), 1)
        ink = _shade(col, 0.62)
        pygame.draw.rect(s, ink, rect.inflate(-6, -6), 1)  # filete duplo de tinta
        pygame.draw.rect(s, ink, rect.inflate(-10, -10), 1)
        pygame.draw.rect(s, _shade(col, 0.8), rect, 1)


PAINTERS = {"madeira": _paint_madeira, "marmore": _paint_marmore, "neon": _paint_neon, "gelo": _paint_gelo,
            "pedra": _paint_pedra, "feltro": _paint_feltro, "retro": _paint_retro, "pergaminho": _paint_pergaminho}
_boards: dict = {}


def board_surface(th: dict, cell: int) -> "pygame.Surface":
    """Textura do tabuleiro inteiro (8x8 casas), desenhada uma vez e guardada em cache."""
    key = (th["name"], cell)
    if key not in _boards:
        if len(_boards) > 24:
            _boards.clear()
        surf = pygame.Surface((cell * 8, cell * 8))
        PAINTERS[th["style"]](surf, cell, th, random.Random(th["name"]))
        _boards[key] = surf
    return _boards[key]


BG_TOP, BG_BOTTOM = (26, 31, 48), (11, 13, 19)
_bg: dict = {}


def background(surf) -> None:
    """Fundo em degradê com brilho suave (cacheado por tamanho de janela)."""
    size = surf.get_size()
    if size not in _bg:
        g = pygame.Surface(size)
        h = max(1, size[1] - 1)
        for y in range(size[1]):
            t = y / h
            pygame.draw.line(g, [int(a + (b - a) * t) for a, b in zip(BG_TOP, BG_BOTTOM)], (0, y), (size[0], y))
        glow = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.circle(glow, (*ACCENT, 16), (size[0] // 2, 0), int(size[0] * 0.55))
        g.blit(glow, (0, 0))
        _bg.clear()
        _bg[size] = g
    surf.blit(_bg[size], (0, 0))


_shadows: dict = {}


def shadow(surf, rect, radius=14, spread=12, alpha=110) -> None:
    """Sombra suave; é cara de desenhar, então cada tamanho é montado uma vez e reaproveitado."""
    key = (rect.w, rect.h, radius, spread, alpha)
    s = _shadows.get(key)
    if s is None:
        if len(_shadows) > 120:
            _shadows.clear()
        s = pygame.Surface((rect.w + spread * 2, rect.h + spread * 2), pygame.SRCALPHA)
        for i in range(spread):
            pygame.draw.rect(s, (0, 0, 0, alpha // spread), (i, i, s.get_width() - 2 * i, s.get_height() - 2 * i),
                             border_radius=radius + spread - i)
        _shadows[key] = s
    surf.blit(s, (rect.x - spread, rect.y - spread + 6))


_pieces: dict = {}


def _piece_layer(rad, light, king, crown_angle, palette):
    if palette:  # cores de peça próprias do tabuleiro (ex.: Neon)
        body, edge = palette["light" if light else "dark"]
    else:
        body, edge = (P_LIGHT, P_LIGHT_EDGE) if light else (P_DARK, P_DARK_EDGE)
    c = rad + 6
    layer = pygame.Surface((c * 2, c * 2 + 4), pygame.SRCALPHA)
    pygame.draw.circle(layer, (0, 0, 0, 90), (c + 2, c + 5), rad)
    pygame.draw.circle(layer, edge, (c, c), rad)
    pygame.draw.circle(layer, body, (c, c - 3), rad - 2)
    pygame.draw.circle(layer, edge, (c, c - 3), int(rad * 0.70), 2)
    pygame.draw.circle(layer, edge, (c, c - 3), int(rad * 0.45), 1)
    pygame.draw.circle(layer, (255, 255, 255, 55 if light else 30), (c - rad * 0.3, c - rad * 0.4), rad * 0.38)
    if king:
        s, cy = rad * 0.48, c - 3
        base = [(-s, s * 0.55), (-s, -s * 0.45), (-s * 0.5, 0), (0, -s * 0.8),
                (s * 0.5, 0), (s, -s * 0.45), (s, s * 0.55)]
        m = Transform2D.translation(c, cy) @ Transform2D.rotation(crown_angle)
        pts = m.apply_points(base)
        pygame.draw.polygon(layer, GOLD, pts)
        pygame.draw.polygon(layer, (150, 105, 20), pts, 2)
    return layer


def piece(surf, center, rad, light: bool, king=False, alpha=255, scale=1.0, crown_angle=0.0, palette=None) -> None:
    """Peça com sombra, relevo, sulcos e brilho; coroa dourada para dama.

    scale e crown_angle animam a promoção: a coroa é transformada pela matriz
    T(centro) · R(ângulo) · S(escala) aplicada aos vértices do polígono.
    Sem animação, o desenho é guardado em cache (60 FPS sem recriar 24 superfícies por quadro).
    """
    rad = max(4, int(rad * scale))
    c = rad + 6
    animated = crown_angle != 0.0
    key = (rad, light, king, id(palette) if palette else 0)
    layer = None if animated else _pieces.get(key)
    if layer is None:
        layer = _piece_layer(rad, light, king, crown_angle, palette)
        if not animated:
            if len(_pieces) > 200:
                _pieces.clear()
            _pieces[key] = layer
    if alpha < 255:
        layer = layer.copy()
        layer.set_alpha(alpha)
    surf.blit(layer, (int(center[0]) - c, int(center[1]) - c))
