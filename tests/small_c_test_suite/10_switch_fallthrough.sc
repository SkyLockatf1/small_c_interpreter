int main() {
    int mode = 2;
    int score = 0;

    switch (mode) {
        case 1:
            score = score + 1;
        case 2:
            score = score + 2;
        case 3:
            score = score + 4;
            break;
        default:
            score = score + 8;
    }

    printf("score=%d\n", score);
    return 0;
}
