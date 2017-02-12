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


"""
    def make_path_dict(self):
        '''
        this function takes the three data structures and creates the code sequences
        :return:
        '''
        # define a named tuple structure for extracting tuple information by name
        a_statement = collections.namedtuple('a_statement', 'typz, lineno, equation ,parent')

        for line_of_code in self.list_of_statements_in_function:
            parent_sect = 'main'
            loc = a_statement(line_of_code[0],line_of_code[1],line_of_code[2],line_of_code[3])
            if loc.typz  == 'Assign':

                # if it is in a named block
                if dhf.iz(loc.parent):
                    parent_sect = loc.parent[-1]

                self.new_dict.setdefault(parent_sect, []).append(loc.equation[0])
            if loc.typz == 'Return':
                if dhf.iz(loc.parent):
                    # this refers to the last element in the list of nested blocks
                    parent_sect = loc.parent[-1]
                self.return_dict.setdefault(parent_sect, []).append(loc.equation[0])



def is_str(st):
    return isinstance(st, str)


def is_int(input_a):
    return isinstance(input_a, int)


def is_float(input_a):
    return isinstance(input_a, float)





import unittest
from unnecessary_math import multiply

class TestUM(unittest.TestCase):

    def setUp(self):
        pass

    def test_numbers_3_4(self):
        self.assertEqual( multiply(3,4), 12)

    def test_strings_a_3(self):
        self.assertEqual( multiply('a',3), 'aaa')

if __name__ == '__main__':
    unittest.main()






 """