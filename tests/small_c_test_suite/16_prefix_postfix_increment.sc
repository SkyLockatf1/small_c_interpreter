int main() {
    int x = 5;
    int a;
    int b;
    int arr[2];
    int *p;
    int first;
    int second;

    a = ++x;
    b = x++;
    printf("x=%d a=%d b=%d\n", x, a, b);

    arr[0] = 10;
    arr[1] = 20;
    p = &arr[0];
    first = *p++;
    second = *p;
    printf("first=%d second=%d\n", first, second);

    --x;
    printf("x=%d old=%d\n", x, x--);
    printf("x=%d\n", x);
    return 0;
}
