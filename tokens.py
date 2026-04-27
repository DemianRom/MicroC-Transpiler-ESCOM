"""Proyecto Final de Compiladores - Definiciones de Tokens.

Descripcion breve:
    Este modulo define el vocabulario lexico de Micro C (tipos de token,
    palabras reservadas y estructura Token) para ser consumido por el lexer.

Profesor: JOSE SANCHEZ JUAREZ
Grupo: 5cm3
Hecho por los alumnos:
    - Demian Romero Bautista
    - Daniel Peredo Borgonio
    - Luca Alexander Bárcenas Pineda

Autor de esta pieza:
    - Daniel Peredo Borgonio (tokens)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TipoToken(str, Enum):
    """Enumera todos los tipos de token soportados por Micro C."""

    ENTERO = "ENTERO"
    IDENTIFICADOR = "IDENTIFICADOR"

    PALABRA_INT = "PALABRA_INT"
    PALABRA_IF = "PALABRA_IF"
    PALABRA_ELSE = "PALABRA_ELSE"
    PALABRA_WHILE = "PALABRA_WHILE"
    PALABRA_RETURN = "PALABRA_RETURN"
    PALABRA_PRINT = "PALABRA_PRINT"

    MAS = "MAS"
    MENOS = "MENOS"
    MULTIPLICACION = "MULTIPLICACION"
    DIVISION = "DIVISION"
    MENOR_QUE = "MENOR_QUE"
    MAYOR_QUE = "MAYOR_QUE"
    MENOR_O_IGUAL = "MENOR_O_IGUAL"
    MAYOR_O_IGUAL = "MAYOR_O_IGUAL"
    ASIGNACION = "ASIGNACION"
    IGUAL_QUE = "IGUAL_QUE"
    DIFERENTE_QUE = "DIFERENTE_QUE"

    LLAVE_IZQUIERDA = "LLAVE_IZQUIERDA"
    LLAVE_DERECHA = "LLAVE_DERECHA"
    PARENTESIS_IZQUIERDO = "PARENTESIS_IZQUIERDO"
    PARENTESIS_DERECHO = "PARENTESIS_DERECHO"
    PUNTO_Y_COMA = "PUNTO_Y_COMA"

    FIN_ARCHIVO = "FIN_ARCHIVO"


PALABRAS_RESERVADAS: dict[str, TipoToken] = {
    "int": TipoToken.PALABRA_INT,
    "if": TipoToken.PALABRA_IF,
    "else": TipoToken.PALABRA_ELSE,
    "while": TipoToken.PALABRA_WHILE,
    "return": TipoToken.PALABRA_RETURN,
    "print": TipoToken.PALABRA_PRINT,
}


@dataclass(slots=True, frozen=True)
class Token:
    """Representa un token con metadatos de ubicación."""

    tipo: TipoToken
    lexema: str
    linea: int
    columna: int
