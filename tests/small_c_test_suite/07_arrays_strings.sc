int main() {
    int arr[5];
    int i;
    int sum = 0;
    char msg[32];

    for (i = 0; i < 5; i = i + 1) {
        arr[i] = (i + 1) * 10;
        sum = sum + arr[i];
    }

    strcpy(msg, "Small");
    strcat(msg, "-C");
    printf("sum=%d\n", sum);
    printf("msg=%s len=%d\n", msg, strlen(msg));
    return 0;
}
