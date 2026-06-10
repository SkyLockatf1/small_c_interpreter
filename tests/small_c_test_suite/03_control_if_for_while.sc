int main() {
    int score = 85;
    int i = 1;
    int sum = 0;

    if (score >= 90) {
        printf("grade=A\n");
    } else if (score >= 80) {
        printf("grade=B\n");
    } else {
        printf("grade=C\n");
    }

    while (i <= 5) {
        sum += i;
        i = i + 1;
    }
    printf("sum=%d\n", sum);

    for (i = 1; i <= 4; i = i + 1) {
        printf("%d:%d\n", i, i * i);
    }
    return 0;
}
