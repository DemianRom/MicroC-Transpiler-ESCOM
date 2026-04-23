# Transpilador Micro C -> Python (Proyecto Final Compiladores)

Proyecto academico desarrollado de forma artesanal en Python 3.10+ para transcompilar un subconjunto de C ("Micro C") hacia Python.

El proyecto incluye:
- Pipeline completo de compilacion: Lexer -> Parser -> Generator.
- Interfaz GUI educativa para visualizar las 3 fases paso a paso.
- Generacion automatica de artefactos `.lex`, `.ast` y `.py`.

## Integrantes
- Demian
- Daniel
- Luca

## Objetivo
Implementar un compilador/transpilador modular, claro y didactico, sin dependencias externas de analisis lexico/sintactico.

## Restricciones de implementacion
- No se usa `re`.
- No se usan generadores de parser (PLY, Lark, ANTLR, etc.).
- Todo el analisis lexico y sintactico se implementa manualmente.

## Especificacion de Micro C soportada

### Estructura obligatoria del programa
Todo programa debe estar envuelto en la funcion principal:

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

### Operadores matematicos
- `+`
- `-`
- `*`
- `/`

### Operadores relacionales / igualdad
- `<`
- `>`
- `<=`
- `>=`
- `==`
- `!=`

### Asignacion
- `=`

### Simbolos
- `{`
- `}`
- `(`
- `)`
- `;`

## Arquitectura del proyecto

### 1) `tokens.py`
Define:
- `TipoToken` (enum de tokens del lenguaje)
- `Token` (dataclass con `tipo`, `lexema`, `linea`, `columna`)

### 2) `lexer.py` (Analizador lexico manual)
Responsabilidades:
- Recorrer el texto caracter por caracter (`self.pos`, `self.char_actual`).
- Identificar tokens de palabras clave, identificadores, numeros, operadores y simbolos.
- Reportar errores lexicos con linea y columna.

Salida:
- Lista secuencial de `Token`.

### 3) `parser.py` (Recursivo descendente + AST)
Responsabilidades:
- Consumir la lista de tokens con `match(tipo_esperado)`.
- Validar la estructura obligatoria `int main() { ... }`.
- Construir AST con `@dataclass`.

Nodos principales:
- `Programa`
- `NodoMain`
- `Bloque`
- `Asignacion`
- `While`
- `If`
- `Return`
- `OperacionBinaria`
- `LiteralEntero`
- `Identificador`

Precedencia implementada:
1. Unario (`-x`)
2. Multiplicacion/Division (`*`, `/`)
3. Suma/Resta (`+`, `-`)
4. Comparaciones (`<`, `>`, `<=`, `>=`)
5. Igualdad (`==`, `!=`)

### 4) `generator.py` (Back-end Python, estilo Visitor)
Responsabilidades:
- Recorrer AST con `match-case`.
- Traducir sentencias/expresiones a Python.
- Controlar rigurosamente la indentacion (4 espacios por nivel).

Salida Python:
- Funcion `def main():`
- Bloque final:

```python
if __name__ == "__main__":
    main()
```

### 5) `main.py` (Orquestador CLI)
Responsabilidades:
- Leer archivo de entrada (`.uc` o `.mc`).
- Ejecutar pipeline Lexer -> Parser -> Generator.
- Guardar salidas en carpeta `output/`.
- Manejar errores de forma amigable.
- Abrir la GUI educativa al finalizar compilacion exitosa.

### 6) `gui_visualizer.py` (Visualizador educativo)
Muestra de forma animada:
1. Fase Lexer: tokens uno por uno.
2. Fase Parser: arbol AST linea por linea.
3. Fase Generator: codigo Python generado linea por linea.

Caracteristicas:
- Animacion no bloqueante con `after()`.
- Slider de velocidad.
- Auto-scroll en los paneles (`see(tk.END)`).
- Compilacion en background para no congelar la UI.

## Estructura de carpetas (esperada)

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
  output/                # se crea automaticamente
```

## Requisitos
- Python 3.10 o superior.

### Opcion 1: Compilar desde CLI (recomendado)

```bash
python main.py ruta/al/archivo.uc
```

o

```bash
python main.py ruta/al/archivo.mc
```

Tambien puedes pasar `-o`, pero por diseno se normaliza a carpeta `output/`:

```bash
python main.py ruta/al/archivo.uc -o salida.py
```

### Opcion 2: Abrir solo visualizador GUI

```bash
python gui_visualizer.py
```

## Archivos de salida generados

Siempre en carpeta `output/` (si no existe, se crea):

Para entrada `programa.uc`:
- `output/programa.lex`   -> tokens
- `output/programa.ast`   -> AST formateado
- `output/salida_programa.py` -> codigo Python final

## Flujo interno de compilacion
1. Lectura de archivo fuente.
2. Tokenizacion con `Lexer`.
3. Parsing y construccion de AST con `Parser`.
4. Generacion de Python con `GeneradorPython`.
5. Escritura de artefactos a `output/`.
6. (CLI) Apertura de GUI para visualizacion educativa.

## Manejo de errores
- Error lexico: caracter invalido, token no reconocido.
- Error sintactico: estructura incorrecta o tokens fuera de regla.
- Error de generacion: nodo/operador AST no soportado.
- Error de E/S: ruta invalida, permisos, archivo inexistente.

Todos los errores se reportan con mensajes legibles, evitando traceback crudo en uso normal.

## Ejemplo minimo valido en Micro C

```c
int main() {
    int x = 0;
    while (x < 3) {
        x = x + 1;
    }
    return x;
}
```

## Valor academico del proyecto
- Demuestra separacion de responsabilidades por fases de compilacion.
- Permite depuracion visual y explicacion pedagogica en exposicion.
- Facilita extension futura del lenguaje (nuevos tokens/reglas/nodos).
