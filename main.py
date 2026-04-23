"""Orquestador CLI del transpilador de Micro C a Python."""

from __future__ import annotations

import argparse
from pathlib import Path

from generator import ErrorGeneracion, GeneradorPython
from lexer import ErrorLexico, Lexer
from parser import ErrorSintactico, Parser


def lanzar_gui_visualizador(archivo_entrada: Path) -> None:
    """Abre la GUI del visualizador y compila automáticamente el archivo indicado."""
    try:
        import tkinter as tk

        from gui_visualizer import VisualizadorCompilador

        raiz = tk.Tk()
        app = VisualizadorCompilador(raiz)
        app.compilar_archivo_directo(archivo_entrada)
        raiz.mainloop()
    except Exception as error_gui:  # pragma: no cover
        print("No fue posible iniciar la interfaz gráfica del visualizador.")
        print(f"Detalle: {error_gui}")


def construir_argumentos() -> argparse.Namespace:
    """Construye y parsea los argumentos de línea de comandos."""
    analizador_argumentos = argparse.ArgumentParser(
        description="Transpilador de Micro C (.uc/.mc) a Python."
    )
    analizador_argumentos.add_argument(
        "archivo_entrada",
        type=Path,
        help="Ruta del archivo fuente con extensión .uc o .mc",
    )
    analizador_argumentos.add_argument(
        "-o",
        "--salida",
        dest="archivo_salida",
        type=Path,
        default=None,
        help="Parámetro legado. La salida se guarda en output/salida_<archivo>.py",
    )
    return analizador_argumentos.parse_args()


def validar_archivo_entrada(archivo_entrada: Path) -> None:
    """Valida existencia y extensión permitida del archivo de entrada."""
    extensiones_validas: set[str] = {".uc", ".mc"}

    if archivo_entrada.suffix.lower() not in extensiones_validas:
        raise ValueError("La entrada debe tener extensión .uc o .mc.")

    if not archivo_entrada.exists():
        raise FileNotFoundError(f"No existe el archivo: {archivo_entrada}")

    if not archivo_entrada.is_file():
        raise ValueError(f"La ruta no apunta a un archivo válido: {archivo_entrada}")


def resolver_ruta_salida(archivo_entrada: Path, archivo_salida: Path | None) -> Path:
    """Resuelve salida obligatoria en carpeta output con nombre estandarizado."""
    carpeta_salida: Path = Path.cwd() / "output"
    carpeta_salida.mkdir(parents=True, exist_ok=True)

    if archivo_salida is not None:
        print(
            "Aviso: se recibió -o/--salida, pero se usará la convención "
            "output/salida_<archivo>.py"
        )

    nombre_archivo_python: str = f"salida_{archivo_entrada.stem}.py"
    return carpeta_salida / nombre_archivo_python


def transcompilar_codigo(codigo_fuente: str) -> str:
    """Orquesta el flujo Lexer -> Parser -> Generator y retorna código Python."""
    lexer = Lexer(codigo_fuente)
    tokens = lexer.tokenizar()

    parser = Parser(tokens)
    ast = parser.parsear()

    generador = GeneradorPython()
    return generador.generar(ast)


def ejecutar() -> int:
    """Punto de entrada del CLI."""
    argumentos = construir_argumentos()
    archivo_entrada: Path = argumentos.archivo_entrada
    archivo_salida: Path = resolver_ruta_salida(archivo_entrada, argumentos.archivo_salida)

    try:
        validar_archivo_entrada(archivo_entrada)
        codigo_fuente: str = archivo_entrada.read_text(encoding="utf-8")
        codigo_python: str = transcompilar_codigo(codigo_fuente)
        archivo_salida.write_text(f"{codigo_python}\n", encoding="utf-8")
        print(f"Transpilación exitosa. Archivo generado: {archivo_salida}")
        print("Abriendo GUI educativa para visualizar Lexer/Parser...")
        lanzar_gui_visualizador(archivo_entrada)
        return 0
    except (ErrorLexico, ErrorSintactico) as error_sintaxis:
        print("Se detectó un error durante el análisis del programa Micro C.")
        print(f"Detalle: {error_sintaxis}")
        return 1
    except (FileNotFoundError, PermissionError, ValueError) as error_entrada:
        print("No fue posible procesar el archivo de entrada/salida.")
        print(f"Detalle: {error_entrada}")
        return 1
    except ErrorGeneracion as error_generacion:
        print("El AST se construyó, pero falló la generación de código Python.")
        print(f"Detalle: {error_generacion}")
        return 1
    except Exception as error_general:  # pragma: no cover
        print("Ocurrió un error inesperado durante la transpilación.")
        print(f"Detalle: {error_general}")
        return 1


if __name__ == "__main__":
    raise SystemExit(ejecutar())
