# Damas — 2 jogadores locais

Repositório: https://github.com/GabrielVictorLopes/jogo_de_damas

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
No menu é possível ligar/desligar: comer obrigatório, lei da maioria, pedra captura para trás, dama voadora e **dicas de jogadas** (padrão: regras oficiais, dicas ligadas). Com as dicas desligadas o jogo não destaca destinos possíveis, peças que podem mover nem peças que serão capturadas; só avisa "Lance inválido" quando o lance não vale.

## Lado, tabuleiros e partidas salvas
- O Jogador 1 escolhe jogar de **Brancas ou Pretas** (as Brancas sempre começam). Quem joga de Pretas fica embaixo: o tabuleiro gira 180°.
- 8 tabuleiros com textura própria: Madeira, Mármore, Neon, Gelo, Pedra, Feltro, Retrô e Pergaminho (o Neon, o Gelo e o Retrô também mudam as cores das peças).
- Cada lance é gravado num banco **SQLite** (`damas.db`, em `%APPDATA%\JogoDeDamas` no Windows). Ao fechar o jogo, a partida em andamento fica salva: no menu, **Continuar partida salva** retoma tabuleiro, turno, placar, tempo, regras e lado (já em pausa).
- **Histórico de partidas** (menu): data, jogadores, placar, resultado e tempo de cada partida; as em andamento têm o botão Continuar.

## Controles
Clique na peça (contorno azul = pode mover) e depois no destino. **P** ou **Esc** pausa a partida (Continuar, Reiniciar ou Menu). **F2** carrega um final de jogo curto para demonstração: as Brancas vencem em 3 lances. Passe o mouse para ver destinos e peças que serão capturadas. `Menu` (no menu de pausa ou na tela final) volta à tela inicial. Escolha o tabuleiro no menu, ou troque durante a partida no botão `Tema` ou na tecla `T`.

## Estrutura
```
main.py            ponto de entrada
checkers/          domínio (sem dependência gráfica)
  board.py         Color, Piece, Move, Board
  rules.py         geração de lances legais
  positions.py     posição de final de jogo para demonstração
  game.py          Player, Game (turno, pontuação, cronômetro, fim, salvar/retomar)
  storage.py       GameStore: banco SQLite com histórico e partidas salvas
ui/                apresentação (Pygame, 60 FPS)
  app.py           laço principal e troca de telas
  screens.py       MenuScreen, HistoryScreen, MatchScreen, EndScreen
  widgets.py       Button, TextInput, Toggle, Choice
  animation.py     MoveAnimation (interpolação linear)
  transform.py     Vector2D e Transform2D (matrizes 3x3: tela/mundo, rotação, escala)
  theme.py         paleta, tipografia e os 8 tabuleiros com textura
tests/test_rules.py  testes automatizados CT01–CT11, CT15–CT17 e CT19–CT22
```
