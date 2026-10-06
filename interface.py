"""Interface gráfica do trabalho prático, inspirada no modelo fornecido."""
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Optional

import cv2
import numpy as np
from PIL import Image, ImageTk

from audios import play_music, stop_music
from caneta import PenDetector
from conversoes import negative, otsu, to_gray
from entradas import load_image
from filtros import canny, mean_filter, median_filter
from histograma import draw_histogram
from morfologia import closing, dilate, erode, opening
from objetos import connected_components
from video import choose_tracker


class PDIApp(tk.Tk):
    """Janela principal: imagem à esquerda e câmera à direita, como no modelo."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Processamento de Imagens e Vídeo")
        self.geometry("1180x760")
        self.minsize(980, 650)
        self.configure(bg="#f2f2f2")

        self.image: Optional[np.ndarray] = None
        self.gray: Optional[np.ndarray] = None
        self.current_frame: Optional[np.ndarray] = None
        self.cap: Optional[cv2.VideoCapture] = None
        self.camera_running = False
        self.live_filter = None
        self.live_filter_name = "Sem filtro"
        self.pen_detector: Optional[PenDetector] = None
        self.pen_detection_active = False
        self.tracker = None
        self.tracker_name = ""
        self.tracking = False
        self.audio_played = False
        self.audio_path = tk.StringVar()
        self.kernel_size = tk.IntVar(value=3)
        self.low_threshold = tk.IntVar(value=50)
        self.high_threshold = tk.IntVar(value=150)
        self.connectivity = tk.IntVar(value=8)
        self.camera_source = tk.StringVar(value="0")
        self.color_name = tk.StringVar(value="Vermelho")
        self.color_intensity = tk.DoubleVar(value=1.0)
        self.photo_counter = 0
        self.status = tk.StringVar(value="Carregue uma imagem ou inicie a câmera.")
        self.original_photo = None
        self.result_photo = None
        self.camera_photo = None
        self.video_result_photo = None
        self.last_video_result: Optional[np.ndarray] = None

        self._build_style()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self.close)

    def _build_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Title.TLabel", font=("Arial", 15, "bold"))
        style.configure("Section.TLabelframe.Label", font=("Arial", 10, "bold"))
        style.configure("Action.TButton", padding=(7, 4))

    def _build_ui(self) -> None:
        ttk.Label(self, text="Processamento de imagens e vídeo", style="Title.TLabel").pack(pady=(10, 5))
        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, padx=10, pady=5)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        sidebar = ttk.Frame(body, width=255)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        sidebar.grid_propagate(False)
        sidebar.rowconfigure(0, weight=1); sidebar.columnconfigure(0, weight=1)
        controls_canvas = tk.Canvas(sidebar, highlightthickness=0, width=235)
        controls_scroll = ttk.Scrollbar(sidebar, orient="vertical", command=controls_canvas.yview)
        controls = ttk.Frame(controls_canvas, width=235)
        controls.bind("<Configure>", lambda e: controls_canvas.configure(scrollregion=controls_canvas.bbox("all")))
        controls_canvas.create_window((0, 0), window=controls, anchor="nw", width=235)
        controls_canvas.configure(yscrollcommand=controls_scroll.set)
        controls_canvas.grid(row=0, column=0, sticky="nsew"); controls_scroll.grid(row=0, column=1, sticky="ns")
        controls_canvas.bind_all("<MouseWheel>", lambda e: controls_canvas.yview_scroll(int(-e.delta / 120), "units"))
        self._build_controls(controls)

        center = ttk.Frame(body)
        center.grid(row=0, column=1, sticky="nsew")
        center.columnconfigure(0, weight=1)
        center.rowconfigure(1, weight=1)
        center.rowconfigure(3, weight=1)
        self._build_view(center)

        ttk.Label(self, textvariable=self.status, relief="sunken", anchor="w").pack(fill="x", side="bottom", padx=10, pady=(0, 8))

    def _build_controls(self, parent: ttk.Frame) -> None:
        file_box = ttk.LabelFrame(parent, text="Aquisição de imagens", style="Section.TLabelframe")
        file_box.pack(fill="x", pady=(0, 8))
        ttk.Button(file_box, text="Carregar imagem...", command=self.load_image, style="Action.TButton").pack(fill="x", padx=7, pady=5)
        ttk.Button(file_box, text="Limpar resultado", command=self.clear_result).pack(fill="x", padx=7, pady=(0, 5))

        conversion = ttk.LabelFrame(parent, text="Conversões", style="Section.TLabelframe")
        conversion.pack(fill="x", pady=(0, 8))
        for text, fn in [("Níveis de cinza", self.op_gray), ("Negativo", self.op_negative), ("Binário – Otsu", self.op_otsu)]:
            ttk.Button(conversion, text=text, command=fn).pack(fill="x", padx=7, pady=2)

        filt = ttk.LabelFrame(parent, text="Filtros e bordas", style="Section.TLabelframe")
        filt.pack(fill="x", pady=(0, 8))
        self._spin(filt, "Janela do filtro", self.kernel_size, 3, 15)
        ttk.Button(filt, text="Média", command=self.op_mean).pack(fill="x", padx=7, pady=2)
        ttk.Button(filt, text="Mediana", command=self.op_median).pack(fill="x", padx=7, pady=2)
        self._spin(filt, "Limiar mínimo Canny", self.low_threshold, 0, 255)
        self._spin(filt, "Limiar máximo Canny", self.high_threshold, 1, 255)
        ttk.Button(filt, text="Canny", command=self.op_canny).pack(fill="x", padx=7, pady=2)

        morph = ttk.LabelFrame(parent, text="Morfologia", style="Section.TLabelframe")
        morph.pack(fill="x", pady=(0, 8))
        self._spin(morph, "Elemento quadrado", self.kernel_size, 3, 15)
        for text, fn in [("Erosão", self.op_erode), ("Dilatação", self.op_dilate), ("Abertura", self.op_opening), ("Fechamento", self.op_closing)]:
            ttk.Button(morph, text=text, command=fn).pack(fill="x", padx=7, pady=1)

        analysis = ttk.LabelFrame(parent, text="Análise de imagem", style="Section.TLabelframe")
        analysis.pack(fill="x", pady=(0, 8))
        self._spin(analysis, "Conectividade", self.connectivity, 4, 8, values=(4, 8))
        ttk.Button(analysis, text="Histograma", command=self.op_histogram).pack(fill="x", padx=7, pady=2)
        ttk.Button(analysis, text="Objetos e medidas", command=self.op_components).pack(fill="x", padx=7, pady=2)

        extras = ttk.LabelFrame(parent, text="Recursos extras", style="Section.TLabelframe")
        extras.pack(fill="x", pady=(0, 8))
        ttk.Label(extras, text="Filtro por cor").pack(anchor="w", padx=7, pady=(5, 0))
        ttk.Combobox(extras, textvariable=self.color_name, values=("Vermelho", "Verde", "Azul"), state="readonly").pack(fill="x", padx=7, pady=2)
        ttk.Scale(extras, from_=0.0, to=1.0, variable=self.color_intensity, orient="horizontal").pack(fill="x", padx=7)
        ttk.Button(extras, text="Aplicar filtro por cor", command=self.op_color).pack(fill="x", padx=7, pady=2)

    def _spin(self, parent, label, variable, from_, to, values=None) -> None:
        row = ttk.Frame(parent); row.pack(fill="x", padx=7, pady=2)
        ttk.Label(row, text=label).pack(side="left", fill="x", expand=True)
        ttk.Spinbox(row, textvariable=variable, from_=from_, to=to, values=values, width=5).pack(side="right")

    def _build_view(self, parent: ttk.Frame) -> None:
        self.tabs = ttk.Notebook(parent)
        self.tabs.grid(row=0, column=0, rowspan=4, sticky="nsew")
        image_tab = ttk.Frame(self.tabs); camera_tab = ttk.Frame(self.tabs)
        self.tabs.add(image_tab, text="Imagem"); self.tabs.add(camera_tab, text="Câmera")
        self._build_image_tab(image_tab)
        self._build_camera_tab(camera_tab)

    def _build_image_tab(self, tab: ttk.Frame) -> None:
        tab.columnconfigure(0, weight=1); tab.columnconfigure(1, weight=1); tab.rowconfigure(1, weight=1)
        ttk.Label(tab, text="Original", font=("Arial", 10, "bold")).grid(row=0, column=0, pady=5)
        ttk.Label(tab, text="Resultado", font=("Arial", 10, "bold")).grid(row=0, column=1, pady=5)
        self.original_view = ttk.Label(tab, text="Nenhuma imagem carregada", anchor="center", relief="groove")
        self.result_view = ttk.Label(tab, text="Aplique uma operação", anchor="center", relief="groove")
        self.original_view.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.result_view.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

    def _build_camera_tab(self, tab: ttk.Frame) -> None:
        tab.columnconfigure(0, weight=1); tab.columnconfigure(1, weight=1); tab.rowconfigure(2, weight=1)
        top = ttk.Frame(tab); top.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        ttk.Label(top, text="Fonte (0 = webcam):").pack(side="left")
        ttk.Entry(top, textvariable=self.camera_source, width=12).pack(side="left", padx=5)
        ttk.Button(top, text="Iniciar câmera", command=self.start_camera).pack(side="left", padx=2)
        ttk.Button(top, text="Parar", command=self.stop_camera).pack(side="left", padx=2)
        ttk.Button(top, text="Tirar foto", command=self.take_photo).pack(side="left", padx=2)
        ttk.Label(tab, text="Câmera / vídeo", font=("Arial", 10, "bold")).grid(row=1, column=0, pady=3)
        ttk.Label(tab, text="Resultado", font=("Arial", 10, "bold")).grid(row=1, column=1, pady=3)
        self.camera_view = ttk.Label(tab, text="Câmera parada", anchor="center", relief="groove")
        self.video_result_view = ttk.Label(tab, text="Use os botões abaixo", anchor="center", relief="groove")
        self.camera_view.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        self.video_result_view.grid(row=2, column=1, sticky="nsew", padx=5, pady=5)
        actions = ttk.LabelFrame(tab, text="Detecção de caneta e música")
        actions.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        ttk.Button(actions, text="Detectar caneta (YOLO)", command=self.start_pen_detection).pack(side="left", padx=5, pady=5)
        ttk.Button(actions, text="Parar detecção", command=self.stop_pen_detection).pack(side="left", padx=5)
        ttk.Button(actions, text="Selecionar para rastrear", command=self.select_object).pack(side="left", padx=5)
        ttk.Button(actions, text="Parar rastreamento", command=self.stop_tracking).pack(side="left", padx=5)
        ttk.Button(actions, text="Escolher música...", command=self.choose_audio).pack(side="left", padx=5)
        ttk.Label(actions, textvariable=self.audio_path).pack(side="left", padx=5)
        ttk.Button(actions, text="Sem filtro", command=self.stop_live_filter).pack(side="left", padx=5)
        ops = ttk.Frame(tab); ops.grid(row=4, column=0, columnspan=2, sticky="ew", padx=5)
        for text, fn in [("Cinza", self.video_gray), ("Negativo", self.video_negative),
                         ("Otsu", self.video_otsu), ("Canny", self.video_canny)]:
            ttk.Button(ops, text=text, command=fn).pack(side="left", padx=2, pady=4)

    def _show(self, widget, image: Optional[np.ndarray], target="original") -> None:
        if image is None: return
        if image.ndim == 2: rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        else: rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb)
        pil.thumbnail((470, 420), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(pil)
        widget.configure(image=photo, text="")
        if target == "original": self.original_photo = photo
        elif target == "result": self.result_photo = photo
        elif target == "video_result": self.video_result_photo = photo
        else: self.camera_photo = photo

    def load_image(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff"), ("Todos", "*.*")])
        if not path: return
        try:
            image = load_image(path)
        except FileNotFoundError as exc:
            messagebox.showerror("Erro", str(exc)); return
        self.image, self.gray = image, to_gray(image)
        self._show(self.original_view, image, "original"); self.result_view.configure(image="", text="Aplique uma operação")
        self.status.set(f"Imagem carregada: {Path(path).name}")

    def require_image(self) -> bool:
        return self.active_source() is not None

    def active_source(self) -> Optional[np.ndarray]:
        """Retorna o quadro da câmera quando ela está ativa; caso contrário, a imagem."""
        if self.camera_running and self.current_frame is not None:
            return self.current_frame
        return self.image

    def active_gray(self) -> Optional[np.ndarray]:
        source = self.active_source()
        return None if source is None else to_gray(source)

    def no_source_message(self) -> None:
        messagebox.showinfo("Entrada necessária", "Carregue uma imagem ou inicie a câmera primeiro.")

    def set_result(self, result: np.ndarray, title: str) -> None:
        self._show(self.result_view, result, "result"); self.status.set(title)

    def set_active_result(self, result: np.ndarray, title: str) -> None:
        """Exibe o resultado na aba correspondente à fonte atualmente ativa."""
        if self.camera_running:
            self._show(self.video_result_view, result, "video_result")
        else:
            self._show(self.result_view, result, "result")
        self.status.set(title)

    def op_gray(self):
        gray = self.active_gray()
        if gray is not None:
            if self.camera_running:
                self.set_live_filter("Níveis de cinza", lambda frame: to_gray(frame))
            else: self.set_active_result(gray, "Conversão para níveis de cinza")
        else: self.no_source_message()
    def op_negative(self):
        source = self.active_source()
        if source is not None:
            if self.camera_running:
                self.set_live_filter("Negativo", lambda frame: negative(frame))
            else: self.set_active_result(negative(source), "Negativo")
        else: self.no_source_message()
    def op_otsu(self):
        gray = self.active_gray()
        if gray is not None:
            if self.camera_running:
                self.set_live_filter("Otsu", lambda frame: otsu(to_gray(frame))[1])
            else:
                threshold, result = otsu(gray); self.set_active_result(result, f"Otsu — limiar calculado: {threshold}")
        else: self.no_source_message()
    def op_mean(self):
        gray = self.active_gray()
        if gray is not None:
            if self.camera_running:
                self.set_live_filter("Média", lambda frame: mean_filter(to_gray(frame), self.kernel_size.get()))
            else: self.set_active_result(mean_filter(gray, self.kernel_size.get()), "Filtro da média")
        else: self.no_source_message()
    def op_median(self):
        gray = self.active_gray()
        if gray is not None:
            if self.camera_running:
                self.set_live_filter("Mediana", lambda frame: median_filter(to_gray(frame), self.kernel_size.get()))
            else: self.set_active_result(median_filter(gray, self.kernel_size.get()), "Filtro da mediana")
        else: self.no_source_message()
    def op_canny(self):
        gray = self.active_gray()
        if gray is not None:
            if self.camera_running:
                self.set_live_filter("Canny", lambda frame: canny(to_gray(frame), self.low_threshold.get(), self.high_threshold.get()))
            else: self.set_active_result(canny(gray, self.low_threshold.get(), self.high_threshold.get()), "Canny autoral")
        else: self.no_source_message()

    def set_live_filter(self, name, operation) -> None:
        """Ativa um filtro contínuo; a operação será reaplicada em cada quadro."""
        self.live_filter = operation
        self.live_filter_name = name
        if self.current_frame is not None:
            self.video_operation(operation(self.current_frame), f"Filtro {name} em tempo real")
        self.status.set(f"Operação {name} em tempo real ativada. Cada novo quadro será processado automaticamente.")

    def stop_live_filter(self) -> None:
        self.live_filter = None
        self.live_filter_name = "Sem filtro"
        self.status.set("Processamento em tempo real desativado.")
    def binary_for_morph(self):
        gray = self.active_gray()
        return None if gray is None else otsu(gray)[1]
    def op_erode(self):
        if self.camera_running and self.current_frame is not None:
            self.set_live_filter("Erosão", lambda frame: erode(otsu(to_gray(frame))[1], self.kernel_size.get()))
        else:
            b = self.binary_for_morph(); b is not None and self.set_active_result(erode(b, self.kernel_size.get()), "Erosão após Otsu")
            b is None and self.no_source_message()
    def op_dilate(self):
        if self.camera_running and self.current_frame is not None:
            self.set_live_filter("Dilatação", lambda frame: dilate(otsu(to_gray(frame))[1], self.kernel_size.get()))
        else:
            b = self.binary_for_morph(); b is not None and self.set_active_result(dilate(b, self.kernel_size.get()), "Dilatação após Otsu")
            b is None and self.no_source_message()
    def op_opening(self):
        if self.camera_running and self.current_frame is not None:
            self.set_live_filter("Abertura", lambda frame: opening(otsu(to_gray(frame))[1], self.kernel_size.get()))
        else:
            b = self.binary_for_morph(); b is not None and self.set_active_result(opening(b, self.kernel_size.get()), "Abertura após Otsu")
            b is None and self.no_source_message()
    def op_closing(self):
        if self.camera_running and self.current_frame is not None:
            self.set_live_filter("Fechamento", lambda frame: closing(otsu(to_gray(frame))[1], self.kernel_size.get()))
        else:
            b = self.binary_for_morph(); b is not None and self.set_active_result(closing(b, self.kernel_size.get()), "Fechamento após Otsu")
            b is None and self.no_source_message()
    def op_histogram(self):
        gray = self.active_gray()
        if gray is not None: self.set_active_result(draw_histogram(gray), "Histograma")
        else: self.no_source_message()
    def op_components(self):
        gray = self.active_gray()
        if gray is None: self.no_source_message(); return
        threshold, binary = otsu(gray); labels, components = connected_components(binary, self.connectivity.get())
        result = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
        lines = [f"Otsu: {threshold} | Objetos: {len(components)}"]
        for c in components:
            x, y, w, h = c.bbox; cv2.rectangle(result, (x, y), (x+w, y+h), (0, 0, 255), 2); cv2.putText(result, str(c.label), (x, max(15, y-4)), cv2.FONT_HERSHEY_SIMPLEX, .6, (255, 0, 0), 2)
            lines.append(f"#{c.label}: área={c.area}px | perímetro={c.perimeter}px | diâmetro={c.diameter:.2f}px")
        self.set_active_result(result, "\n".join(lines))
        messagebox.showinfo("Medições dos objetos", "\n".join(lines))

    def color_operation(self, frame: np.ndarray) -> np.ndarray:
        """Mantém somente a cor escolhida, com intensidade ajustável."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        ranges = {
            "Vermelho": ((0, 120, 70), (10, 255, 255), (170, 120, 70), (180, 255, 255)),
            "Verde": ((35, 50, 50), (85, 255, 255), None, None),
            "Azul": ((90, 60, 50), (130, 255, 255), None, None),
        }
        lower, upper, lower2, upper2 = ranges[self.color_name.get()]
        mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
        if lower2 is not None:
            mask |= cv2.inRange(hsv, np.array(lower2), np.array(upper2))
        selected = cv2.bitwise_and(frame, frame, mask=mask)
        intensity = float(self.color_intensity.get())
        return cv2.addWeighted(frame, 1.0 - intensity, selected, intensity, 0)

    def op_color(self):
        source = self.active_source()
        if source is None:
            self.no_source_message(); return
        if self.camera_running:
            self.set_live_filter(f"Cor {self.color_name.get()}", self.color_operation)
        else:
            self.set_active_result(self.color_operation(source), f"Filtro por cor: {self.color_name.get()}")

    def take_photo(self):
        frame = self.last_video_result if self.last_video_result is not None else self.current_frame
        if frame is None:
            messagebox.showinfo("Captura", "Inicie a câmera antes de tirar uma foto."); return
        self.photo_counter += 1
        path = Path.cwd() / f"foto_{self.photo_counter:03d}.png"
        cv2.imwrite(str(path), frame)
        self.status.set(f"Foto salva: {path.name}")
    def clear_result(self): self.result_view.configure(image="", text="Aplique uma operação"); self.result_photo = None

    def start_camera(self) -> None:
        self.stop_camera()
        source = self.camera_source.get().strip() or "0"
        self.cap = cv2.VideoCapture(int(source) if source.isdigit() else source)
        if not self.cap.isOpened(): self.cap = None; messagebox.showerror("Câmera", f"Não foi possível abrir: {source}"); return
        self.camera_running = True
        self.status.set("Câmera em execução — os botões da barra lateral usarão o quadro atual."); self._update_camera()

    def _update_camera(self) -> None:
        if self.cap is None: return
        ok, frame = self.cap.read()
        if ok:
            self.current_frame = frame
            display = frame.copy()
            if self.pen_detection_active and self.pen_detector is not None:
                try:
                    display, detections = self.pen_detector.annotate(frame)
                    if detections and self.audio_path.get() and not self.audio_played:
                        if play_music(self.audio_path.get()):
                            self.audio_played = True
                            self.status.set("Caneta reconhecida pelo YOLO; música acionada.")
                    elif not detections:
                        stop_music()
                        self.audio_played = False
                        self.status.set("Nenhuma caneta detectada; música parada.")
                except Exception as exc:
                    self.stop_pen_detection()
                    self.status.set(f"Detecção YOLO interrompida: {exc}")
            if self.tracking and self.tracker is not None:
                tracked, box = self.tracker.update(frame)
                if tracked:
                    x, y, w, h = map(int, box)
                    cv2.rectangle(display, (x, y), (x + w, y + h), (255, 180, 0), 2)
                    cv2.putText(display, f"Rastreamento {self.tracker_name}", (x, max(20, y - 8)), cv2.FONT_HERSHEY_SIMPLEX, .6, (255, 180, 0), 2)
                else:
                    self.tracking = False
                    self.status.set("O rastreador perdeu o objeto.")
            self._show(self.camera_view, display, "camera")
            if self.live_filter is not None:
                try:
                    live_result = self.live_filter(frame)
                    self.last_video_result = live_result.copy()
                    self._show(self.video_result_view, live_result, "video_result")
                    self.status.set(f"Operação {self.live_filter_name} processando em tempo real")
                except ValueError as exc:
                    self.stop_live_filter(); self.status.set(f"Filtro interrompido: {exc}")
        self.after(30, self._update_camera)

    def stop_camera(self) -> None:
        if self.cap is not None: self.cap.release(); self.cap = None
        self.camera_running = False; self.stop_pen_detection(); self.stop_tracking(); self.stop_live_filter(); self.status.set("Câmera parada")

    def start_pen_detection(self) -> None:
        if not self.camera_running or self.current_frame is None:
            messagebox.showinfo("YOLO", "Inicie a câmera ou abra um vídeo antes de detectar a caneta."); return
        try:
            if self.pen_detector is None:
                self.status.set("Carregando YOLO-World; na primeira execução o modelo será baixado...")
                self.update_idletasks()
                self.pen_detector = PenDetector()
            self.pen_detection_active = True
            self.audio_played = False
            self.status.set("Detecção de caneta YOLO ativa; aguardando uma caneta no vídeo.")
        except Exception as exc:
            messagebox.showerror("YOLO", str(exc))

    def stop_pen_detection(self) -> None:
        self.pen_detection_active = False
        stop_music()
        self.audio_played = False

    def select_object(self) -> None:
        if self.current_frame is None or not self.camera_running:
            messagebox.showinfo("Rastreamento", "Inicie a câmera antes de selecionar um objeto."); return
        factory, name = choose_tracker()
        if factory is None:
            messagebox.showerror("Rastreamento", "Nenhum rastreador disponível nesta instalação do OpenCV."); return
        roi = cv2.selectROI("Selecione o objeto e pressione ENTER", self.current_frame, fromCenter=False, showCrosshair=True)
        cv2.destroyWindow("Selecione o objeto e pressione ENTER")
        if roi[2] <= 0 or roi[3] <= 0: return
        self.tracker = factory()
        self.tracker.init(self.current_frame, roi)
        self.tracker_name = name
        self.tracking = True
        self.status.set(f"Rastreamento {name} iniciado.")

    def stop_tracking(self) -> None:
        self.tracking = False
        self.tracker = None
        self.tracker_name = ""
    def choose_audio(self):
        path = filedialog.askopenfilename(filetypes=[("Áudio", "*.wav *.mp3 *.ogg"), ("Todos", "*.*")])
        if path: self.audio_path.set(path); self.status.set(f"Música selecionada: {Path(path).name}")
    def video_operation(self, result, title):
        if self.current_frame is None: messagebox.showinfo("Vídeo", "Inicie a câmera primeiro."); return
        self.last_video_result = result.copy()
        self._show(self.video_result_view, result, "video_result"); self.status.set(f"Vídeo — {title}")
    def video_gray(self):
        if self.current_frame is None: messagebox.showinfo("Vídeo", "Inicie a câmera primeiro."); return
        self.video_operation(to_gray(self.current_frame), "Cinza")
    def video_negative(self):
        if self.current_frame is None: messagebox.showinfo("Vídeo", "Inicie a câmera primeiro."); return
        self.video_operation(negative(self.current_frame), "Negativo")
    def video_canny(self):
        if self.current_frame is None: messagebox.showinfo("Vídeo", "Inicie a câmera primeiro."); return
        self.video_operation(canny(to_gray(self.current_frame), self.low_threshold.get(), self.high_threshold.get()), "Canny")
    def video_otsu(self):
        if self.current_frame is None: messagebox.showinfo("Vídeo", "Inicie a câmera primeiro."); return
        threshold, result = otsu(to_gray(self.current_frame)); self.video_operation(result, f"Otsu (limiar {threshold})")
    def close(self): self.stop_camera(); self.destroy()


def run_gui() -> None:
    app = PDIApp(); app.mainloop()
