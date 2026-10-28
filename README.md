# Damas — 2 jogadores locais

Jogo de Damas (regras oficiais brasileiras) em Python 3.10+ com Pygame.

## Executar
```bash
pip install -r requirements.txt
python main.py
```
## Testes
```bash
python -m unittest -v
```
## Regras implementadas
- Tabuleiro 8x8 (matriz bidimensional), pedras andam 1 casa na diagonal para frente.
- Captura obrigatória, simples e múltipla; pedras capturam também para trás.
- Lei da maioria: obrigatório o lance que captura mais peças.
- Promoção a dama ao terminar o lance na última linha; dama anda e captura à distância.
- Vitória: adversário sem peças ou sem lances. Empate: 20 lances seguidos só de damas sem captura.

## Regras configuráveis
No menu é possível ligar/desligar: comer obrigatório, lei da maioria, pedra captura para trás e dama voadora (padrão: regras oficiais).

## Controles
Clique na peça (contorno azul = pode mover) e depois no destino. Passe o mouse para ver destinos e peças que serão capturadas. `Menu` volta à tela inicial. Escolha o tabuleiro (Clássico, Torneio, Oceano, Mármore, Neon) no menu, ou troque durante a partida no botão `Tema` ou na tecla `T`.

## Estrutura
```
main.py            ponto de entrada
checkers/          domínio (sem dependência gráfica)
  board.py         Color, Piece, Move, Board
  rules.py         geração de lances legais
  game.py          Player, Game (turno, pontuação, cronômetro, fim)
ui/                apresentação (Pygame, 60 FPS)
  app.py           laço principal e troca de telas
  screens.py       MenuScreen, MatchScreen, EndScreen
  widgets.py       Button, TextInput
  animation.py     MoveAnimation (interpolação linear)
  theme.py         paleta e tipografia
tests/test_rules.py  casos de teste CT01–CT10
```
# damas
