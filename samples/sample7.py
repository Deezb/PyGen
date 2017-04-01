def design_doc1(par1, par2, par3):
    x = par1 + 5
    if x > par2:
        while(par3 < x):
            par3 = par3 + 1
    else:
        if x > par3:
            par3 = par3 * 2
        else:
            par3 = par3 - par2
    return par3 * par2 + par1 * x
