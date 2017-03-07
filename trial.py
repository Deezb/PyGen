import time
import datetime
import logging
import ast
import data_handling_functions as dhf
import sourceTree
import function_paths
import unit_test_maker as utm
from pprint import pprint


text = """
def func1():
    for i in range(3,11,2):
        if i > 5:
            print(i)
"""

def main():
    modNode = ast.parse(text)
    pass



if __name__ == '__main__':
    main()