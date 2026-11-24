"""Execute: python -m unittest -v"""
import unittest
from collections import Counter, deque
from regras import Jogo, Casa


def caminho_ate_oculta(j):
    inicio = j.jogadores[j.vez].pos
    fila = deque([(inicio, [])]); vistos={inicio}
    while fila:
        pos, passos = fila.popleft()
        for p in j.adjacentes(pos):
            if p in vistos: continue
            novo=passos+[p]
            if j.mina[p[0]][p[1]].dono is None: return novo
            vistos.add(p); fila.append((p,novo))
    raise AssertionError('Jogador sem acesso a casas ocultas')


class TestRegras(unittest.TestCase):
    def test_distribuicao(self):
        j=Jogo(seed=1)
        casas=[c for linha in j.mina for c in linha]
        self.assertEqual(Counter(c.tipo for c in casas),dict(diamante=30,pista=2,tunel=2,esconderijo=2))
        self.assertTrue(all(1<=c.valor<=10 for c in casas if c.tipo=='diamante'))
        self.assertTrue(all(c.dono is None for c in casas))

    def test_movimento_e_revisita(self):
        j=Jogo(seed=3)
        self.assertFalse(j.mover(1,1))
        j.mina[0][0]=Casa('diamante',7)
        self.assertTrue(j.mover(0,0))
        self.assertEqual(j.jogadores[0].pontos,7)
        self.assertEqual(j.vez,1)
        # Posicionamento controlado para verificar passagem sem nova coleta.
        j.jogadores[1].pos=(0,1)
        j.mover(0,0)
        self.assertEqual(j.vez,1)
        self.assertEqual(j.jogadores[1].pontos,0)
        self.assertEqual(j.reveladas,1)
        self.assertFalse(j.mover(1,1)) # diagonal

    def test_itens(self):
        j=Jogo(3)
        j.mina[0][0]=Casa('pista'); j.mover(0,0)
        self.assertEqual(j.jogadores[0].pontos,3)
        j.jogadores[1].pos=(1,0); j.mina[1][1]=Casa('esconderijo'); j.mover(1,1)
        self.assertEqual([p.pontos for p in j.jogadores],[-2,0,-5])
        self.assertTrue(j.jogadores[1].invisivel)
        j.jogadores[2].pos=(2,0); j.mina[2][1]=Casa('tunel'); j.mover(2,1)
        self.assertTrue(j.jogadores[2].penalidade)
        j.vez=2; j.mina[2][2]=Casa('diamante',4); j.mover(2,2)
        self.assertEqual(j.jogadores[2].pontos,-11)
        self.assertFalse(j.jogadores[2].penalidade)
        j.vez=1; j.mina[1][2]=Casa('diamante',2); j.mover(1,2)
        self.assertFalse(j.jogadores[1].invisivel)

    def test_partidas_completas(self):
        for n in (2,3,4):
            for seed in range(30):
                with self.subTest(n=n,seed=seed):
                    j=Jogo(n,seed)
                    while not j.terminou:
                        for p in caminho_ate_oculta(j): j.mover(*p)
                    self.assertEqual([p.jogadas for p in j.jogadores],[36//n]*n)
                    # Conservação global: diamantes + pistas - túneis - ataques aos rivais.
                    soma=sum(c.valor for linha in j.mina for c in linha)
                    self.assertEqual(sum(p.pontos for p in j.jogadores),soma+6-20-10*(n-1))
                    antes=[p.pontos for p in j.jogadores]
                    self.assertFalse(j.mover(0,0))
                    self.assertEqual(antes,[p.pontos for p in j.jogadores])
                    self.assertTrue(j.vencedores())
                    self.assertFalse(any(p.penalidade for p in j.jogadores))

    def test_empate_e_reinicio(self):
        j=Jogo(4)
        self.assertEqual(len(j.vencedores()),4)
        j.mover(0,0)
        novo=Jogo(4)
        self.assertEqual(novo.reveladas,0)
        self.assertEqual([p.pontos for p in novo.jogadores],[0]*4)

if __name__=='__main__': unittest.main()
