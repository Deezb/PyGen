def minxy(x, y):
    if x < y:
        return x
    else:
        return y

def factorial(x):
    if x == 0:
        return 1
    else:
        return x * factorial(x-1)
