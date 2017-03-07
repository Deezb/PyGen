import os
import data_handling_functions as dhf
from sympy import simplify
def make_unit_tests(filename, dictionary):
    """
    takes in a nested dict containing inputs and equation to evaluate the result

    :param dict: dictionary containing input values which find this path an the symbolic equation for this path
    :return: creates unit test framework
    """
    version = 'a'
    functionnamepaths = [xs.split('xx')[0] for xs in list(dictionary.keys())]
    functions = list(set(functionnamepaths))

    for function in functions:
        fullfilepathlist = filename.split('\\')
        step_up_directory = fullfilepathlist[-2]
        selectedfilename = fullfilepathlist[-1].strip('.py')
        testfilename = ["pygen_unit_tests", "test_" + selectedfilename + ".py"]

        testfilepath =  fullfilepathlist[:-2]
        testfilepath.extend(testfilename[:1])
        if not os.path.exists('\\'.join(testfilepath)):
            os.mkdir('\\'.join(testfilepath))
        testfilepath.extend(testfilename[1:])
        testfile = '\\'.join(testfilepath)
        print('The Unit Test have been written to the file \n\t',testfile)
        with open(testfile, 'w') as fl:
            fl.write('"""pygen created this file automatically from \n{0}"""\n'.format(filename))
            fl.write("import unittest\n")
            fl.write("import os\n")
            fl.write("import sys\n")
            fl.write("filepath  =  os.path.dirname(__file__)\n")
            fl.write("print('filepath = ',filepath)\n")
            #this is a method for loading relative imports in directories higher than the current files dir.
            fl.write("sys.path.append(os.path.join(filepath, '..'))\n")
            #set pythonpath to include the source file location
            fl.write("\n")

            # not filename, need a way to reference the original file
            fl.write("from {0}.{1} import {2}\n".format(step_up_directory, selectedfilename, function))
            fl.write("\n\n")
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
            for test,pieces in dictionary.items():
                test_function_name = test.split('xx')[0]
                test_count += 1
                test_name = "test_{0}_{1}_{2}".format(test_function_name, test_count, version)
                test_flow_path = test
                input_values = pieces[0]
                expected_return = pieces[2][0]
                formula = ''.join(dhf.post_to_in(pieces[1]))
                input_range = list(range(len(input_values)))
                inputs = [str(input_values['Sym'+str(i)]) for i in input_range]
                input_parameters = ', '.join(inputs)
                simpd_form = simplify(formula)
                test_text = '"""This test is using the path {0} \nand is using input values of {1}\nThe expected result is {2} \nbased on the symbolic formula {3}\nWhich simplifies to {4}"""'.format(test_flow_path,
                                                                                       input_values,
                                                                                       expected_return,
                                                                                       formula,
                                                                                       simpd_form
                                                                                       )
                fl.write("  def {0}(self):\n".format(test_name))
                fl.write('      {0}\n'.format(test_text))
                fl.write("      expected_result = {0}\n".format(expected_return))
                fl.write("      test_result = {0}({1})\n".format(function, input_parameters))
                fl.write("      self.assertEqual(expected_result, test_result)\n")
                fl.write("  \n")
            fl.write("if __name__ == '__main__':\n    unittest.main()")

    """if __name__ == '__main__':
        unittest.main(verbosity=2)"""
    print("\nProcessing finished.\n")
