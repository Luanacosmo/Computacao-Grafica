# Procurando o Tesouro — Jardim dos Tesouros

Trabalho de Computação Gráfica em Python, PyOpenGL e Pygame.

Interface em tema de jardim: creme e verde-sálvia, com detalhes rosa e lavanda. A matriz representa a área de exploração de uma mina de diamantes sob o jardim. As regras de exploração e pontuação foram preservadas. Todo o cenário e os itens são modelados em OpenGL; não é uma imagem de fundo.

![Prévia do jardim](previa_jardim.png)

## Executar no Windows

Instale Python 3.11 ou 3.12 e extraia o ZIP. Abra o terminal na pasta dos arquivos:

```powershell
py -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python main.py
```

No Linux, com OpenGL e GLU disponíveis:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

No Ubuntu, se as bibliotecas gráficas não estiverem disponíveis: `sudo apt install libgl1 libglu1-mesa`. A janela usa 1280 × 800 pixels e requer OpenGL de compatibilidade 2.1 ou superior. No notebook, prefira executar diretamente no Windows com o driver da placa de vídeo atualizado. Não são necessárias imagens baixadas nem arquivos de áudio/modelos.

## Como jogar

1. Escolha 2, 3 ou 4 jogadores no menu e clique em **Entrar no jardim**.
2. O jogador ativo aparece no painel. Seu avatar começa fora da mina, junto a uma entrada. A borda laranja identifica as casas adjacentes disponíveis.
3. Clique em uma dessas casas ou use as setas do teclado. As setas correspondem às linhas e colunas da matriz, independentemente da rotação da câmera. Não há movimento diagonal.
4. Entrar em uma casa oculta revela seu item, marca a casa com a cor do jogador e passa a vez. Em uma casa explorada, o turno continua e o item não é coletado novamente.
5. Ao revelar as 36 casas, o jogo exibe o vencedor ou todos os empatados. O painel mantém o ranking e permite reiniciar ou voltar ao menu.

A câmera gira e inclina ao arrastar o botão direito. A roda aproxima/afasta. O painel também oferece botões de rotação e zoom. `Esc` pausa/continua. Menus e seleção de jogadores são gráficos; não existe escolha de teclas na abertura.

## Distribuição e pontuação

| Item | Quantidade | Efeito |
|---|---:|---|
| Diamante azul | 30 | Soma entre 1 e 10 quilates, sorteados individualmente |
| Pista verde — Prossiga | 2 | Soma 3 quilates |
| Túnel de terracota | 2 | Desconta 10 quilates ao sair da casa |
| Esconderijo — baú | 2 | Oculta o avatar até sua próxima descoberta e desconta 5 de cada oponente |

As posições são embaralhadas a cada partida. O conteúdo oculto não é desenhado. Após uma descoberta, o item e a marca de propriedade permanecem visíveis. Os diamantes exibem seu valor acima do modelo. Cada avatar tem cor, número e acessório próprios; o número desaparece junto com o avatar invisível. O ranking continua visível.

## Decisões para pontos não especificados pelo enunciado

- Como 36 × 5% = 1,8 e 36 × 10% = 3,6, foi adotado arredondamento para o inteiro mais próximo: 2 pistas (5,56%) e 4 armadilhas (11,11%), divididas entre os dois tipos. As casas restantes têm diamantes; os tipos são exclusivos por casa.
- Uma jogada significa **uma descoberta**. Atravessar casas já abertas usa somente passos adjacentes e não consome descoberta. Isso evita bloqueios e assegura 18, 12 ou 9 descobertas por participante. Os avatares não bloqueiam casas uns dos outros.
- As entradas iniciais ficam fora do tabuleiro, ao lado dos cantos, evitando conceder itens antes do primeiro turno.
- A penalidade do túnel é cobrada apenas na saída após sua primeira descoberta. Ao terminar a partida, todos saem da mina e qualquer penalidade pendente é cobrada antes do ranking final.
- A invisibilidade dura até o jogador descobrir outra casa; pode atravessar casas abertas sem reaparecer. A identificação histórica das casas permanece.
- São permitidos pontos negativos, para descontar integralmente as penalidades. Empates são anunciados como vitória conjunta.

