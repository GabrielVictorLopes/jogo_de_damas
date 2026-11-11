"""Posições prontas de tabuleiro (usadas na demonstração e nos testes)."""
from .board import Board, Color, Piece


def endgame_demo() -> Board:
    """Final de jogo curto: as Brancas fazem captura dupla com promoção e vencem no lance seguinte.

    1. Brancas: (4,1) x (3,2) x (1,4) → (0,5), vira dama.
    2. Pretas: (5,4) avança para (6,3) ou (6,5).
    3. Brancas: (7,4) captura a última peça preta → vitória.
    """
    b = Board(setup=False)
    for r, c, color in [(4, 1, Color.LIGHT), (7, 4, Color.LIGHT),
                        (3, 2, Color.DARK), (1, 4, Color.DARK), (5, 4, Color.DARK)]:
        b.set(r, c, Piece(color))
    return b
