int fact(int n) {
    if (n <= 1) {
        return 1;
    }
    return n * fact(n - 1);
}

int fib(int n) {
    if (n <= 1) {
        return n;
    }
    return fib(n - 1) + fib(n - 2);
}

int main() {
    printf("fact(6)=%d\n", fact(6));
    printf("fib(8)=%d\n", fib(8));
    return 0;
}
