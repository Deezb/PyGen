def sect1(x, y):
    a = 3 * y + 5
    b = x - 5
    if a>10:
        while b < a+1:
            #print('a= ', a, ', b= ',b)
            b= b + 1
    else:
        while b < a:
            #print('a= ', a, ', b= ', b)
            b = b + 2
    return b + a * 3