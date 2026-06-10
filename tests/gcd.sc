int gcd(int a, int b) {
    while (b != 0) {
        int temp;
        temp = b;
        b = a % b;
        a = temp;
    }
    return a;
}

int main() {
    int result;
    result = gcd(48, 18);
    printf("GCD(48, 18) = %d\n",result);
    return 0;
}