import time
import datetime
import logging
import ast
import sys
import data_handling_functions as dhf
import sourceTree
import function_paths
import unit_test_maker as utm
from pprint import pprint

timex = datetime.datetime.fromtimestamp(int(time.time())).strftime('%d.%m.%Y.%H.%M.%S')

# creates a log file for each run, stores file,line,time,message
logging.basicConfig(filename='../logs/pyGen'+timex+'.log', format="%(levelname)s;%(filename)s;\
%(lineno)d;%(asctime)s.%(msecs)03d;%(message)s", datefmt="%H:%M:%S", level=logging.DEBUG)

# setting an alias for sending data to the log filem, must be string formatted on sending
log_info = logging.info
log_info("run started at {0}".format(timex))

"""
PyGen Test Data.
 Author     :   David Bryan.
 Email      :   C00188175@itcarlow.ie
 Supervisor :   Christophe Meudec.

This package is an investigation into the automatic generation of Unit Tests from source code.
The evaluation techniques of Symbolic Execution and Constraint logic programming are used.

This module is the main program.
It requires setting up a configuration settings section in a gui to handle the following
 1. ECLiPSe program directory - folder that Eclipse is installed, main folder (not /bin)
 2. ECLiPSe pl files directory - for placing temporary Prolog files during the program run.
 3. Test folder location - folder where sample Python files are placed, makes choosing easier

"""


def main():

    # check if 'conf' argument has been included in call
    if len(sys.argv) > 1:
        if sys.argv[1] == 'conf':
            dhf.create_config()

    # load configuration settings
    config = dhf.get_config()

    source_directory = config['SOURCE_DIR']
    eclipse_file_dir = config['ECLIPSE_FILES_DIR']

    source_file = ""

    # get user to select source file.
    try:
        source_file = dhf.get_source_file(source_directory)
    except TypeError:
        print("This process requires the selection of a valid python source code file .py")

    # set folder for saving Prolog files
    output_dir = '/'.join([eclipse_file_dir, 'solver/'])

    print("file chosen is ", source_file)

    # get source code from target source file
    content = dhf.read_source_file(source_file)

    # convert the file contents to an Abstract Syntax Tree
    try:
        ast_tree_source = ast.parse(content)
    except IndentationError as err:
        print("There was a problem with the indentation in that source file")
        print(err.msg, 'on line', err.lineno)
        return 0

    # this creates an ast_object for traversing the tree
    ast_object = sourceTree.SourceTree(ast_tree_source)

    # this runs the node extraction process
    ast_object.process_source_code()

    # this creates the complete node list for the source code 'nodevals'
    ast_object.construct_node_data_list()

    print('Extracting Functions and classes')
    log_info('Extracting Functions and classes')

    # filter nodevals to extract the indices of Function and class Definition Nodes
    list_of_functions = [node_number[0] for node_number in ast_object.nodevals if node_number[5] == 'FunctionDef']
    list_of_classes = [node_number[0] for node_number in ast_object.nodevals if node_number[5] == 'ClassDef']

    log_info('classes = {0}'.format(str(list_of_classes)))

    # Start FunctionDef analysis
    print('Iterate through Functions')

    # list to store all functions
    function_objects_list = []
    # iterate through the list of indices
    for function in list_of_functions:

        # create an object to store this function, this points the function_object at the id
        # which is the memory address of the function node
        function_object = function_paths.FuncDef(ast_object.nodevals[function][6], output_dir)

        # extract the functions name
        function_name = function_object.head.name
        print('analysing function ', function_name)

        # extract parameters from the function
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

        # At this point the function is broken into paths and the paths need to be built and then
        # Symbolically executed to evaluate the return expression
        function_object.build_paths()

        function_object.symbolically_execute_paths()

        print("path_dict")
        for key, value in function_object.path_dict.items():
            print(key, value)

        # this adds the current function object reference to the list of function object references
        function_objects_list.append(function_object)

        # this creates and runs a Prolog file for each path and collects results
        function_object.test_path_constraints()

        # remove non satisfiable paths
        function_object.filter_returned_paths()

        # use return expression and input data set to add tested values to return_dict
        function_object.evaluate_expected_results()

    # send the result structure for extraction to Unit Test Files
    utm.make_unit_tests(source_file, function_objects_list)


if __name__ == '__main__':
    main()
