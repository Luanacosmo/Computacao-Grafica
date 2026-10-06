from __future__ import annotations

import argparse
import cv2
import numpy as np
from conversoes import negative, otsu, to_gray
from entradas import load_image
from filtros import canny, mean_filter, median_filter
from histograma import draw_histogram
from morfologia import closing, dilate, erode, opening
from objetos import connected_components
from video import process_video, show

def process_image(path: str) -> None:
    image = load_image(path)
    gray = to_gray(image)
    print("\nOperações: 1 cinza | 2 negativo | 3 Otsu | 4 média | 5 mediana | 6 Canny | 7 morfologia | 8 histograma | 9 componentes | 0 voltar")
    while True:
        op = input("Escolha: ").strip()
        if op == "0": break
        if op == "1": result, title = gray, "Níveis de cinza"
        elif op == "2": result, title = negative(image), "Negativo"
        elif op == "3":
            threshold, result = otsu(gray); title = f"Otsu (limiar={threshold})"; print(f"Limiar calculado: {threshold}")
        elif op in {"4", "5"}:
            size = int(input("Janela ímpar (3, 5, ...): "))
            result = mean_filter(gray, size) if op == "4" else median_filter(gray, size)
            title = "Filtro da média" if op == "4" else "Filtro da mediana"
        elif op == "6": result, title = canny(gray), "Canny autoral"
        elif op == "7":
            threshold, binary = otsu(gray); size = int(input("Tamanho do elemento (ímpar): "))
            print("1 erosão | 2 dilatação | 3 abertura | 4 fechamento")
            kind = input("Operação: ")
            fn = {"1": erode, "2": dilate, "3": opening, "4": closing}.get(kind)
            if not fn: print("Opção inválida."); continue
            result, title = fn(binary, size), f"Morfologia (Otsu={threshold})"
        elif op == "8": show("Histograma", draw_histogram(gray)); continue
        elif op == "9":
            threshold, binary = otsu(gray); _, components = connected_components(binary)
            print(f"Limiar Otsu: {threshold}; objetos encontrados: {len(components)}")
            for c in components: print(f"#{c.label}: área={c.area}px, perímetro={c.perimeter}px, diâmetro={c.diameter:.2f}px, centroide=({c.centroid[0]:.1f},{c.centroid[1]:.1f})")
            result = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
            for c in components:
                x, y, w, h = c.bbox; cv2.rectangle(result, (x, y), (x + w, y + h), (0, 0, 255), 2); cv2.putText(result, str(c.label), (x, max(15, y - 4)), cv2.FONT_HERSHEY_SIMPLEX, .6, (255, 0, 0), 2)
            title = "Componentes conexos"
        else: print("Opção inválida."); continue
        show(title, result)
    cv2.destroyAllWindows()

def menu() -> None:
    print("\n=== TRABALHO PRÁTICO DE PDI ===\n1 - Carregar imagem\n2 - Câmera/vídeo\n3 - Teste dos algoritmos\n0 - Sair")
    while True:
        choice = input("Escolha: ").strip()
        if choice == "0": break
        try:
            if choice == "1": process_image(input("Caminho da imagem: ").strip())
            elif choice == "2": process_video(input("Fonte (0 para câmera ou caminho): ").strip() or "0", input("Áudio (Enter para nenhum): ").strip() or None)
            elif choice == "3": self_test()
            else: print("Opção inválida.")
        except (ValueError, FileNotFoundError, RuntimeError) as exc: print(f"Erro: {exc}")


def self_test() -> None:
    image = np.zeros((80, 100), dtype=np.uint8); image[10:30, 10:30] = 255; image[45:70, 60:90] = 255
    threshold, binary = otsu(image); _, comps = connected_components(binary)
    assert threshold == 0 and len(comps) == 2
    assert negative(np.array([[0, 255]], dtype=np.uint8)).tolist() == [[255, 0]]
    assert mean_filter(image, 3).shape == image.shape and median_filter(image, 3).shape == image.shape
    assert canny(image).shape == image.shape
    assert opening(binary, 3).shape == image.shape and closing(binary, 3).shape == image.shape
    assert draw_histogram(image).shape == (420, 700, 3)
    print(f"OK: {len(comps)} componentes; áreas={[c.area for c in comps]}; todos os testes passaram.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Trabalho prático de PDI")
    parser.add_argument("--self-test", action="store_true", help="executa testes sem abrir câmera")
    parser.add_argument("--cli", action="store_true", help="usa a interface de terminal em vez da GUI")
    args = parser.parse_args()
    if args.self_test: self_test()
    elif args.cli:
        menu()
    else:
        try:
            from interface import run_gui
            run_gui()
        except Exception as exc:
            print(f"GUI indisponível ({exc}); usando interface CLI.")
            menu()


if __name__ == "__main__":
    main()
