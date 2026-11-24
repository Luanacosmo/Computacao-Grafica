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
        pygame.display.set_caption('Procurando o Tesouro | Jardim dos Tesouros')
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
        self.rocha = self.textura_rocha('terra')
        self.grama = self.textura_rocha('grama')
        self.madeira = self.textura_rocha('madeira')
        self.recordes = self.ler_recordes()
        self.erro_salvar = ''
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_NORMALIZE)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glShadeModel(GL_SMOOTH)
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (.56,.58,.52,1))
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (.85,.82,.7,1))
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

    def textura_rocha(self, material='terra'):
        """Três texturas procedurais originais: grama, terra e madeira."""
        rng = random.Random(43)
        s = pygame.Surface((128,128))
        for x in range(128):
            for y in range(128):
                ruido = rng.randint(-12,12)
                if material == 'grama':
                    v = ruido + (12 if (x*7+y*3)%19 < 3 else 0)
                    cor = (157+v,183+v,116+v)
                elif material == 'madeira':
                    v = ruido//3 + int(13*math.sin(y*.5+math.sin(x*.09)))
                    cor = (204+v,167+v,114+v)
                else:
                    v = ruido//2
                    cor = (213+v,190+v,155+v)
                s.set_at((x,y),cor)
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
            glBindTexture(GL_TEXTURE_2D, self.grama if textura == 'grama' else self.madeira if textura == 'madeira' else self.rocha)
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

    def flor(self,x,z,indice):
        altura=.45+(indice%3)*.1
        dx=math.sin(self.tempo*1.5+x)*.035
        self.caixa(x,.15,z,.035,.6,.035,(.32,.53,.25))
        self.esfera(x+.10,.2,z,.09,(.43,.64,.31))
        cor=((.94,.64,.68),(.98,.84,.42),(.71,.62,.83))[indice%3]
        for k in range(5):
            a=k*math.tau/5
            self.esfera(x+dx+math.cos(a)*.12,altura,z+math.sin(a)*.12,.09,cor)
        self.esfera(x+dx,altura+.04,z,.075,(.98,.72,.25))

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
        # Jardim aberto: cerca, árvores, canteiros, flores e banco de madeira.
        self.caixa(0,-.36,0,28,.35,28,(1,1,1),'grama')
        self.caixa(0,-.18,0,7.4,.12,7.4,(1,.98,.92),True)
        for k in range(-8,9):
            x=k*.65
            self.caixa(x,.45,-5.5,.12,1.4,.14,(1,.99,.92))
            self.caixa(-5.5,.45,x,.14,1.4,.12,(1,.99,.92))
        for y in (.25,.8):
            self.caixa(0,y,-5.5,11.2,.12,.12,(1,.99,.92))
            self.caixa(-5.5,y,0,.12,.12,11.2,(1,.99,.92))
        for x,z in ((-4.6,-4.4),(4.3,-4.6),(-4.8,3.9)):
            self.caixa(x,.7,z,.32,1.8,.32,(.85,.76,.62),'madeira')
            for dx,dy,dz,r in ((0,2.1,0,.88),(-.5,1.75,0,.65),(.45,1.9,.15,.67)):
                self.esfera(x+dx,dy,z+dz,r,(.48+dx*.12,.67,.37))
        for x,z in ((-4.2,-2),(-4.2,0),(4.2,-2),(4.2,0),(0,-4.4),(2,-4.4)):
            self.caixa(x,-.03,z,.9,.23,1.2,(.85,.66,.51),True)
            for k in range(3):
                self.flor(x-.26+k*.25,z+(.24 if k%2 else -.18),k)
        # Banco lateral, sem bloquear a visão das casas.
        for z in (-1,0,1): self.caixa(5,.25,z,.16,.65,.16,(.82,.78,.68))
        for x in (4.8,5,5.2): self.caixa(x,.55,0,.15,.12,2.3,(1,.95,.86),'madeira')
        self.caixa(5.35,.95,0,.12,.45,2.3,(1,.95,.86),'madeira')
        # Pedras do caminho na entrada.
        for x,z in ((-3.7,-2.5),(3.7,2.5),(2.5,-3.7),(-2.5,3.7)):
            self.caixa(x,-.04,z,.6,.16,.55,(.84,.84,.75))
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
                cor=(1,1,1) if casa.dono is None else tuple(v*.42+.58 for v in CORES[casa.dono])
                self.caixa(x,0,z,.94,.24,.94,cor,'grama' if casa.dono is None else True)
                if (r,c) in destinos:
                    glDisable(GL_LIGHTING)
                    glColor3f(.95,.52,.23)
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
                    self.cristal(x,z,(.25,.76,.88),.55+casa.valor*.035)
                elif casa.tipo=='pista':
                    self.caixa(x,.45,z,.08,.65,.08,(.75,.6,.39))
                    self.caixa(x+.16,.72,z,.4,.22,.08,(.32,.65,.42))
                elif casa.tipo=='tunel':
                    self.caixa(x,.16,z,.65,.04,.65,(.045,.045,.065))
                    for dx in (-.3,.3): self.caixa(x+dx,.42,z,.12,.6,.18,(.78,.39,.32))
                    self.caixa(x,.72,z,.72,.14,.18,(.78,.39,.32))
                else:
                    self.caixa(x,.37,z,.57,.4,.4,(.95,.82,.63),'madeira')
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
        raio=min(14,w/2,h/2)
        glColor4f(*cor) if len(cor)==4 else glColor3f(*cor)
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(x+w/2,y+h/2)
        for cx,cy,inicio in ((x+raio,y+raio,180),(x+w-raio,y+raio,270),
                             (x+w-raio,y+h-raio,0),(x+raio,y+h-raio,90)):
            for k in range(9):
                a=math.radians(inicio+k*90/8)
                glVertex2f(cx+math.cos(a)*raio,cy+math.sin(a)*raio)
        glVertex2f(x,y+raio)
        glEnd()

    def circulo(self,x,y,r,cor):
        glColor3fv(cor)
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(x,y)
        for k in range(49):
            a=k*math.tau/48
            glVertex2f(x+r*math.cos(a),y+r*math.sin(a))
        glEnd()

    def flor_2d(self,x,y,tamanho,cor):
        for k in range(5):
            a=k*math.tau/5
            self.circulo(x+math.cos(a)*tamanho,y+math.sin(a)*tamanho,tamanho*.65,cor)
        self.circulo(x,y,tamanho*.55,(.94,.72,.3))

    def texto(self,t,x,y,n=18,cor=(49,69,55)):
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
        self.retangulo(rect,(.38,.55,.40) if ativo else ((.79,.85,.71) if hover else (.88,.91,.82)))
        x,y,w,h=rect
        self.texto(t,x+(w-self.fontes[18].size(t)[0])//2,y+(h-22)//2,18,(255,252,240) if ativo else (49,69,55))
        self.botoes.append((pygame.Rect(rect),acao))

    def iniciar(self):
        self.jogo=Jogo(self.quantidade)
        self.estado='jogo'
        self.erro_salvar=''

    def interface(self):
        self.inicio_2d()
        self.botoes=[]
        verde=(61,91,64)
        if self.estado in ('menu','ajuda','recordes'):
            self.retangulo((0,0,W,H),(.97,.96,.91))
            self.texto('PROCURANDO O TESOURO',64,35,16,verde)
            self.texto('Jardim dos Tesouros',60,78,56,verde)
            self.texto('Uma pequena aventura entre flores e diamantes.',64,154,22)
            if self.estado=='menu':
                self.retangulo((60,224,500,504),(1,.995,.97))
                self.texto('Vamos explorar?',90,250,28,verde)
                self.texto('Quantos jogadores vão participar?',90,304,18)
                for i in range(2,5):
                    self.botao(f'{i} jogadores',(90+(i-2)*146,347,132,54),('quantidade',i),self.quantidade==i)
                self.texto(f'{36//self.quantidade} descobertas para cada jogador',90,421,16)
                self.botao('Entrar no jardim',(90,466,440,58),'iniciar',True)
                self.botao('Como jogar',(90,540,212,48),'ajuda')
                self.botao('Recordes',(318,540,212,48),'recordes')
                self.botao('Sair',(90,605,440,44),'sair')
                self.texto('PYOPENGL  /  CENÁRIO 3D  /  MULTIJOGADOR LOCAL',90,685,14)
                # Ilustração vetorial original para a capa do jardim.
                self.retangulo((600,224,620,504),(.88,.92,.82))
                self.circulo(1130,305,42,(.99,.88,.61))
                for row in range(6):
                    for col in range(6):
                        self.retangulo((760+(col-row)*28,305+(col+row)*23,46,35),
                                       (.70,.79,.57) if (row+col)%2 else (.78,.84,.65))
                self.flor_2d(700,380,24,(.94,.71,.73))
                self.flor_2d(1080,490,30,(.74,.65,.84))
                self.flor_2d(690,565,19,(1,.88,.61))
                self.texto('36 casas. Um tesouro a descobrir.',650,623,22,verde)
                self.texto('Diamantes, pistas e surpresas pelo caminho.',650,665,16)
            elif self.estado=='ajuda':
                self.retangulo((60,218,1160,466),(1,.995,.97))
                textos=[
                    'Comece pela entrada ao lado de um canto. Clique em uma casa com borda laranja ou use as setas (direções da matriz). Ande somente para casas adjacentes, sem diagonais.',
                    'Casas exploradas são passagens gratuitas. Revelar uma casa oculta encerra o turno. Cada jogador terá 18, 12 ou 9 descobertas, de acordo com a quantidade de participantes.',
                    'Diamante: +1 a +10 quilates. Placa verde: +3. Túnel de terracota: -10 ao sair. Baú: avatar invisível até a próxima descoberta e -5 para cada rival.',
                    'Pontos podem ser negativos. Ao terminar, todos saem da mina sob o jardim e pagam túneis pendentes. A maior soma vence; empates têm vencedores conjuntos.',
                    'Câmera: arraste o botão direito para girar/inclinar e use a roda para aproximar/afastar. Há botões de câmera no painel. Esc abre a pausa.'
                ]
                y=245
                for i,t in enumerate(textos):
                    self.texto(f'0{i+1}',86,y,22,verde)
                    y=self.linhas(t,138,y,1035,18)+21
                self.botao('Voltar ao início',(60,711,260,48),'menu')
            else:
                self.retangulo((60,218,1160,468),(1,.995,.97))
                self.texto('As melhores colheitas de quilates',90,242,28,verde)
                if not self.recordes: self.texto('Complete uma partida para registrar sua pontuação.',90,330,22)
                for i,d in enumerate(self.recordes):
                    col=i//5; row=i%5; x=90+col*550; y=310+row*65
                    self.retangulo((x,y,510,52),(.92,.94,.87))
                    self.texto(f"{i+1:02d}    {d['nome']}    •    {d['pontos']} quilates",x+18,y+13,18)
                self.botao('Voltar ao início',(60,711,260,48),'menu')
            return
        # Etiquetas sobre a cena com contraste independente da cor do terreno.
        for t,x,y in self.rotulos:
            largura=self.fontes[16].size(t)[0]+12
            self.retangulo((x-6,y-2,largura,25),(1,.99,.93,.94))
            self.texto(t,x,y,16,(44,78,67))
        self.retangulo((20,18,380,64),(1,.99,.94,.96))
        self.texto('Jardim dos Tesouros',38,29,22,verde)
        self.texto('Clique nas bordas laranja para caminhar',38,57,14)
        self.retangulo((W-PAINEL,0,PAINEL,H),(.97,.96,.91))
        x=W-PAINEL+22
        j=self.jogo
        self.texto('SEU PASSEIO',x,22,14,verde)
        self.texto('Jardim dos Tesouros',x,49,22,verde)
        self.retangulo((x,94,296,9),(.85,.88,.79))
        if j.reveladas: self.retangulo((x,94,296*j.reveladas/36,9),(.42,.62,.44))
        self.texto(f'{j.reveladas} de 36 casas descobertas',x,115,16)
        self.retangulo((x,154,296,51),(.86,.91,.81))
        self.texto('Passeio concluído' if j.terminou else f'Vez: {j.jogadores[j.vez].nome}',x+14,167,22,verde)
        self.texto('RANKING / QUILATES',x,229,14,verde)
        for rank,(i,p) in enumerate(j.ranking()):
            y=260+rank*62
            self.retangulo((x,y,296,54),(1,.995,.97))
            self.retangulo((x+8,y+9,6,36),CORES[i])
            self.texto(f'{rank+1}. {p.nome}',x+24,y+5,18)
            self.texto(f'{p.pontos}q',x+238,y+5,18,verde)
            self.texto(f'{p.jogadas}/{36//len(j.jogadores)} descobertas'+(' • invisível' if p.invisivel else ''),x+24,y+31,14)
        self.retangulo((x,520,296,109),(.93,.90,.83))
        self.linhas(j.mensagem,x+12,531,274,14)
        self.texto('CÂMERA',x,642,14,verde)
        for k,(t,act) in enumerate([('Girar -','esq'),('Girar +','dir'),('+ Zoom','mais'),('- Zoom','menos')]):
            self.botao(t,(x+(k%2)*152,666+(k//2)*39,144,33),act)
        self.botao('Pausar / Menu',(x,751,296,34),'pausar',True)
        if self.estado in ('pausa','fim'):
            self.retangulo((0,0,W-PAINEL,H),(.22,.32,.24,.58))
            self.retangulo((95,160,750,490),(.99,.98,.94))
            if self.estado=='fim':
                self.texto('Um jardim de descobertas!',132,198,38,verde)
                self.linhas('Vencedor(es): '+', '.join(j.vencedores()),132,279,655,28)
                self.texto(f'Maior soma: {j.ranking()[0][1].pontos} quilates',132,365,22)
                if self.erro_salvar: self.texto(self.erro_salvar,132,407,16)
            else:
                self.texto('Uma pausa no jardim',132,205,38,verde)
                self.texto('Sua partida continua aqui.',132,274,22)
                self.botao('Continuar passeio',(132,340,660,50),'continuar',True)
            self.botao('Nova partida',(132,480,660,50),'iniciar')
            self.botao('Menu principal',(132,548,660,50),'menu')

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
            glClearColor(.77,.87,.82,1)
            glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
            if self.jogo is not None and self.estado in ('jogo','pausa','fim'): self.cena()
            self.interface()
            pygame.display.flip()
            self.tempo+=self.clock.tick(60)/1000
        gluDeleteQuadric(self.quadrica)
        glDeleteTextures([self.rocha,self.grama,self.madeira])
        pygame.quit()

if __name__=='__main__':
    Aplicacao().executar()
