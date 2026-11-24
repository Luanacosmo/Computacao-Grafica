"""Regras independentes da interface OpenGL (coordenadas: linha, coluna)."""
from dataclasses import dataclass
import random

CORES = [(.25, .56, .72), (.86, .43, .40), (.61, .45, .73), (.35, .62, .36)]

@dataclass
class Casa:
    tipo: str
    valor: int = 0
    dono: int | None = None

@dataclass
class Jogador:
    nome: str
    pos: tuple
    pontos: int = 0
    jogadas: int = 0
    invisivel: bool = False
    penalidade: bool = False

class Jogo:
    def __init__(self, quantidade=2, seed=None):
        if quantidade not in (2, 3, 4):
            raise ValueError('Escolha de 2 a 4 jogadores.')
        self.n = 6
        rng = random.Random(seed)
        # Arredondamento ao inteiro mais próximo: 5% de 36 = 2; 10% = 4.
        tipos = ['pista'] * 2 + ['tunel'] * 2 + ['esconderijo'] * 2 + ['diamante'] * 30
        rng.shuffle(tipos)
        self.mina = [[Casa(tipos[r*6+c], rng.randint(1, 10) if tipos[r*6+c] == 'diamante' else 0)
                      for c in range(6)] for r in range(6)]
        entradas = [(0, -1), (5, 6), (-1, 5), (6, 0)]
        self.jogadores = [Jogador(f'Mineiro {i+1}', entradas[i]) for i in range(quantidade)]
        self.vez = 0
        self.reveladas = 0
        self.mensagem = 'Entre na mina pela casa indicada. Explore uma casa por turno.'

    @property
    def terminou(self):
        return self.reveladas == 36

    def adjacentes(self, pos):
        r, c = pos
        return [(a,b) for a,b in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)) if 0 <= a < 6 and 0 <= b < 6]

    def destinos(self):
        return self.adjacentes(self.jogadores[self.vez].pos) if not self.terminou else []

    def mover(self, r, c):
        if self.terminou or (r,c) not in self.destinos():
            return False
        j = self.jogadores[self.vez]
        eventos = []
        if j.penalidade:
            j.pontos -= 10
            j.penalidade = False
            eventos.append('Saiu do túnel: -10 quilates.')
        j.pos = (r,c)
        casa = self.mina[r][c]
        if casa.dono is not None:
            self.mensagem = ' '.join(eventos + ['Passagem por casa explorada: continue seu turno.'])
            return True
        j.invisivel = False
        casa.dono = self.vez
        j.jogadas += 1
        self.reveladas += 1
        if casa.tipo == 'diamante':
            j.pontos += casa.valor
            eventos.append(f'Diamante de {casa.valor} quilates!')
        elif casa.tipo == 'pista':
            j.pontos += 3
            eventos.append('Prossiga: caminho certo! +3 quilates.')
        elif casa.tipo == 'tunel':
            j.penalidade = True
            eventos.append('Túnel sem saída: perderá 10 quilates ao sair.')
        elif casa.tipo == 'esconderijo':
            j.invisivel = True
            for outro in self.jogadores:
                if outro is not j:
                    outro.pontos -= 5
            eventos.append('Esconderijo: invisível até explorar outra casa; rivais -5.')
        self.mensagem = j.nome + ': ' + ' '.join(eventos)
        if not self.terminou:
            self.vez = (self.vez + 1) % len(self.jogadores)
        else:
            # Saída automática da mina encerra também os túneis pendentes.
            for outro in self.jogadores:
                if outro.penalidade:
                    outro.pontos -= 10
                    outro.penalidade = False
            self.mensagem += ' Fim: todos saem da mina (túneis pendentes cobrados).'
        return True

    def ranking(self):
        return sorted(enumerate(self.jogadores), key=lambda par: -par[1].pontos)

    def vencedores(self):
        melhor = self.ranking()[0][1].pontos
        return [j.nome for j in self.jogadores if j.pontos == melhor]
