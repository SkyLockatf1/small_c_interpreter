int main() {
    int arr[2];
    int *p;
    arr[0] = 1;
    arr[1] = 2;
    p = &arr[0];
    p = p + 2;
    printf("%d\n", *p);
    return 0;
}