Essas decisões completam lacunas do PDF; caso o professor prefira outra interpretação, devem ser ajustadas antes da apresentação.

## Correspondência com o gabarito

| Requisito | Implementação |
|---|---|
| Textura e iluminação | Texturas procedurais de grama, terra e madeira no cenário; luz ambiente, difusa e especular, normais das faces |
| Movimentação de câmera | Órbita horizontal, inclinação vertical e distância limitadas |
| Cenário de fundo | Jardim aberto com árvores, cerca clara, flores 3D, canteiros, banco e pedras de entrada |
| Menus gráficos | Menu inicial, quantidade de jogadores, ajuda, recordes, pausa e final |
| Itens 3D | Cristais facetados, placa da pista, entrada de túnel e baú |
| Jogadores 3D e movimento | Mineiros compostos de sólidos; passos ortogonais pela matriz |
| Jogo para 2 a 4 e pontuação | Módulo `regras.py`, independente da renderização |
| Ranking, fim e reinício | Ranking a cada jogada, empates, reinício e retorno ao menu |
| Diferenciais implementados | Cristais animados, avatares com acessórios, invisibilidade, realce de destinos, quilates sobre os diamantes e recordes persistentes |

## Organização e explicação para apresentar

- `regras.py`: contém `Casa`, `Jogador` e `Jogo`. O campo `dono=None` representa casa oculta. `mover()` valida adjacência, resolve a saída de túnel, aplica o item e passa a vez somente em descobertas. `ranking()` ordena pela pontuação decrescente.
- `main.py`: abre a janela OpenGL e executa eventos → atualização → cena 3D → interface 2D → troca de buffers. O Pygame trata janela, mouse, teclado e fontes; o PyOpenGL desenha todos os sólidos, textura, iluminação e interface.
- `textura_rocha()`: gera grama, terra e veios de madeira com ruído e funções periódicas e envia à GPU com `glTexImage2D`. As faces usam coordenadas de textura.
- `caixa()`, `esfera()`, `cristal()` e `avatar()`: constroem os modelos. As normais orientam a iluminação. Push/pop de matrizes isolam transformações de cada objeto.
- `cena()`: usa perspectiva e `gluLookAt`; desenha somente itens revelados. `gluProject` converte os cantos de cada casa em polígonos na tela para seleção com mouse.
- `interface()`: troca para projeção ortográfica, desativa profundidade/iluminação e desenha menus, botões, textos e ranking.
- `recordes.json`: criado automaticamente após partidas completas, com as dez maiores pontuações individuais. Se a pasta não permitir gravação, uma mensagem informa o problema e a partida continua.
- `test_regras.py`: verifica distribuição, adjacência, revisitas, efeitos dos itens, empates, reinício e 90 partidas completas. Não precisa de bibliotecas gráficas.

## Verificação

```bash
python -m unittest -v
```

Foram verificadas partidas com 30 sementes para cada quantidade de jogadores, totalizando 90 partidas. O teste confere a igualdade de descobertas e a conservação da pontuação global, incluindo túneis pendentes e ataques do esconderijo. As telas e modelos também foram renderizados em OpenGL/Mesa fora de tela. Isso não substitui a execução no computador da apresentação.

## Roteiro de demonstração

1. Apresente o objetivo: vencer pela maior soma de quilates.
2. Mostre a seleção de 2 a 4 participantes e a tela de ajuda.
3. Comece uma partida e destaque entrada, bordas laranja e alternância de turnos.
4. Gire/incline/aproxime a câmera para mostrar textura, iluminação e modelos.
5. Revele casas e explique diamantes, pistas, túnel e esconderijo conforme aparecerem.
6. Mostre a navegação por casas exploradas sem coletar novamente.
7. Termine uma partida para demonstrar resultado, reinício e recordes.
8. Explique a separação entre regras e interface e as decisões descritas acima.

Para entregar: envie este ZIP completo ao Moodle e apresente ao professor, conforme o enunciado. Os comandos `py`/`python` devem usar o mesmo ambiente em que as dependências foram instaladas.
