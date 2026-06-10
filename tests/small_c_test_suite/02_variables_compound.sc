int main() {
    int x = 10;
    int y = 20;
    int z;
    char ch = 'A';

    z = x + y;
    printf("x=%d, y=%d, z=%d\n", x, y, z);
    x += 5;
    y -= 3;
    z *= 2;
    printf("x=%d, y=%d, z=%d\n", x, y, z);
    printf("ch=%c (%d)\n", ch, ch);
    return 0;
}
