int main() {
    int arr[3];
    int i = 1;
    int old_arr;
    int new_arr;
    int x = 7;
    int *p;
    int old_ptr;
    int new_ptr;

    arr[0] = 10;
    arr[1] = 20;
    arr[2] = 30;

    old_arr = arr[i]++;
    new_arr = ++arr[i];
    printf("arr old=%d new=%d final=%d\n", old_arr, new_arr, arr[i]);

    p = &x;
    old_ptr = (*p)++;
    new_ptr = ++(*p);
    printf("ptr old=%d new=%d final=%d\n", old_ptr, new_ptr, x);

    return 0;
}
