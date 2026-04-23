"""Traductor de AST Micro C a código Python."""

from __future__ import annotations

from typing import Final

from parser import (
    Asignacion,
    Bloque,
    Expresion,
    Identificador,
    If,
    LiteralEntero,
    NodoMain,
    OperacionBinaria,
    Programa,
    Return,
    Sentencia,
    While,
)
from tokens import TipoToken


class ErrorGeneracion(Exception):
    """Error lanzado cuando se detecta un nodo AST no soportado para traducción."""


class GeneradorPython:
    """Genera código Python recorriendo el AST con patrón Visitor manual."""

    _ESPACIOS_POR_NIVEL: Final[int] = 4

    def __init__(self) -> None:
        """Inicializa el estado interno del generador."""
        self.nivel_indentacion: int = 0
        self.lineas_salida: list[str] = []

    def generar(self, programa: Programa) -> str:
        """Traduce un nodo Programa completo a texto Python."""
        self.nivel_indentacion = 0
        self.lineas_salida = []
        self.visitar(programa)
        return "\n".join(self.lineas_salida)

    def visitar(self, nodo: Programa | NodoMain | Sentencia | Expresion) -> str | None:
        """Despacha la visita al método correspondiente usando match-case."""
        match nodo:
            case Programa():
                self._visitar_programa(nodo)
                return None
            case NodoMain():
                self._visitar_main(nodo)
                return None
            case Bloque():
                self._visitar_bloque(nodo)
                return None
            case Asignacion():
                self._visitar_asignacion(nodo)
                return None
            case While():
                self._visitar_while(nodo)
                return None
            case If():
                self._visitar_if(nodo)
                return None
            case Return():
                self._visitar_return(nodo)
                return None
            case OperacionBinaria():
                return self._visitar_operacion_binaria(nodo)
            case LiteralEntero():
                return self._visitar_literal_entero(nodo)
            case Identificador():
                return self._visitar_identificador(nodo)
            case _:
                raise ErrorGeneracion(f"Nodo no soportado: {type(nodo).__name__}")

    def _agregar_linea(self, contenido: str) -> None:
        """Agrega una línea respetando el nivel actual de indentación."""
        prefijo: str = " " * (self.nivel_indentacion * self._ESPACIOS_POR_NIVEL)
        self.lineas_salida.append(f"{prefijo}{contenido}")

    def _incrementar_indentacion(self) -> None:
        """Aumenta en un nivel la indentación actual."""
        self.nivel_indentacion += 1

    def _decrementar_indentacion(self) -> None:
        """Disminuye en un nivel la indentación actual."""
        if self.nivel_indentacion == 0:
            raise ErrorGeneracion("No se puede decrementar una indentación en cero.")
        self.nivel_indentacion -= 1

    def _visitar_programa(self, nodo: Programa) -> None:
        """Traduce el programa envolviendo el cuerpo dentro de def main()."""
        self.visitar(nodo.main)
        self.lineas_salida.append("")
        self._agregar_linea('if __name__ == "__main__":')
        self._incrementar_indentacion()
        try:
            self._agregar_linea("main()")
        finally:
            self._decrementar_indentacion()

    def _visitar_main(self, nodo: NodoMain) -> None:
        """Traduce el nodo de función principal obligatorio."""
        self._agregar_linea("def main():")
        self._incrementar_indentacion()
        try:
            if not nodo.sentencias:
                self._agregar_linea("pass")
                return
            for sentencia in nodo.sentencias:
                self.visitar(sentencia)
        finally:
            self._decrementar_indentacion()

    def _visitar_bloque(self, nodo: Bloque) -> None:
        """Traduce un bloque preservando el orden de sus sentencias."""
        if not nodo.sentencias:
            self._agregar_linea("pass")
            return

        for sentencia in nodo.sentencias:
            self.visitar(sentencia)

    def _visitar_asignacion(self, nodo: Asignacion) -> None:
        """Traduce una asignación o declaración."""
        if nodo.valor is None:
            # En Micro C, `int x;` se traduce a inicialización explícita en Python.
            self._agregar_linea(f"{nodo.nombre} = 0")
            return

        valor_traducido: str = self._generar_expresion(nodo.valor)
        self._agregar_linea(f"{nodo.nombre} = {valor_traducido}")

    def _visitar_while(self, nodo: While) -> None:
        """Traduce una sentencia while y controla rigurosamente su indentación."""
        condicion_traducida: str = self._generar_expresion(nodo.condicion)
        self._agregar_linea(f"while {condicion_traducida}:")
        self._incrementar_indentacion()
        try:
            self._visitar_cuerpo_control(nodo.cuerpo)
        finally:
            self._decrementar_indentacion()

    def _visitar_if(self, nodo: If) -> None:
        """Traduce una sentencia if/else y maneja su indentación."""
        condicion_traducida: str = self._generar_expresion(nodo.condicion)
        self._agregar_linea(f"if {condicion_traducida}:")
        self._incrementar_indentacion()
        try:
            self._visitar_cuerpo_control(nodo.cuerpo_si)
        finally:
            self._decrementar_indentacion()

        if nodo.cuerpo_sino is not None:
            self._agregar_linea("else:")
            self._incrementar_indentacion()
            try:
                self._visitar_cuerpo_control(nodo.cuerpo_sino)
            finally:
                self._decrementar_indentacion()

    def _visitar_return(self, nodo: Return) -> None:
        """Traduce una sentencia return."""
        valor_traducido: str = self._generar_expresion(nodo.valor)
        self._agregar_linea(f"return {valor_traducido}")

    def _visitar_operacion_binaria(self, nodo: OperacionBinaria) -> str:
        """Traduce una operación binaria envolviendo en paréntesis para seguridad."""
        izquierda: str = self._generar_expresion(nodo.izquierda)
        derecha: str = self._generar_expresion(nodo.derecha)
        operador_python: str = self._traducir_operador(nodo.operador)
        return f"({izquierda} {operador_python} {derecha})"

    def _visitar_literal_entero(self, nodo: LiteralEntero) -> str:
        """Traduce un literal entero a su representación textual."""
        return str(nodo.valor)

    def _visitar_identificador(self, nodo: Identificador) -> str:
        """Traduce un identificador a su nombre en Python."""
        return nodo.nombre

    def _visitar_cuerpo_control(self, cuerpo: Sentencia) -> None:
        """Traduce el cuerpo de un if/while conservando semántica de bloque."""
        if isinstance(cuerpo, Bloque):
            self._visitar_bloque(cuerpo)
            return

        self.visitar(cuerpo)

    def _generar_expresion(self, expresion: Expresion) -> str:
        """Genera el código Python de una expresión."""
        resultado: str | None = self.visitar(expresion)
        if resultado is None:
            raise ErrorGeneracion("Se esperaba una expresión traducible.")
        return resultado

    def _traducir_operador(self, operador: TipoToken) -> str:
        """Convierte un operador del AST al símbolo equivalente en Python."""
        match operador:
            case TipoToken.MAS:
                return "+"
            case TipoToken.MENOS:
                return "-"
            case TipoToken.MULTIPLICACION:
                return "*"
            case TipoToken.DIVISION:
                return "/"
            case TipoToken.MENOR_QUE:
                return "<"
            case TipoToken.MAYOR_QUE:
                return ">"
            case TipoToken.MENOR_O_IGUAL:
                return "<="
            case TipoToken.MAYOR_O_IGUAL:
                return ">="
            case TipoToken.IGUAL_QUE:
                return "=="
            case TipoToken.DIFERENTE_QUE:
                return "!="
            case _:
                raise ErrorGeneracion(f"Operador no soportado: {operador.value}")
