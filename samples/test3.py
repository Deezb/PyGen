def evaluate(x, t):
    r = 2 * t
    y = 2 * x
    a = 4 * x
    a = 2 * a + 27
    if x > 5:                   # IF001  Sym0 > 5
        y = y - 3
    else:
        y = y + 4
    if x >= 10 and x <= 20:     # IF002  Sym0 >=10 Sym0 <=20
        x = x + 5.5
    else:
        x = x * 6
    if x > 25 :                 # IF003 TTT 20 >=  Sym0 > 19.5         TTF Sym0<= 19.5     TFT Sym0>4.25      TFF Sym0<=4.25
        if x < 30:              # IF004 TTTT Sym0 < 24.5
            if x == 27:         # IF005
                r = 5 * r
            else:
                r = 3 * r
        else:
            y = y + 1
        y = 2 * x + 7 + r
    else:
        y = 3 * x + 2
    return y + r
