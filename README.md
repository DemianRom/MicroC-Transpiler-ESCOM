# Transpilador Micro C -> Python

Proyecto final de Compiladores implementado de forma manual en Python 3.10+.
Descripcion breve:
Proyecto educativo que transpila un subconjunto de C (Micro C) a Python y
permite visualizar las 3 fases del proceso (Lexer, Parser y Generator).

Profesor: JOSE SANCHEZ JUAREZ
Grupo: 5cm3
Hecho por los alumnos:
- Demian Romero Bautista
- Daniel Peredo Borgonio
- Luca Alexander Bárcenas Pineda

Este repositorio contiene un transpilador educativo de Micro C a Python con:
- Analisis lexico manual
- Parser recursivo descendente con manejo de precedencia
- Generador de codigo estilo Visitor.
- GUI para visualizar las 3 fases del pipeline.

## Estado del proyecto

El proyecto esta funcional para exposicion y demostracion de pipeline completo:
1. Lexer -> tokens.
2. Parser -> AST.
3. Generator -> Python.

Ademas genera artefactos de salida en disco y permite visualizacion paso a paso en GUI.

## Restricciones de implementacion cumplidas
- No se usa `re`.
- No se usan generadores de parser externos.
- Todo el procesamiento se hace con logica manual en Python.

## Especificacion de Micro C soportada

### Estructura obligatoria
Todo programa debe tener esta forma:

```c
int main() {
    // sentencias
}
```

### Palabras clave
- `int`
- `if`
- `else`
- `while`
- `return`
- `print` (extension educativa agregada)

### Operadores
- Matematicos: `+`, `-`, `*`, `/`
- Relacionales: `<`, `>`, `<=`, `>=`, `==`, `!=`
- Asignacion: `=`

### Simbolos
- `{`, `}`, `(`, `)`, `;`

### Comentarios
- `// comentario de linea` (extension agregada)

## Extensiones agregadas para la demo

Se agregaron 3 mejoras clave para fortalecer la exposicion:

1. `print(...)` en Micro C
- Se reconoce como token reservado.
- Parser soporta `print(expresion);`.
- Generator produce `print(...)` en Python.

2. Comentarios `//`
- Lexer ignora comentarios de linea completos.
- Ya no rompen el parseo ni la transpilacion.

3. Division entera estilo C
- En C con enteros, `a / b` trunca hacia cero.
- El generator transpila division como `int(a / b)` para aproximar ese comportamiento.
- Ejemplo:
  - `5 / 2` -> `2`
  - `-5 / 2` -> `-2`

## Arquitectura modular

### `tokens.py`
- Define `TipoToken` y `Token`.
- Centraliza el vocabulario del lenguaje.
- Desarrollado por: Daniel Peredo Borgonio.

### `lexer.py`
- Recorre el codigo caracter por caracter (`self.pos`, `self.char_actual`).
- Construye tokens y reporta errores con linea/columna.
- Ignora espacios y comentarios `//`.
- Desarrollado por: Daniel Peredo Borgonio.

### `parser.py`
- Consume tokens con `match(tipo_esperado)`.
- Valida `int main() { ... }`.
- Construye AST con `@dataclass`.
- Precedencia implementada:
  1. Unario
  2. Multiplicacion/Division
  3. Suma/Resta
  4. Comparaciones
  5. Igualdad
- Desarrollado por: Demian Romero Bautista.

### `generator.py`
- Recorre AST con `match-case`.
- Controla indentacion de Python (4 espacios por nivel).
- Emite:
  - `def main():`
  - `if __name__ == "__main__": main()`
- Desarrollado por: Luca Alexander Bárcenas Pineda.

### `main.py`
- Orquesta CLI: leer archivo -> lexer -> parser -> generator.
- Guarda salidas en carpeta `output/`.
- Maneja errores amigables.
- Abre GUI automaticamente tras compilacion exitosa.

### `gui_visualizer.py`
- Visualiza animado:
  1. Tokens
  2. AST
  3. Codigo Python generado
- Usa `after()` (no bloqueante), slider de velocidad y auto-scroll.
- Desarrollado en conjunto por:
  - Demian Romero Bautista
  - Daniel Peredo Borgonio
  - Luca Alexander Bárcenas Pineda

## Estructura del proyecto

```text
Proyecto_final/
  tokens.py
  lexer.py
  parser.py
  generator.py
  gui_visualizer.py
  main.py
  README.md
  .gitignore
  ap/
    prueba1.uc
  output/                  # se crea automaticamente
```

## Requisitos
- Python 3.10 o superior

## Ejecucion

### Compilar por CLI (recomendado)
```bash
python main.py ruta/al/archivo.uc
```
o
```bash
python main.py ruta/al/archivo.mc
```

Nota: `-o/--salida` se acepta por compatibilidad, pero la salida se normaliza a `output/salida_<nombre>.py`.

### Abrir solo GUI
```bash
python gui_visualizer.py
```

## Archivos de salida

Para un archivo `programa.uc`, se generan:
- `output/programa.lex`
- `output/programa.ast`
- `output/salida_programa.py`

## Flujo interno
1. Lectura de fuente.
2. Tokenizacion.
3. Parseo y AST.
4. Generacion Python.
5. Escritura de artefactos.
6. (CLI) Apertura de GUI.

## Ejemplo completo

### Entrada Micro C
```c
int main() {
    int a = 10;
    int b = 20;
    int suma = a + b;
    print(suma); // salida educativa
    print(-5 / 2);
    return 0;
}
```

### Salida Python esperada
```python
def main():
    a = 10
    b = 20
    suma = (a + b)
    print(suma)
    print(int(((0 - 5)) / (2)))
    return 0

if __name__ == "__main__":
    main()
```

## Manejo de errores
- Lexico: caracter no reconocido.
- Sintactico: estructura o tokens invalidos.
- Generacion: nodo/operador no soportado.
- E/S: archivo inexistente, permisos o ruta invalida.

Los mensajes se muestran en formato legible para evitar traceback crudo en uso normal.

## Limitaciones conocidas (actuales)
- No hay literales string (ejemplo: `print("hola")` no esta soportado).
- No hay comentarios de bloque `/* ... */`.
- No hay funciones adicionales aparte de `main`.
- No hay chequeo semantico de tipos/variables (solo sintaxis y generacion).

## Valor academico
- Demuestra separacion de responsabilidades por fases.
- Facilita explicacion visual del proceso de compilacion.
- Permite extensiones futuras de manera ordenada.
