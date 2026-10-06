# Trabalho Prático de Processamento Digital de Imagens

## Requisitos cobertos

- **Interface interativa:** GUI em Tkinter inspirada no modelo fornecido, com abas Imagem/Câmera, painel de operações, visualização Original/Resultado e barra de status; o CLI permanece disponível.
- **Aquisição:** carregamento de imagens e câmera/vídeo por arquivo ou webcam.
- **Conversões:** níveis de cinza, negativo e limiarização automática de Otsu.
- **Operações:** filtros autorais da média e mediana, Canny didático, erosão, dilatação, abertura e fechamento, disponíveis tanto para imagens quanto para quadros de vídeo.
- **Imagem:** histograma desenhado a partir da contagem autoral; rotulação BFS de componentes conexos; área, perímetro, diâmetro, centróide e caixa delimitadora.
- **Vídeo:** detecção automática de caneta com YOLO-World em cada quadro; acionamento de áudio quando uma caneta é reconhecida.

As funções de processamento de imagem foram escritas no próprio arquivo. As funções prontas do OpenCV ficam restritas à leitura/exibição, vídeo, seleção de ROI e rastreamento, conforme as observações do enunciado.

## Instalação

```bash
python -m pip install numpy opencv-python
```

Para a detecção automática de caneta, instale também:

```bash
pip install ultralytics
```

O primeiro uso do botão **Detectar caneta (YOLO)** baixa o modelo YOLO-World nano (`yolov8n-world.pt`).

Para tocar áudio no Linux, instale um reprodutor disponível no PATH, por exemplo `ffplay`, e selecione um arquivo `.wav` ou `.mp3` na GUI.

## Execução

Na pasta dos arquivos:

```bash
python main.py
```

`trabalho_pdi.py` também pode ser usado como compatibilidade e encaminha a execução para `main.py`.

Para usar apenas o menu de terminal:

```bash
python main.py --cli
```

Na aba **Imagem**, carregue um arquivo e use os botões de conversão, filtros, Canny, morfologia, histograma e análise dos objetos. Na aba **Câmera**, informe `0` para a webcam ou o caminho de um vídeo e clique em **Iniciar câmera**. Com a câmera ativa, **todos os botões da barra lateral passam a usar automaticamente o quadro mais recente**, e o resultado aparece no painel da aba Câmera. Assim, não é necessário carregar uma imagem para aplicar filtros, conversões, morfologia, histograma ou análise de objetos no vídeo.

As conversões **Níveis de cinza**, **Negativo** e **Otsu**, os filtros **Média**, **Mediana** e **Canny**, além de **Erosão**, **Dilatação**, **Abertura** e **Fechamento**, funcionam em modo contínuo na câmera. Clique em uma operação enquanto a câmera estiver rodando e o painel Resultado continuará sendo atualizado como um vídeo, quadro a quadro, com a operação aplicada. Use **Sem filtro** para interromper o processamento ao vivo. Os valores da janela e dos limiares do Canny são lidos a cada quadro, permitindo ajustá-los durante a execução.

O painel lateral possui rolagem vertical para acessar todos os controles. Em **Recursos extras**, estão disponíveis o filtro por cor (vermelho, verde e azul) e seu controle de intensidade. Na aba Câmera, **Tirar foto** salva o último quadro exibido (já com o processamento ativo, se houver) como `foto_001.png`, `foto_002.png` etc. Em **Detecção de caneta e música**, o YOLO-World procura canetas automaticamente no vídeo.

A contagem de objetos usa rotulação BFS própria em `objetos.py`. Para cada componente conexo foreground são calculados área em pixels, perímetro por borda exposta e diâmetro máximo (exato para componentes pequenos e aproximado pela caixa para componentes grandes). A implementação foi conferida com duas formas sintéticas: foram encontrados 2 objetos, com áreas 20 e 36 pixels.


Exemplo de execução dos testes:

```bash
python trabalho_pdi.py --self-test
```

## Observação sobre o áudio

O programa procura automaticamente por **caneta**, **caneta esferográfica**, **canetão** e **lápis** usando YOLO-World. Quando ao menos uma detecção supera o limiar de confiança e há um áudio selecionado, a música é tocada uma vez. Também é possível usar o botão **Selecionar para rastrear** para marcar manualmente qualquer objeto e acompanhá-lo com CSRT, KCF ou MIL; os dois modos podem ficar ativos simultaneamente.

## Arquivos

- `audios.py`: seleção e reprodução não bloqueante da música do objeto.
- `conversoes.py`: níveis de cinza, negativo e Otsu.
- `entradas.py`: carregamento de imagens e abertura de câmera/vídeo.
- `filtros.py`: média, mediana e Canny autorais.
- `histograma.py`: histograma manual e visualização.
- `interface.py`: única GUI Tkinter, com abas e controles simples.
- `morfologia.py`: erosão, dilatação, abertura e fechamento autorais.
- `objetos.py`: rotulação de componentes conexos e métricas.
- `video.py`: processamento de vídeo e rastreamento OpenCV.
- `main.py`: ponto de entrada e seleção GUI/CLI.
- `README.md`: instruções de instalação e uso.
