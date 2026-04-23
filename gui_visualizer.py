"""Interfaz gráfica educativa para visualizar el pipeline del transpilador."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
from typing import Any

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from generator import ErrorGeneracion, GeneradorPython
from lexer import ErrorLexico, Lexer
from parser import ErrorSintactico, Parser


def pretty_print_ast(nodo: Any, nivel: int = 0) -> list[str]:
    """Convierte un AST arbitrario en una lista de líneas con indentación."""
    indentacion: str = "    " * nivel

    if nodo is None:
        return [f"{indentacion}None"]

    if is_dataclass(nodo):
        lineas: list[str] = [f"{indentacion}{type(nodo).__name__}"]
        for campo in fields(nodo):
            valor_campo: Any = getattr(nodo, campo.name)
            lineas.append(f"{indentacion}  {campo.name}:")
            lineas.extend(pretty_print_ast(valor_campo, nivel + 1))
        return lineas

    if isinstance(nodo, list):
        lineas_lista: list[str] = [f"{indentacion}["]
        for indice, elemento in enumerate(nodo):
            lineas_lista.append(f"{indentacion}  [{indice}]")
            lineas_lista.extend(pretty_print_ast(elemento, nivel + 2))
        lineas_lista.append(f"{indentacion}]")
        return lineas_lista

    return [f"{indentacion}{repr(nodo)}"]


class VisualizadorCompilador:
    """Controla la GUI de visualización y animación del análisis."""

    def __init__(self, raiz: tk.Tk) -> None:
        """Inicializa widgets, estado y ciclo de revisión del hilo de fondo."""
        self.raiz: tk.Tk = raiz
        self.raiz.title("Proyecto Final - Compiladores - Demian, Daniel y Luca")
        self.raiz.geometry("1200x720")

        self.cola_resultados: Queue[tuple[str, Any]] = Queue()
        self.archivo_actual: Path | None = None

        self.lineas_tokens: list[str] = []
        self.lineas_ast: list[str] = []
        self.lineas_generador: list[str] = []

        self.indice_token: int = 0
        self.indice_ast: int = 0
        self.indice_generador: int = 0
        self.etapa_animacion: str = "detenido"
        self.animacion_activa: bool = False

        self._construir_interfaz()
        self._programar_revision_cola()

    def _construir_interfaz(self) -> None:
        """Construye el layout principal con controles y paneles visuales."""
        marco_controles = ttk.Frame(self.raiz, padding=10)
        marco_controles.pack(side=tk.TOP, fill=tk.X)

        self.boton_cargar = ttk.Button(
            marco_controles,
            text="Cargar y Compilar Archivo .uc",
            command=self.cargar_y_compilar_archivo,
        )
        self.boton_cargar.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(marco_controles, text="Velocidad:").pack(side=tk.LEFT)
        self.slider_velocidad = ttk.Scale(
            marco_controles,
            from_=1,
            to=10,
            orient=tk.HORIZONTAL,
            length=220,
        )
        self.slider_velocidad.set(5)
        self.slider_velocidad.pack(side=tk.LEFT, padx=8)

        self.etiqueta_velocidad = ttk.Label(marco_controles, text="Nivel 5")
        self.etiqueta_velocidad.pack(side=tk.LEFT, padx=(0, 16))
        self.slider_velocidad.configure(command=self._actualizar_etiqueta_velocidad)

        self.boton_animar = ttk.Button(
            marco_controles,
            text="Animar Paso a Paso",
            command=self.iniciar_animacion,
            state=tk.DISABLED,
        )
        self.boton_animar.pack(side=tk.LEFT)

        self.estado_var = tk.StringVar(value="Esperando archivo para compilar...")
        self.etiqueta_estado = ttk.Label(
            marco_controles,
            textvariable=self.estado_var,
            anchor="w",
        )
        self.etiqueta_estado.pack(side=tk.LEFT, padx=(16, 0), fill=tk.X, expand=True)

        self.paned = ttk.Panedwindow(self.raiz, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        panel_lexer = ttk.LabelFrame(self.paned, text="Fase Lexer (Tokens)", padding=8)
        panel_parser = ttk.LabelFrame(self.paned, text="Fase Parser (AST)", padding=8)
        panel_generador = ttk.LabelFrame(
            self.paned, text="Fase Generador (Python)", padding=8
        )

        self.paned.add(panel_lexer, weight=3)
        self.paned.add(panel_parser, weight=4)
        self.paned.add(panel_generador, weight=3)

        self.texto_lexer = self._crear_texto_solo_lectura(panel_lexer)
        self.texto_parser = self._crear_texto_solo_lectura(panel_parser)
        self.texto_generador = self._crear_texto_solo_lectura(panel_generador)

    def _crear_texto_solo_lectura(self, contenedor: ttk.LabelFrame) -> tk.Text:
        """Crea un widget de texto con scroll y modo solo lectura."""
        marco = ttk.Frame(contenedor)
        marco.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(marco, orient=tk.VERTICAL)
        texto = tk.Text(
            marco,
            wrap=tk.NONE,
            yscrollcommand=scrollbar.set,
            font=("Consolas", 10),
            state=tk.DISABLED,
        )
        scrollbar.config(command=texto.yview)

        texto.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        return texto

    def _actualizar_etiqueta_velocidad(self, _: str) -> None:
        """Actualiza la etiqueta de velocidad al mover el slider."""
        nivel: int = int(float(self.slider_velocidad.get()))
        self.etiqueta_velocidad.config(text=f"Nivel {nivel}")

    def _programar_revision_cola(self) -> None:
        """Consulta periódicamente la cola para integrar resultados del hilo."""
        self._procesar_cola_resultados()
        self.raiz.after(100, self._programar_revision_cola)

    def _procesar_cola_resultados(self) -> None:
        """Procesa eventos de compilación enviados por el hilo de fondo."""
        try:
            while True:
                tipo_evento, payload = self.cola_resultados.get_nowait()
                if tipo_evento == "ok":
                    self._manejar_compilacion_exitosa(payload)
                elif tipo_evento == "error":
                    self._manejar_compilacion_fallida(str(payload))
        except Empty:
            return

    def cargar_y_compilar_archivo(self) -> None:
        """Permite seleccionar un archivo y ejecuta el pipeline en background."""
        if self.animacion_activa:
            return

        ruta = filedialog.askopenfilename(
            title="Selecciona un archivo Micro C",
            filetypes=[
                ("Archivos Micro C", "*.uc *.mc"),
                ("Archivo .uc", "*.uc"),
                ("Archivo .mc", "*.mc"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if not ruta:
            return

        self.archivo_actual = Path(ruta)
        self._iniciar_compilacion_actual()

    def compilar_archivo_directo(self, ruta_archivo: Path) -> None:
        """Inicia compilación desde una ruta recibida externamente (por ejemplo CLI)."""
        if self.animacion_activa:
            return
        self.archivo_actual = Path(ruta_archivo)
        self._iniciar_compilacion_actual()

    def _iniciar_compilacion_actual(self) -> None:
        """Configura estado UI e inicia el hilo de compilación para archivo_actual."""
        self._limpiar_paneles_analisis()
        self._actualizar_estado("Compilando en background...")
        self.boton_cargar.config(state=tk.DISABLED)
        self.boton_animar.config(state=tk.DISABLED)

        hilo = Thread(target=self._compilar_en_background, daemon=True)
        hilo.start()

    def _compilar_en_background(self) -> None:
        """Ejecuta lexer, parser y generador; además guarda .lex, .ast y .py."""
        if self.archivo_actual is None:
            self.cola_resultados.put(("error", "No hay archivo seleccionado."))
            return

        try:
            codigo_fuente: str = self.archivo_actual.read_text(encoding="utf-8")

            lexer = Lexer(codigo_fuente)
            tokens = lexer.tokenizar()

            parser = Parser(tokens)
            ast = parser.parsear()

            generador = GeneradorPython()
            codigo_python: str = generador.generar(ast)

            lineas_tokens: list[str] = [self._formatear_token(token) for token in tokens]
            lineas_ast: list[str] = pretty_print_ast(ast)
            lineas_generador: list[str] = codigo_python.splitlines()

            carpeta_salida: Path = Path.cwd() / "output"
            carpeta_salida.mkdir(parents=True, exist_ok=True)

            base_nombre: str = self.archivo_actual.stem
            ruta_lex: Path = carpeta_salida / f"{base_nombre}.lex"
            ruta_ast: Path = carpeta_salida / f"{base_nombre}.ast"
            ruta_py: Path = carpeta_salida / f"salida_{base_nombre}.py"

            ruta_lex.write_text("\n".join(lineas_tokens) + "\n", encoding="utf-8")
            ruta_ast.write_text("\n".join(lineas_ast) + "\n", encoding="utf-8")
            ruta_py.write_text(codigo_python + "\n", encoding="utf-8")

            self.cola_resultados.put(
                (
                    "ok",
                    {
                        "lineas_tokens": lineas_tokens,
                        "lineas_ast": lineas_ast,
                        "lineas_generador": lineas_generador,
                        "ruta_lex": ruta_lex,
                        "ruta_ast": ruta_ast,
                        "ruta_py": ruta_py,
                    },
                )
            )
        except (ErrorLexico, ErrorSintactico, ErrorGeneracion) as error_compilacion:
            self.cola_resultados.put(("error", str(error_compilacion)))
        except Exception as error_general:  # pragma: no cover
            self.cola_resultados.put(("error", f"Error inesperado: {error_general}"))

    def _manejar_compilacion_exitosa(self, datos: dict[str, Any]) -> None:
        """Integra en UI los datos listos para animación y reporta archivos."""
        self.lineas_tokens = list(datos["lineas_tokens"])
        self.lineas_ast = list(datos["lineas_ast"])
        self.lineas_generador = list(datos["lineas_generador"])
        self.boton_cargar.config(state=tk.NORMAL)
        self.boton_animar.config(state=tk.NORMAL)

        self._actualizar_estado(
            "Compilación completada. Listo para animar Lexer, Parser y Generador."
        )

    def _manejar_compilacion_fallida(self, mensaje: str) -> None:
        """Muestra error amigable de compilación y reactiva controles."""
        self.boton_cargar.config(state=tk.NORMAL)
        self.boton_animar.config(state=tk.DISABLED)
        self._actualizar_estado("Compilación detenida por error.")
        messagebox.showerror("Error de compilación", mensaje)

    def iniciar_animacion(self) -> None:
        """Inicia playback no bloqueante: Lexer -> Parser -> Generador."""
        if not self.lineas_tokens and not self.lineas_ast and not self.lineas_generador:
            messagebox.showwarning("Sin datos", "Primero carga y compila un archivo.")
            return
        if self.animacion_activa:
            return

        self._limpiar_paneles_analisis()
        self.indice_token = 0
        self.indice_ast = 0
        self.indice_generador = 0
        self.etapa_animacion = "lexer"
        self.animacion_activa = True
        self.boton_cargar.config(state=tk.DISABLED)
        self.boton_animar.config(state=tk.DISABLED)
        self._actualizar_estado("Animación iniciada.")
        self._animar_siguiente_paso()

    def _animar_siguiente_paso(self) -> None:
        """Ejecuta un paso de animación y reprograma el siguiente con after()."""
        if self.etapa_animacion == "lexer":
            if self.indice_token < len(self.lineas_tokens):
                linea: str = self.lineas_tokens[self.indice_token]
                self._insertar_linea(self.texto_lexer, linea)
                self.indice_token += 1
                self.raiz.after(self._obtener_retraso_ms(), self._animar_siguiente_paso)
                return
            self.etapa_animacion = "parser"
            self.raiz.after(self._obtener_retraso_ms(), self._animar_siguiente_paso)
            return

        if self.etapa_animacion == "parser":
            if self.indice_ast < len(self.lineas_ast):
                linea_ast: str = self.lineas_ast[self.indice_ast]
                self._insertar_linea(self.texto_parser, linea_ast)
                self.indice_ast += 1
                self.raiz.after(self._obtener_retraso_ms(), self._animar_siguiente_paso)
                return
            self.etapa_animacion = "generador"
            self.raiz.after(self._obtener_retraso_ms(), self._animar_siguiente_paso)
            return

        if self.etapa_animacion == "generador":
            if self.indice_generador < len(self.lineas_generador):
                linea_generador: str = self.lineas_generador[self.indice_generador]
                self._insertar_linea(self.texto_generador, linea_generador)
                self.indice_generador += 1
                self.raiz.after(self._obtener_retraso_ms(), self._animar_siguiente_paso)
                return
            self.etapa_animacion = "detenido"
            self.animacion_activa = False
            self.boton_cargar.config(state=tk.NORMAL)
            self.boton_animar.config(state=tk.NORMAL)
            self._actualizar_estado("Animación finalizada.")

    def _obtener_retraso_ms(self) -> int:
        """Calcula retraso en milisegundos según el slider de velocidad."""
        nivel: int = int(float(self.slider_velocidad.get()))
        return max(60, 1100 - (nivel * 100))

    def _formatear_token(self, token: Any) -> str:
        """Formatea visualmente un token como [TIPO] -> valor."""
        lexema: str = token.lexema if token.lexema != "" else "<EOF>"
        return f"[{token.tipo.value}] -> {lexema}"

    def _insertar_linea(self, widget: tk.Text, linea: str) -> None:
        """Inserta una línea en un Text de solo lectura con auto-scroll."""
        widget.configure(state=tk.NORMAL)
        widget.insert(tk.END, linea + "\n")
        widget.see(tk.END)
        widget.configure(state=tk.DISABLED)

    def _actualizar_estado(self, mensaje: str) -> None:
        """Actualiza la barra de estado general de la interfaz."""
        self.estado_var.set(mensaje)

    def _limpiar_paneles_analisis(self) -> None:
        """Limpia los paneles de las tres fases para nueva corrida/animación."""
        for widget in (self.texto_lexer, self.texto_parser, self.texto_generador):
            widget.configure(state=tk.NORMAL)
            widget.delete("1.0", tk.END)
            widget.configure(state=tk.DISABLED)


def main() -> None:
    """Inicializa la aplicación de visualización y ejecuta el loop principal."""
    raiz = tk.Tk()
    VisualizadorCompilador(raiz)
    raiz.mainloop()


if __name__ == "__main__":
    main()
