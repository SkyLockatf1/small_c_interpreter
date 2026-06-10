int main() {
    int i = 0;
    int total = 0;

    do {
        i = i + 1;
        if (i == 3) {
            continue;
        }
        if (i > 6) {
            break;
        }
        total = total + i;
    } while (i < 10);

    printf("i=%d total=%d\n", i, total);
    return 0;
}
