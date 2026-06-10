void swap(int *a, int *b) {
    int temp;
    temp = *a;
    *a = *b;
    *b = temp;
}

int main() {
    int x = 11;
    int y = 22;
    int *p;

    p = &x;
    printf("*p=%d\n", *p);
    *p = 33;
    swap(&x, &y);
    printf("x=%d y=%d\n", x, y);
    return 0;
}
