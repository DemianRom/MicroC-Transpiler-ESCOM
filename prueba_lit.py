def main():
    maximo = 100
    actual = 0
    while (actual < maximo):
        if (actual == 50):
            actual = (actual + 10)
        else:
            actual = (actual + 1)
    return actual

if __name__ == "__main__":
    main()
