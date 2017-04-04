import os
import data_handling_functions as dhf
from sympy import simplify


# function_object_list is the list of function object references
def make_unit_tests(filename, function_objects_list):
    """
    takes in a nested dict containing inputs and equation to evaluate the result
    :param filename: the name of the test file to create and fill with unit tests
    :param function_objects_list: the list of function_object references
    :output : writes filename.py and puts all unit tests into it.
    :return: None
    """
    version = 'a'

    dictionary = {}

    # adds all the function dictionaries together as one dictionary
    for item in function_objects_list:
        dictionary.update(item.return_dict)

    # get the name of function for each unit test, has repeated elements
    functionnamepaths = [xs.split('xx')[0] for xs in list(dictionary.keys())]

    # extract uniques names of the functions
    functions = list(set(functionnamepaths))

    # string the functionnames together (used for an import statement)
    function_names = ', '.join(functions)

    # get the parent directory name (just the directory name)
    fullfilepathlist = filename.split('\\')
    step_up_directory = fullfilepathlist[-2]

    # get the filename and remove the .py extension
    selectedfilename = fullfilepathlist[-1][:-3]

    # create the test file name
    testfilename = ["pygen_unit_tests", "test_" + selectedfilename + ".py"]

    # this is the file path as a list of nested directories
    testfilepath = fullfilepathlist[:-2]

    # add the new folder
    testfilepath.extend(testfilename[:1])

    # check if folder exists, create it if not
    if not os.path.exists('\\'.join(testfilepath)):
        os.mkdir('\\'.join(testfilepath))

    # add the filename to the path
    testfilepath.extend(testfilename[1:])

    # turn the list into a string
    testfile = '\\'.join(testfilepath)

    print('The Unit Test have been written to the file \n\t', testfile)
    with open(testfile, 'w') as fl:
        fl.write('"""pygen created this file automatically from \n{0}"""\n'.format(filename))
        fl.write("import unittest\n")
        fl.write("import os\n")
        fl.write("import sys\n")
        # this line finds the current files directory
        fl.write("filepath  =  os.path.dirname(__file__)\n")

        fl.write("print('filepath = ',filepath)\n")
        # this is a method for loading relative imports in directories higher than the current files directory.
        # set pythonpath to include the source file location
        fl.write("sys.path.append(os.path.join(filepath, '..'))\n")
        fl.write("\n")

        # reference to the original selected file, import the function names
        fl.write("from {0}.{1} import {2}\n".format(step_up_directory, selectedfilename, function_names))
        fl.write("\n\n")

        # create a new class tht inherits unittest.TestCase
        fl.write("class Test{0}(unittest.TestCase):".format(selectedfilename))
        fl.write("  \n  \n")
        fl.write("  def setUp(self):\n")
        fl.write("      pass\n")
        fl.write("  \n")
        fl.write("  \n")
        fl.write("  def tearDown(self):\n")
        fl.write("      pass\n")
        fl.write("  \n")
        fl.write("  \n")

        test_count = 0

        # iterate test sets to write each unit test
        for test, pieces in dictionary.items():
            test_function_name = test.split('xx')[0]
            test_count += 1

            # make the tests name
            test_name = "test_{0}_{1}_{2}".format(test_function_name, test_count, version)

            # name of path
            test_flow_path = test

            # values of symbolic variables
            input_values = pieces[0]


            tested_result = pieces[2][0]
            formula = ''.join(dhf.post_to_in(pieces[1]))

            # count of symbolic variables to set up loops
            input_range = list(range(len(input_values)))

            # this puts the input set together as a string, to pass as an argument to the function
            inputs = [str(input_values['Sym'+str(i)]) for i in input_range]
            input_parameters = ', '.join(inputs)

            # creates a simplified expression of the return formula
            simpd_form = simplify(formula)

            # put the test together and add it to the file
            test_text = '"""This test is using the path {0} \nand is using input values of {1} \
            \nThe expected result is {2} \nbased on the symbolic formula {3}\nWhich simplifies \
            to {4}"""'.format(test_flow_path,
                              input_values,
                              tested_result,
                              formula,
                              simpd_form)
            fl.write("  def {0}(self):\n".format(test_name))
            fl.write('      {0}\n'.format(test_text))
            fl.write("      tested_result = {0}\n".format(tested_result))
            fl.write("      returned_result = {0}({1})\n".format(test_function_name, input_parameters))
            fl.write("      self.assertEqual(tested_result, returned_result)\n")
            fl.write("  \n")
        fl.write("if __name__ == '__main__':\n    unittest.main()")

    print("\nProcessing finished.\n")
