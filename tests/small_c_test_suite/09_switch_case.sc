int classify(int code) {
    switch (code) {
        case 1:
            return 10;
        case 2:
        case 3:
            return 20;
        default:
            return 99;
    }
}

int main() {
    printf("c1=%d\n", classify(1));
    printf("c2=%d\n", classify(2));
    printf("c3=%d\n", classify(3));
    printf("c9=%d\n", classify(9));
    return 0;
}
