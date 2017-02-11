import time
x = time.time()

import datetime
timex = datetime.datetime.fromtimestamp(int(time.time())).strftime('%d.%m.%Y.%H.%M.%S')

import logging
logging.basicConfig(filename='logs/pyGen'+timex+'.log',format= "%(levelname)s;%(filename)s;%(lineno)d;%(asctime)s.%(msecs)03d;%(message)s", datefmt="%H:%M:%S", level=logging.DEBUG)

log_info = logging.info
log_info("run started at {0}".format(timex))

import ast
import data_handling_functions as dhf
import sourceTree
import function_paths
from pprint import pprint
#from test_generator import FuncDef
# from ast_decompiler import decompile

"""
PyGen Test Data.
 Author     :   David Bryan  C00188175@itcarlow.ie
 Supervisor :   Christophe Meudec.

This package is an investigation into the automatic generation of Unit Tests based on source code
evaluation techniques of Symbolic Execution and Constraint logic programming.

This file is the project handler.
It requires setting up a configuration settings section in a gui to handle the followiing
 1. Source File Name
 2. Test folder location
 3. ECLiPSe path location (may be set through the system path ECLIPSEDIR variable either.
 4. Temp directory setting (this package currently uses tempfiles for processing and allows the setting of a location
    for placing these files, if left blank the default directory is chosen as the folder
    that the test files are to be placed in)

"""


def main():
    import platform
    if platform.system() == 'Darwin':
        source_file = '/Users/davidbryan/Google Drive/Year4/006BigProject/Python/ast3/samples/test3.py'
        output_dir = "/Volumes/C/EclipsePTC/solver/"
    else:
        source_directory = "d:/googledrive/Year4/006BigProject/Python/ast3/samples/"
        source_file = dhf.get_source_file(source_directory)
        output_dir = "C:/EclipsePTC/solver/"

    print("file chosen is ", source_file)
    content = dhf.read_source_file(source_file)
    ast_tree_source = ast.parse(content)

    # this creates the data structure object
    ast_object = sourceTree.SourceTree(ast_tree_source)

    # this runs the node extraction process
    ast_object.process_source_code()

    # this creates the complete node list for the source code
    ast_object.construct_node_data_list()

    # now we need to get the global variables and load them into a data structure which handles scope
    print('global variable load')

    # then add the ClassDef and FunctionDef nodes to the structure
    print('Extract Functions and Classes')

    # filter nodevals to extract the indices of Function Definiton Nodes
    list_of_functions = [ node_number[0] for node_number in ast_object.nodevals if node_number[5] == 'FunctionDef']

    # Start FunctionDef analysis
    print('Iterate through Functions')
    function_store = {}
    function_objects_list = []
    # iterate through the list of indices
    for function in list_of_functions:

        # create an object to store this function
        function_object = function_paths.FuncDef(ast_object.nodevals[function][6], output_dir)

        # extract the functions name
        function_name = function_object.head.name
        print('analysing function ',function_name)

        #extract parameters from the function
        function_object.get_variables_from_args()

        # extract returns and decorator_list (these functions are empty currently)
        function_object.get_decorator_list()
        function_object.get_return_list()

        # extract function body to create paths
        function_object.process_function_body()
        print("At this point the function has been analysed to identify the possible paths")
        print("there are 3 important data structures ready for the Symbolic analysis")
        print("1. function_object.conditions_dict")
        pprint(function_object.conditions_dict)
        print("2. function_object.list_of_statements_in_function")
        pprint(function_object.list_of_statements_in_function)
        print("3. function_object.paths")
        pprint(function_object.paths)
        # At this point the function is broken into paths and the paths need to be tested
        #function_object.make_path_dict()

        function_object.symbolically_execute_paths()

        print("path_dict")
        for key,value in function_object.path_dict.items():
            print(key,value)
        function_objects_list.append(function_object)

        function_object.test_path_constraints()

    # take first FunctionDef, send to analyser
    # receive back set of data variables and return evaluation formulae.

    print('next phase')

    # send the dataset into a nose-parameterized structured file for creating
    # dynamic unit tests in a test class that inherits from unittest.Testcase
    print('next phase')
    # run unit tests, test code coverage
    print('next phase')
    #produce analysis
    print('next phase')



if __name__=='__main__':
    main()