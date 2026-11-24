# Procurando o Tesouro — Jardim dos Tesouros

Trabalho de Computação Gráfica em Python, PyOpenGL e Pygame.

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
7. Termine uma partida para demonstrar resultado, reinício e recordes.
8. Explique a separação entre regras e interface e as decisões descritas acima.

Para entregar: envie este ZIP completo ao Moodle e apresente ao professor, conforme o enunciado. Os comandos `py`/`python` devem usar o mesmo ambiente em que as dependências foram instaladas.
