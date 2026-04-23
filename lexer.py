"""Analizador léxico manual para Micro C sin expresiones regulares."""

from __future__ import annotations

from typing import Final

from tokens import PALABRAS_RESERVADAS, TipoToken, Token


class ErrorLexico(Exception):
    """Error lanzado cuando se encuentra un carácter inválido en la entrada."""

    def __init__(self, mensaje: str, linea: int, columna: int) -> None:
        """Construye un error léxico con contexto de ubicación."""
        super().__init__(f"Error léxico en línea {linea}, columna {columna}: {mensaje}")
        self.linea: int = linea
        self.columna: int = columna


class Lexer:
    """Implementa un autómata finito manual para tokenizar código Micro C."""

    _CARACTER_NULO: Final[str] = "\0"

    def __init__(self, codigo_fuente: str) -> None:
        """Inicializa el lexer con el código fuente de entrada."""
        self.codigo_fuente: str = codigo_fuente
        self.pos: int = 0
        self.linea: int = 1
        self.columna: int = 1
        self.char_actual: str = (
            codigo_fuente[0] if len(codigo_fuente) > 0 else self._CARACTER_NULO
        )

    def avanzar(self) -> None:
        """Avanza una posición en el flujo de entrada y actualiza ubicación."""
        if self.char_actual == "\n":
            self.linea += 1
            self.columna = 1
        else:
            self.columna += 1

        self.pos += 1
        if self.pos >= len(self.codigo_fuente):
            self.char_actual = self._CARACTER_NULO
            return

        self.char_actual = self.codigo_fuente[self.pos]

    def mirar_siguiente(self) -> str:
        """Retorna el siguiente carácter sin consumirlo."""
        siguiente_pos: int = self.pos + 1
        if siguiente_pos >= len(self.codigo_fuente):
            return self._CARACTER_NULO
        return self.codigo_fuente[siguiente_pos]

    def saltar_espacios(self) -> None:
        """Consume espacios, tabulaciones y saltos de línea."""
        while self.char_actual in {" ", "\t", "\r", "\n"}:
            self.avanzar()

    def procesar_numero(self) -> Token:
        """Consume un literal entero y retorna su token correspondiente."""
        columna_inicial: int = self.columna
        digitos: list[str] = []

        while self.char_actual.isdigit():
            digitos.append(self.char_actual)
            self.avanzar()

        lexema: str = "".join(digitos)
        return Token(
            tipo=TipoToken.ENTERO,
            lexema=lexema,
            linea=self.linea,
            columna=columna_inicial,
        )

    def procesar_identificador_o_palabra_clave(self) -> Token:
        """Consume un identificador o palabra reservada y retorna su token."""
        columna_inicial: int = self.columna
        caracteres: list[str] = []

        while self.char_actual.isalpha() or self.char_actual.isdigit() or self.char_actual == "_":
            caracteres.append(self.char_actual)
            self.avanzar()

        lexema: str = "".join(caracteres)
        tipo: TipoToken = PALABRAS_RESERVADAS.get(lexema, TipoToken.IDENTIFICADOR)
        return Token(tipo=tipo, lexema=lexema, linea=self.linea, columna=columna_inicial)

    def procesar_simbolo_o_operador(self) -> Token:
        """Procesa símbolos y operadores usando clasificación con match-case."""
        columna_inicial: int = self.columna
        linea_inicial: int = self.linea
        char: str = self.char_actual

        match char:
            case "+":
                self.avanzar()
                return Token(TipoToken.MAS, "+", linea_inicial, columna_inicial)
            case "-":
                self.avanzar()
                return Token(TipoToken.MENOS, "-", linea_inicial, columna_inicial)
            case "*":
                self.avanzar()
                return Token(TipoToken.MULTIPLICACION, "*", linea_inicial, columna_inicial)
            case "/":
                self.avanzar()
                return Token(TipoToken.DIVISION, "/", linea_inicial, columna_inicial)
            case "<":
                if self.mirar_siguiente() == "=":
                    self.avanzar()
                    self.avanzar()
                    return Token(TipoToken.MENOR_O_IGUAL, "<=", linea_inicial, columna_inicial)
                self.avanzar()
                return Token(TipoToken.MENOR_QUE, "<", linea_inicial, columna_inicial)
            case ">":
                if self.mirar_siguiente() == "=":
                    self.avanzar()
                    self.avanzar()
                    return Token(TipoToken.MAYOR_O_IGUAL, ">=", linea_inicial, columna_inicial)
                self.avanzar()
                return Token(TipoToken.MAYOR_QUE, ">", linea_inicial, columna_inicial)
            case "{":
                self.avanzar()
                return Token(TipoToken.LLAVE_IZQUIERDA, "{", linea_inicial, columna_inicial)
            case "}":
                self.avanzar()
                return Token(TipoToken.LLAVE_DERECHA, "}", linea_inicial, columna_inicial)
            case "(":
                self.avanzar()
                return Token(
                    TipoToken.PARENTESIS_IZQUIERDO, "(", linea_inicial, columna_inicial
                )
            case ")":
                self.avanzar()
                return Token(
                    TipoToken.PARENTESIS_DERECHO, ")", linea_inicial, columna_inicial
                )
            case ";":
                self.avanzar()
                return Token(TipoToken.PUNTO_Y_COMA, ";", linea_inicial, columna_inicial)
            case "=":
                if self.mirar_siguiente() == "=":
                    self.avanzar()
                    self.avanzar()
                    return Token(TipoToken.IGUAL_QUE, "==", linea_inicial, columna_inicial)

                self.avanzar()
                return Token(TipoToken.ASIGNACION, "=", linea_inicial, columna_inicial)
            case "!":
                if self.mirar_siguiente() == "=":
                    self.avanzar()
                    self.avanzar()
                    return Token(TipoToken.DIFERENTE_QUE, "!=", linea_inicial, columna_inicial)
                raise ErrorLexico(
                    f"Carácter no reconocido: '{char}'",
                    linea=linea_inicial,
                    columna=columna_inicial,
                )
            case _:
                raise ErrorLexico(
                    f"Carácter no reconocido: '{char}'",
                    linea=linea_inicial,
                    columna=columna_inicial,
                )

    def obtener_siguiente_token(self) -> Token:
        """Retorna el siguiente token válido en el flujo de entrada."""
        while self.char_actual != self._CARACTER_NULO:
            if self.char_actual in {" ", "\t", "\r", "\n"}:
                self.saltar_espacios()
                continue

            if self.char_actual.isdigit():
                return self.procesar_numero()

            if self.char_actual.isalpha() or self.char_actual == "_":
                return self.procesar_identificador_o_palabra_clave()

            return self.procesar_simbolo_o_operador()

        return Token(
            tipo=TipoToken.FIN_ARCHIVO,
            lexema="",
            linea=self.linea,
            columna=self.columna,
        )

    def tokenizar(self) -> list[Token]:
        """Tokeniza toda la entrada y devuelve la lista completa de tokens."""
        tokens: list[Token] = []
        while True:
            token: Token = self.obtener_siguiente_token()
            tokens.append(token)
            if token.tipo == TipoToken.FIN_ARCHIVO:
                break
        return tokens
