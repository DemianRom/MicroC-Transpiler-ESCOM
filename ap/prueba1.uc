int main() {
    int n = 5;
    int resultado = 1;
    int contador = 1;

    while (contador <= n) {
        resultado = resultado * contador;
        contador = contador + 1;
    }

    return resultado;
}