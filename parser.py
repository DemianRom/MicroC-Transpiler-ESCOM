"""Analizador sintáctico recursivo descendente para Micro C."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from tokens import TipoToken, Token


@dataclass(slots=True)
class Programa:
    """Nodo raíz del AST que representa un programa completo."""

    main: "NodoMain"


@dataclass(slots=True)
class NodoMain:
    """Representa el cuerpo de la función principal obligatoria main."""

    sentencias: list["Sentencia"]


@dataclass(slots=True)
class Bloque:
    """Representa un bloque delimitado por llaves."""

    sentencias: list["Sentencia"]


@dataclass(slots=True)
class Asignacion:
    """Representa una asignación o una declaración de variable entera."""

    nombre: str
    valor: "Expresion | None"
    es_declaracion: bool


@dataclass(slots=True)
class While:
    """Representa una sentencia while con condición y cuerpo."""

    condicion: "Expresion"
    cuerpo: "Sentencia"


@dataclass(slots=True)
class If:
    """Representa una sentencia if con rama else opcional."""

    condicion: "Expresion"
    cuerpo_si: "Sentencia"
    cuerpo_sino: "Sentencia | None"


@dataclass(slots=True)
class Return:
    """Representa una sentencia return."""

    valor: "Expresion"


@dataclass(slots=True)
class OperacionBinaria:
    """Representa una operación binaria entre dos expresiones."""

    izquierda: "Expresion"
    operador: TipoToken
    derecha: "Expresion"


@dataclass(slots=True)
class LiteralEntero:
    """Representa un literal entero dentro de una expresión."""

    valor: int


@dataclass(slots=True)
class Identificador:
    """Representa una referencia a identificador."""

    nombre: str


Expresion: TypeAlias = OperacionBinaria | LiteralEntero | Identificador
Sentencia: TypeAlias = Asignacion | While | If | Return | Bloque


class ErrorSintactico(Exception):
    """Error lanzado cuando la secuencia de tokens no cumple la gramática."""

    def __init__(self, mensaje: str, token: Token) -> None:
        """Construye un error sintáctico con contexto del token actual."""
        descripcion: str = (
            f"Error sintáctico en línea {token.linea}, columna {token.columna}: "
            f"{mensaje}. Token actual: {token.tipo.value} ('{token.lexema}')"
        )
        super().__init__(descripcion)
        self.token: Token = token


class Parser:
    """Implementa un parser recursivo descendente para el lenguaje Micro C."""

    def __init__(self, tokens: list[Token]) -> None:
        """Inicializa el parser con la lista de tokens producida por el lexer."""
        if not tokens:
            raise ValueError("La lista de tokens no puede estar vacía.")

        self.tokens: list[Token] = tokens
        self.pos: int = 0
        self.token_actual: Token = tokens[0]

    def avanzar(self) -> None:
        """Avanza al siguiente token de la secuencia."""
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
            self.token_actual = self.tokens[self.pos]

    def match(self, tipo_esperado: TipoToken) -> Token:
        """Consume el token actual si coincide con el tipo esperado."""
        if self.token_actual.tipo != tipo_esperado:
            raise ErrorSintactico(
                f"Se esperaba {tipo_esperado.value} y se encontró {self.token_actual.tipo.value}",
                self.token_actual,
            )

        token_consumido: Token = self.token_actual
        self.avanzar()
        return token_consumido

    def parsear(self) -> Programa:
        """Punto de entrada del análisis sintáctico."""
        return self.parsear_programa()

    def parsear_programa(self) -> Programa:
        """Regla: programa -> 'int' 'main' '(' ')' '{' sentencia* '}' FIN_ARCHIVO."""
        self.match(TipoToken.PALABRA_INT)
        token_nombre_main: Token = self.match(TipoToken.IDENTIFICADOR)
        if token_nombre_main.lexema != "main":
            raise ErrorSintactico(
                "Se esperaba el identificador 'main' para la función principal",
                token_nombre_main,
            )

        self.match(TipoToken.PARENTESIS_IZQUIERDO)
        self.match(TipoToken.PARENTESIS_DERECHO)
        self.match(TipoToken.LLAVE_IZQUIERDA)

        sentencias: list[Sentencia] = []

        while self.token_actual.tipo not in {
            TipoToken.LLAVE_DERECHA,
            TipoToken.FIN_ARCHIVO,
        }:
            sentencias.append(self.parsear_sentencia())

        self.match(TipoToken.LLAVE_DERECHA)
        self.match(TipoToken.FIN_ARCHIVO)
        return Programa(main=NodoMain(sentencias=sentencias))

    def parsear_sentencia(self) -> Sentencia:
        """Regla principal de sentencias del lenguaje."""
        tipo_actual: TipoToken = self.token_actual.tipo

        match tipo_actual:
            case TipoToken.PALABRA_INT:
                return self.parsear_declaracion()
            case TipoToken.IDENTIFICADOR:
                return self.parsear_asignacion()
            case TipoToken.PALABRA_WHILE:
                return self.parsear_mientras()
            case TipoToken.PALABRA_IF:
                return self.parsear_si()
            case TipoToken.PALABRA_RETURN:
                return self.parsear_retorno()
            case TipoToken.LLAVE_IZQUIERDA:
                return self.parsear_bloque()
            case _:
                raise ErrorSintactico("Sentencia no válida", self.token_actual)

    def parsear_bloque(self) -> Bloque:
        """Regla: bloque -> '{' sentencia* '}'."""
        self.match(TipoToken.LLAVE_IZQUIERDA)
        sentencias: list[Sentencia] = []

        while self.token_actual.tipo not in {
            TipoToken.LLAVE_DERECHA,
            TipoToken.FIN_ARCHIVO,
        }:
            sentencias.append(self.parsear_sentencia())

        self.match(TipoToken.LLAVE_DERECHA)
        return Bloque(sentencias=sentencias)

    def parsear_declaracion(self) -> Asignacion:
        """Regla: declaracion -> 'int' IDENTIFICADOR ('=' expresion)? ';'."""
        self.match(TipoToken.PALABRA_INT)
        token_identificador: Token = self.match(TipoToken.IDENTIFICADOR)

        valor: Expresion | None = None
        if self.token_actual.tipo == TipoToken.ASIGNACION:
            self.match(TipoToken.ASIGNACION)
            valor = self.parsear_expresion()

        self.match(TipoToken.PUNTO_Y_COMA)
        return Asignacion(
            nombre=token_identificador.lexema,
            valor=valor,
            es_declaracion=True,
        )

    def parsear_asignacion(self) -> Asignacion:
        """Regla: asignacion -> IDENTIFICADOR '=' expresion ';'."""
        token_identificador: Token = self.match(TipoToken.IDENTIFICADOR)
        self.match(TipoToken.ASIGNACION)
        valor: Expresion = self.parsear_expresion()
        self.match(TipoToken.PUNTO_Y_COMA)

        return Asignacion(
            nombre=token_identificador.lexema,
            valor=valor,
            es_declaracion=False,
        )

    def parsear_mientras(self) -> While:
        """Regla: while -> 'while' '(' expresion ')' sentencia."""
        self.match(TipoToken.PALABRA_WHILE)
        self.match(TipoToken.PARENTESIS_IZQUIERDO)
        condicion: Expresion = self.parsear_expresion()
        self.match(TipoToken.PARENTESIS_DERECHO)
        cuerpo: Sentencia = self.parsear_sentencia()
        return While(condicion=condicion, cuerpo=cuerpo)

    def parsear_si(self) -> If:
        """Regla: if -> 'if' '(' expresion ')' sentencia ('else' sentencia)?."""
        self.match(TipoToken.PALABRA_IF)
        self.match(TipoToken.PARENTESIS_IZQUIERDO)
        condicion: Expresion = self.parsear_expresion()
        self.match(TipoToken.PARENTESIS_DERECHO)

        cuerpo_si: Sentencia = self.parsear_sentencia()
        cuerpo_sino: Sentencia | None = None
        if self.token_actual.tipo == TipoToken.PALABRA_ELSE:
            self.match(TipoToken.PALABRA_ELSE)
            cuerpo_sino = self.parsear_sentencia()

        return If(condicion=condicion, cuerpo_si=cuerpo_si, cuerpo_sino=cuerpo_sino)

    def parsear_retorno(self) -> Return:
        """Regla: return -> 'return' expresion ';'."""
        self.match(TipoToken.PALABRA_RETURN)
        valor: Expresion = self.parsear_expresion()
        self.match(TipoToken.PUNTO_Y_COMA)
        return Return(valor=valor)

    def parsear_expresion(self) -> Expresion:
        """Regla inicial de expresiones con menor precedencia."""
        return self.parsear_igualdad()

    def parsear_igualdad(self) -> Expresion:
        """Regla: igualdad -> comparacion (('==' | '!=') comparacion)*."""
        expresion: Expresion = self.parsear_comparacion()

        while self.token_actual.tipo in {TipoToken.IGUAL_QUE, TipoToken.DIFERENTE_QUE}:
            operador: TipoToken = self.token_actual.tipo
            self.match(operador)
            derecha: Expresion = self.parsear_comparacion()
            expresion = OperacionBinaria(
                izquierda=expresion,
                operador=operador,
                derecha=derecha,
            )

        return expresion

    def parsear_comparacion(self) -> Expresion:
        """Regla: comparacion -> termino (('<' | '>' | '<=' | '>=') termino)*."""
        expresion: Expresion = self.parsear_termino()

        while self.token_actual.tipo in {
            TipoToken.MENOR_QUE,
            TipoToken.MAYOR_QUE,
            TipoToken.MENOR_O_IGUAL,
            TipoToken.MAYOR_O_IGUAL,
        }:
            operador: TipoToken = self.token_actual.tipo
            self.match(operador)
            derecha: Expresion = self.parsear_termino()
            expresion = OperacionBinaria(
                izquierda=expresion,
                operador=operador,
                derecha=derecha,
            )

        return expresion

    def parsear_termino(self) -> Expresion:
        """Regla: termino -> factor (('+' | '-') factor)*."""
        expresion: Expresion = self.parsear_factor()

        while self.token_actual.tipo in {TipoToken.MAS, TipoToken.MENOS}:
            operador: TipoToken = self.token_actual.tipo
            self.match(operador)
            derecha: Expresion = self.parsear_factor()
            expresion = OperacionBinaria(
                izquierda=expresion,
                operador=operador,
                derecha=derecha,
            )

        return expresion

    def parsear_factor(self) -> Expresion:
        """Regla: factor -> unario (('*' | '/') unario)*."""
        expresion: Expresion = self.parsear_unario()

        while self.token_actual.tipo in {TipoToken.MULTIPLICACION, TipoToken.DIVISION}:
            operador: TipoToken = self.token_actual.tipo
            self.match(operador)
            derecha: Expresion = self.parsear_unario()
            expresion = OperacionBinaria(
                izquierda=expresion,
                operador=operador,
                derecha=derecha,
            )

        return expresion

    def parsear_unario(self) -> Expresion:
        """Regla: unario -> '-' unario | primario."""
        if self.token_actual.tipo == TipoToken.MENOS:
            operador: TipoToken = self.match(TipoToken.MENOS).tipo
            derecha: Expresion = self.parsear_unario()
            return OperacionBinaria(
                izquierda=LiteralEntero(0),
                operador=operador,
                derecha=derecha,
            )

        return self.parsear_primario()

    def parsear_primario(self) -> Expresion:
        """Regla: primario -> ENTERO | IDENTIFICADOR | '(' expresion ')'."""
        tipo_actual: TipoToken = self.token_actual.tipo

        match tipo_actual:
            case TipoToken.ENTERO:
                token_entero: Token = self.match(TipoToken.ENTERO)
                return LiteralEntero(valor=int(token_entero.lexema))
            case TipoToken.IDENTIFICADOR:
                token_identificador: Token = self.match(TipoToken.IDENTIFICADOR)
                return Identificador(nombre=token_identificador.lexema)
            case TipoToken.PARENTESIS_IZQUIERDO:
                self.match(TipoToken.PARENTESIS_IZQUIERDO)
                expresion: Expresion = self.parsear_expresion()
                self.match(TipoToken.PARENTESIS_DERECHO)
                return expresion
            case _:
                raise ErrorSintactico("Se esperaba una expresión primaria", self.token_actual)
