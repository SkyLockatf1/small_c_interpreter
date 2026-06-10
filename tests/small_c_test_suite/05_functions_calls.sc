int square(int x) {
    return x * x;
}

int add3(int a, int b, int c) {
    return a + b + c;
}

void print_pair(int a, int b) {
    printf("pair=%d,%d\n", a, b);
}

int main() {
    int a = square(6);
    int b = add3(1, 2, 3);
    print_pair(a, b);
    printf("result=%d\n", a + b);
    return 0;
}
