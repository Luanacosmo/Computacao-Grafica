"""Procurando o Tesouro - PyOpenGL + Pygame. Execute: python main.py."""
import math
import random
import json
from pathlib import Path
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
from regras import Jogo, CORES

W, H = 1280, 800
PAINEL = 340

class Aplicacao:
    def __init__(self):
        pygame.init()
        pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
        pygame.display.set_mode((W,H), pygame.OPENGL | pygame.DOUBLEBUF)
        pygame.display.set_caption('Procurando o Tesouro | Mina dos Cristais')
        self.clock = pygame.time.Clock()
        self.fontes = {n: pygame.font.SysFont('dejavusans', n) for n in (14,16,18,22,28,38,56)}
        self.estado = 'menu'
        self.quantidade = 2
        self.jogo = None
        self.angulo, self.elevacao, self.distancia = 35, 52, 12
        self.botoes = []
        self.projecoes = {}
        self.rodando = True
        self.tempo = 0
        self.quadrica = gluNewQuadric()
        self.rocha = self.textura_rocha()
        self.recordes = self.ler_recordes()
        self.erro_salvar = ''
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_NORMALIZE)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glShadeModel(GL_SMOOTH)
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (.36,.38,.44,1))
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (.95,.86,.69,1))
        glLightfv(GL_LIGHT0, GL_SPECULAR, (.8,.8,.9,1))
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, (.35,.35,.4,1))
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 35)

    def ler_recordes(self):
        self.arquivo_recordes = Path(__file__).resolve().with_name('recordes.json')
        try:
            dados = json.loads(self.arquivo_recordes.read_text(encoding='utf-8'))
            return [d for d in dados if isinstance(d,dict) and isinstance(d.get('nome'),str)
                    and isinstance(d.get('pontos'),int)][:10] if isinstance(dados,list) else []
        except (OSError, ValueError):
            return []

    def salvar_recordes(self):
        self.recordes += [{'nome':j.nome, 'pontos':j.pontos} for j in self.jogo.jogadores]
        self.recordes = sorted(self.recordes,key=lambda d:-d['pontos'])[:10]
        try:
            self.arquivo_recordes.write_text(json.dumps(self.recordes,ensure_ascii=False,indent=2),encoding='utf-8')
        except OSError:
            self.erro_salvar = 'Não foi possível salvar os recordes nesta pasta.'

    def textura_rocha(self):
        """Textura original procedural; não depende de imagens externas."""
        rng = random.Random(43)
        s = pygame.Surface((128,128))
        for x in range(128):
            for y in range(128):
                v = rng.randint(70,120) + int(9*math.sin(x*.3+y*.15))
                s.set_at((x,y),(v,int(v*.86),int(v*.73)))
        tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D,tex)
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D,0,GL_RGB,128,128,0,GL_RGB,GL_UNSIGNED_BYTE,pygame.image.tostring(s,'RGB',True))
        return tex

    def caixa(self,x,y,z,sx,sy,sz,cor,textura=False):
        glPushMatrix()
        glTranslatef(x,y,z)
        glScalef(sx,sy,sz)
        glColor3fv(cor)
        if textura:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D,self.rocha)
        faces = [((0,1,0),[(-1,1,-1),(-1,1,1),(1,1,1),(1,1,-1)]),
                 ((0,-1,0),[(-1,-1,1),(-1,-1,-1),(1,-1,-1),(1,-1,1)]),
                 ((0,0,1),[(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]),
                 ((0,0,-1),[(1,-1,-1),(-1,-1,-1),(-1,1,-1),(1,1,-1)]),
                 ((1,0,0),[(1,-1,1),(1,-1,-1),(1,1,-1),(1,1,1)]),
                 ((-1,0,0),[(-1,-1,-1),(-1,-1,1),(-1,1,1),(-1,1,-1)])]
        glBegin(GL_QUADS)
        for normal,vertices in faces:
            glNormal3fv(normal)
            for uv,v in zip(((0,0),(1,0),(1,1),(0,1)),vertices):
                glTexCoord2fv(uv)
                glVertex3f(v[0]/2,v[1]/2,v[2]/2)
        glEnd()
        glDisable(GL_TEXTURE_2D)
        glPopMatrix()

    def esfera(self,x,y,z,raio,cor):
        glColor3fv(cor)
        glPushMatrix()
        glTranslatef(x,y,z)
        gluSphere(self.quadrica,raio,16,12)
        glPopMatrix()

    def cristal(self,x,z,cor,escala=1):
        glPushMatrix()
        glTranslatef(x,.28,z)
        glRotatef(self.tempo*25,0,1,0)
        glScalef(escala,escala,escala)
        glColor3fv(cor)
        vertices = [(0,.75,0),(.27,.25,0),(0,.25,.27),(-.27,.25,0),(0,.25,-.27),(0,0,0)]
        glBegin(GL_TRIANGLES)
        for i in range(4):
            for inds in ((0,1+(i+1)%4,1+i),(5,1+i,1+(i+1)%4)):
                a,b,c = [vertices[t] for t in inds]
                u=[b[k]-a[k] for k in range(3)]; v=[c[k]-a[k] for k in range(3)]
                normal=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
                glNormal3fv(normal)
                for p in (a,b,c): glVertex3fv(p)
        glEnd()
        glPopMatrix()

    def avatar(self,x,z,i):
        cor=CORES[i]
        # Quatro silhuetas: acessórios distintos além das cores e números.
        self.caixa(x,.59,z,.28,.42,.24,cor)
        for dx in (-.09,.09): self.caixa(x+dx,.29,z,.09,.25,.12,(.15,.19,.25))
        self.esfera(x,.94,z,.17,(.87,.68,.47))
        self.caixa(x,1.07,z,.4,.1,.35,cor)
        self.esfera(x,1.08,z+.19,.06,(1,.95,.62))
        for dx in (-.22,.22): self.caixa(x+dx,.65,z,.1,.32,.12,cor)
        if i == 1: self.caixa(x,.7,z-.2,.3,.35,.18,(.52,.3,.12))
        if i == 2: self.caixa(x+.3,.8,z,.08,.65,.08,(.7,.7,.75))
        if i == 3: self.esfera(x-.28,.51,z,.12,(1,.72,.2))

    def cena(self):
        glViewport(0,0,W-PAINEL,H)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(46,(W-PAINEL)/H,.1,90)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        a,e=math.radians(self.angulo),math.radians(self.elevacao)
        d=self.distancia
        gluLookAt(d*math.cos(e)*math.sin(a),d*math.sin(e),d*math.cos(e)*math.cos(a),0,0,0,0,1,0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glLightfv(GL_LIGHT0,GL_POSITION,(4,8,4,1))
        self.caixa(0,-.5,0,17,.6,17,(.53,.5,.5),True)
        # Paredes, suportes de madeira, cristais e luminárias compõem a caverna.
        self.caixa(0,1,-6,17,3,1,(.5,.54,.6),True)
        self.caixa(-7,1,0,1,3,12,(.5,.54,.6),True)
        for x in (-5,-2,2,5):
            self.caixa(x,1.1,-5.3,.25,3,.25,(.33,.18,.09),True)
            self.esfera(x,2.25,-5.1,.14,(1,.74,.24))
        self.caixa(0,2.7,-5.3,11,.28,.28,(.37,.21,.1),True)
        for x,z in ((-5,-3),(4,-4),(5,3),(-4,4)):
            self.cristal(x,z,(.23,.56,.75),1.5)
            self.cristal(x+.4,z+.2,(.5,.35,.8),.8)
        j=self.jogo
        self.projecoes={}
        model=glGetDoublev(GL_MODELVIEW_MATRIX)
        proj=glGetDoublev(GL_PROJECTION_MATRIX)
        view=glGetIntegerv(GL_VIEWPORT)
        destinos=j.destinos()
        for r in range(6):
            for c in range(6):
                x,z=c-2.5,r-2.5
                casa=j.mina[r][c]
                cor=(.47,.43,.37) if casa.dono is None else tuple(v*.65+.15 for v in CORES[casa.dono])
                self.caixa(x,0,z,.94,.24,.94,cor,True)
                if (r,c) in destinos:
                    glDisable(GL_LIGHTING)
                    glColor3f(.95,.8,.35)
                    glLineWidth(3)
                    glBegin(GL_LINE_LOOP)
                    for dx,dz in ((-.47,-.47),(.47,-.47),(.47,.47),(-.47,.47)): glVertex3f(x+dx,.14,z+dz)
                    glEnd()
                    glEnable(GL_LIGHTING)
                # Projeta os quatro cantos para seleção por clique no tabuleiro.
                self.projecoes[(r,c)]=[(p[0],H-p[1]) for p in
                    [gluProject(x+dx,.125,z+dz,model,proj,view) for dx,dz in ((-.48,-.48),(.48,-.48),(.48,.48),(-.48,.48))]]
                if casa.dono is None: continue  # Nunca desenhar conteúdo oculto.
                self.caixa(x-.33,.19,z-.33,.16,.12,.16,CORES[casa.dono])
                if casa.tipo=='diamante':
                    self.cristal(x,z,(.3,.9,1),.55+casa.valor*.035)
                elif casa.tipo=='pista':
                    self.caixa(x,.45,z,.08,.65,.08,(.64,.42,.2))
                    self.caixa(x+.16,.72,z,.4,.22,.08,(.28,.94,.46))
                elif casa.tipo=='tunel':
                    self.caixa(x,.16,z,.65,.04,.65,(.045,.045,.065))
                    for dx in (-.3,.3): self.caixa(x+dx,.42,z,.12,.6,.18,(.62,.23,.18))
                    self.caixa(x,.72,z,.72,.14,.18,(.62,.23,.18))
                else:
                    self.caixa(x,.37,z,.57,.4,.4,(.52,.25,.08),True)
                    self.caixa(x,.59,z,.62,.09,.46,(1,.68,.16))
                    self.caixa(x,.43,z+.21,.1,.15,.04,(1,.85,.3))
        for i,p in enumerate(j.jogadores):
            r,c=p.pos
            if not p.invisivel: self.avatar(c-2.5+(i%2)*.13,r-2.5+(i//2)*.13,i)
        # Números e quilates flutuantes são desenhados no HUD após a cena.
        self.rotulos=[]
        for r in range(6):
            for c in range(6):
                casa=j.mina[r][c]
                if casa.dono is not None and casa.tipo=='diamante':
                    p=gluProject(c-2.5,1.05,r-2.5,model,proj,view)
                    self.rotulos.append((f'{casa.valor}q',int(p[0]),int(H-p[1])))
        for i,p in enumerate(j.jogadores):
            if not p.invisivel:
                r,c=p.pos; pt=gluProject(c-2.5,1.4,r-2.5,model,proj,view)
                self.rotulos.append((str(i+1),int(pt[0]),int(H-pt[1])))

    def inicio_2d(self):
        glViewport(0,0,W,H)
        glMatrixMode(GL_PROJECTION); glLoadIdentity(); glOrtho(0,W,H,0,-1,1)
        glMatrixMode(GL_MODELVIEW); glLoadIdentity()
        glDisable(GL_LIGHTING); glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)

    def retangulo(self,rect,cor):
        x,y,w,h=rect
        glColor4f(*cor) if len(cor)==4 else glColor3f(*cor)
        glBegin(GL_QUADS)
        for p in ((x,y),(x+w,y),(x+w,y+h),(x,y+h)): glVertex2f(*p)
        glEnd()

    def texto(self,t,x,y,n=18,cor=(225,232,239)):
        s=self.fontes[n].render(str(t),True,cor)
        # glDrawPixels é parte do perfil de compatibilidade usado pelo PyOpenGL.
        glWindowPos2d(x,H-y-s.get_height())
        glDrawPixels(s.get_width(),s.get_height(),GL_RGBA,GL_UNSIGNED_BYTE,pygame.image.tostring(s,'RGBA',True))

    def linhas(self,t,x,y,largura=300,n=16):
        linha=''
        for palavra in t.split():
            nova=(linha+' '+palavra).strip()
            if self.fontes[n].size(nova)[0]>largura and linha:
                self.texto(linha,x,y,n); y+=25; linha=palavra
            else: linha=nova
        if linha: self.texto(linha,x,y,n); y+=25
        return y

    def botao(self,t,rect,acao,ativo=False):
        mouse=pygame.mouse.get_pos()
        hover=pygame.Rect(rect).collidepoint(mouse)
        self.retangulo(rect,(.2,.42,.48) if ativo else ((.18,.28,.36) if hover else (.11,.18,.25)))
        x,y,w,h=rect
        self.texto(t,x+(w-self.fontes[18].size(t)[0])//2,y+(h-22)//2)
        self.botoes.append((pygame.Rect(rect),acao))

    def iniciar(self):
        self.jogo=Jogo(self.quantidade)
        self.estado='jogo'
        self.erro_salvar=''

    def interface(self):
        self.inicio_2d()
        self.botoes=[]
        if self.estado in ('menu','ajuda','recordes'):
            self.retangulo((0,0,W,H),(.035,.055,.085))
            self.texto('MINA DOS CRISTAIS',100,70,56,(99,222,232))
            self.texto('Procurando o Tesouro • Computação Gráfica',104,145,22)
            if self.estado=='menu':
                self.texto('Explore. Encontre diamantes. Conquiste mais quilates.',104,225,22)
                self.texto('Quantidade de jogadores',104,295,18)
                for i in range(2,5): self.botao(str(i),(104+(i-2)*110,335,90,55),('quantidade',i),self.quantidade==i)
                self.botao('Iniciar expedição',(104,430,330,58),'iniciar')
                self.botao('Como jogar',(104,505,330,48),'ajuda')
                self.botao('Melhores pontuações',(104,568,330,48),'recordes')
                self.botao('Sair',(104,631,330,48),'sair')
                self.texto('36 casas',650,300,56,(243,198,94))
                self.texto('30 diamantes • 4 armadilhas • 2 pistas',650,385,22)
                self.texto('2 a 4 exploradores • Uma descoberta por turno',650,430,18)
            elif self.estado=='ajuda':
                textos=[
                    'Cada jogador começa em uma entrada junto a um canto. Clique em uma casa com borda dourada ou use as setas (direções da matriz). Só é permitido andar para casas adjacentes, sem diagonais.',
                    'Casas exploradas são passagens gratuitas: ande por elas até alcançar uma casa oculta. Revelar uma casa encerra o turno. Cada jogador explora 18, 12 ou 9 casas.',
                    'Diamante: soma de 1 a 10 quilates. Pista verde: +3. Túnel vermelho: -10 ao sair. Esconderijo: invisibilidade até a próxima descoberta e -5 para cada rival.',
                    'Pontuações podem ser negativas. Ao terminar, todos saem da mina e pagam túneis pendentes. Maior soma vence; empate produz vencedores conjuntos.',
                    'Câmera: arraste com o botão direito para girar/inclinar; use a roda para aproximar/afastar. Botões no painel também controlam a câmera. Esc abre a pausa.'
                ]
                y=220
                for t in textos: y=self.linhas(t,104,y,1050,18)+18
                self.botao('Voltar',(104,705,220,46),'menu')
            else:
                self.texto('Melhores pontuações de todas as partidas',104,220,28)
                if not self.recordes: self.texto('Nenhuma partida concluída ainda.',104,290,22)
                for i,d in enumerate(self.recordes): self.texto(f"{i+1:02d}   {d['nome']}   •   {d['pontos']} quilates",104,280+i*36,22)
                self.botao('Voltar',(800,690,220,46),'menu')
            return
        for t,x,y in self.rotulos: self.texto(t,x-8,y,16,(255,239,184))
        self.retangulo((W-PAINEL,0,PAINEL,H),(.045,.065,.095))
        x=W-PAINEL+22
        self.texto('EXPEDIÇÃO',x,24,28,(103,224,229))
        j=self.jogo
        self.texto(f'Casas reveladas: {j.reveladas}/36',x,74,18)
        self.texto('Fim da partida' if j.terminou else f'Vez: {j.jogadores[j.vez].nome}',x,108,22,(247,204,99))
        self.texto('RANKING • QUILATES',x,165,18)
        for rank,(i,p) in enumerate(j.ranking()):
            y=205+rank*67
            self.retangulo((x,y,6,45),CORES[i])
            self.texto(f'{rank+1}. {p.nome}     {p.pontos}q',x+16,y,18)
            self.texto(f'{p.jogadas}/{36//len(j.jogadores)} explorações'+(' • invisível' if p.invisivel else ''),x+16,y+28,14)
        self.linhas(j.mensagem,x,490,295,16)
        self.texto('CÂMERA',x,630,14)
        for k,(t,act) in enumerate([('Girar -','esq'),('Girar +','dir'),('+ Zoom','mais'),('- Zoom','menos')]):
            self.botao(t,(x+(k%2)*150,655+(k//2)*44,140,36),act)
        self.botao('Pausar / Menu',(x,750,290,34),'pausar')
        if self.estado in ('pausa','fim'):
            self.retangulo((0,0,W-PAINEL,H),(.015,.025,.04,.91))
            if self.estado=='fim':
                self.texto('EXPEDIÇÃO CONCLUÍDA',90,200,38,(103,224,229))
                self.linhas('Vencedor(es): '+', '.join(j.vencedores()),90,280,710,28)
                self.texto(f'Maior soma: {j.ranking()[0][1].pontos} quilates',90,360,22)
                if self.erro_salvar: self.texto(self.erro_salvar,90,410,16)
            else:
                self.texto('JOGO PAUSADO',90,220,38)
                self.botao('Continuar',(90,320,320,50),'continuar')
            self.botao('Nova partida',(90,470,320,50),'iniciar')
            self.botao('Menu principal',(90,540,320,50),'menu')

    def agir(self,acao):
        if isinstance(acao,tuple): self.quantidade=acao[1]
        elif acao=='iniciar': self.iniciar()
        elif acao=='sair': self.rodando=False
        elif acao in ('menu','ajuda','recordes'): self.estado=acao
        elif acao=='pausar' and self.estado=='jogo': self.estado='pausa'
        elif acao=='continuar': self.estado='jogo'
        elif acao=='esq': self.angulo-=15
        elif acao=='dir': self.angulo+=15
        elif acao=='mais': self.distancia=max(7,self.distancia-1)
        elif acao=='menos': self.distancia=min(23,self.distancia+1)

    @staticmethod
    def dentro(p,poligono):
        sinais=[]
        for a,b in zip(poligono,poligono[1:]+poligono[:1]):
            sinais.append((b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0]))
        return all(v>=0 for v in sinais) or all(v<=0 for v in sinais)

    def mover(self,r,c):
        self.jogo.mover(r,c)
        if self.jogo.terminou:
            self.salvar_recordes()
            self.estado='fim'

    def executar(self):
        while self.rodando:
            for ev in pygame.event.get():
                if ev.type==pygame.QUIT: self.rodando=False
                elif ev.type==pygame.KEYDOWN:
                    if ev.key==pygame.K_ESCAPE:
                        if self.estado=='jogo': self.estado='pausa'
                        elif self.estado=='pausa': self.estado='jogo'
                        else: self.estado='menu'
                    elif self.estado=='jogo' and ev.key in (pygame.K_UP,pygame.K_DOWN,pygame.K_LEFT,pygame.K_RIGHT):
                        dr,dc={pygame.K_UP:(-1,0),pygame.K_DOWN:(1,0),pygame.K_LEFT:(0,-1),pygame.K_RIGHT:(0,1)}[ev.key]
                        r,c=self.jogo.jogadores[self.jogo.vez].pos
                        self.mover(r+dr,c+dc)
                elif ev.type==pygame.MOUSEMOTION and ev.buttons[2] and self.estado=='jogo':
                    self.angulo+=ev.rel[0]*.4
                    self.elevacao=max(25,min(80,self.elevacao+ev.rel[1]*.3))
                elif ev.type==pygame.MOUSEWHEEL and self.estado=='jogo':
                    self.distancia=max(7,min(23,self.distancia-ev.y*.7))
                elif ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
                    acao=next((a for rect,a in reversed(self.botoes) if rect.collidepoint(ev.pos)),None)
                    if acao is not None: self.agir(acao)
                    elif self.estado=='jogo' and ev.pos[0]<W-PAINEL:
                        for pos,poly in self.projecoes.items():
                            if self.dentro(ev.pos,poly): self.mover(*pos); break
            glClearColor(.035,.055,.085,1)
            glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
            if self.jogo is not None and self.estado in ('jogo','pausa','fim'): self.cena()
            self.interface()
            pygame.display.flip()
            self.tempo+=self.clock.tick(60)/1000
        gluDeleteQuadric(self.quadrica)
        glDeleteTextures([self.rocha])
        pygame.quit()

if __name__=='__main__':
    Aplicacao().executar()
