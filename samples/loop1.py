def evaluate(x, t):
    r = 2 * t
    y = 2 * x
    a = 4 * x
    a = 2 * a + 27
    while(x<17):
        y = y + 1
        x = x + 1
    else:
        x =5
    if x > 5:
        y = y - 3
    else:
        y = y + 4 * a
    if x >= 10 and x <= 20:
        x = x + 5.5
    else:
        x = x * 6
    if x > 25 :
        if x < 30:
            if x == 27:
                r = 5 * r
            else:
                r = 3 * r
        else:
            y = y + 1
        y = 2 * x + 7 + r
    else:
        y = 3 * x + 2
    return y + r


def main():
    print(evaluate(1, 5))
    print(evaluate(2, 5))
    print(evaluate(4.5, 5))
    print(evaluate(4.75, 5))
    print(evaluate(5, 5))
    print(evaluate(6, 5))
    print(evaluate(17, 5))
    print(evaluate(19,5))
    print(evaluate(20, 5))
    print(evaluate(21, 5))
    print(evaluate(31, 5))

if __name__=='__main__':
    main()

