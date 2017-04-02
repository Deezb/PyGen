import data_handling_functions as dhf
import ast
from ast_decompiler import decompile
import collections
from collections import Counter
from subprocess import Popen, PIPE
from itertools import chain
from sympy import simplify

import logging
log_info = logging.info
"""This file is given the head node of a function and
returns a set of test data sets and results"""
LOOP_LIST = [0,1,5]

# define the rational bounds for the Prolog search, in the format 'low_value , high_value'
RANGE_BOUNDS = '-100.0, 300.0'


def get_variable_name(section):
    variable_names = []
    for target in section.targets:

        # for single entries
        if hasattr(target, 'id'):
            return [target.id]
        # for multiple entries
        for elt in target.elts:
            # each elt represents a separate variable name
            if str(elt.ctx).startswith("<_ast.Store object at"):
                variable_names.append(elt.id)
            elif str(elt.ctx).startswith("<_ast.Load object at"):
                log_info("Load in vars, not allowed")
    return variable_names


# get assignment values from tree node
# this function extracts the list of variable values from a tree node
def get_variable_value(section):
    variable_value_list = []

    # check for Binop
    if hasattr(section.value, 'left'):
        return [decompile(section.value)]

    # check for string
    if hasattr(section.value, 's'):
        return [section.value.s]

    # check for single value
    if hasattr(section.value, 'n'):
        return [section.value.n]

    if isinstance(section.value.elts, list):
        for value in section.value.elts:
            variable_value_list.append(value.n)
    return variable_value_list


class FuncDef(object):
    def __init__(self, node, output_dir):
        self.head = node
        self.variables = []
        self.output_dir = output_dir
        self.symbolic_variables = {}
        self.constraint_list = []
        self.paths = [['list_identity']]
        self.conditional_count = 0
        self.while_count = 0
        self.list_of_statements_in_function = []
        self.conditions_dict = {}
        self.linecount = 0
        self.symbol_count = 0
        self.variable_count = 0
        self.active_code_block = ['list_identity']
        self.new_dict = {}
        self.path_dict = {}
        self.return_dict = {}
        self.path_codes_list = {}


    """This function takes the function paramaters and sets up Symbolic variables and variables for them"""
    def get_variables_from_args(self):
        arg_list = dhf.PLD['arguments']  # 3.5.2 => ['args', 'vararg', 'kwonlyargs', 'kw_defaults', 'kwarg', 'defaults']
        for argument in arg_list:
            fetch = eval('self.head.args.{0}'.format(argument))
            if dhf.iz(fetch):
                # that means it contains something, else is empty set or empty list or none
                if isinstance(fetch, list):
                    # if fetch is a list then add each one to the variables and generate a symbol for each
                    # it may become necessary to extract the linenos where args are encountered.
                    # this would be the place to do that
                    for argume in fetch:
                        self.variables.append(argume.arg)
                        self.symbolic_variables[argume.arg] = ('Sym' + str(self.symbol_count))
                        self.symbol_count += 1
                if isinstance(fetch, str):
                    # if fetch is singular add it to the variables and generate a symbol for it
                    self.variables.append(fetch)
                    self.symbolic_variables[argument.arg] = ('Sym' + str(self.symbol_count))
                    self.symbol_count += 1

    """This function will handle decorators"""
    def get_decorator_list(self):
        pass

    """ this function is for handling the returns list"""
    def get_return_list(self):
        pass

    """This method recursively extracts statements from the function to store them in a the FuncDef structure"""
    def process_function_body(self):
        function_body = self.head.body
        for statement in function_body:
            self.extract_section(statement)

    # ###################################################################################################
    # ###    EXTRACT ELEMENTS FROM A GIVEN NODE AND FORWARD THEM TO BE PROCESSED
    # ###################################################################################################

    # this function takes a list node and processes each element in the body of that node list
    def extract_from(self, nodelist):
        for statement in nodelist:
            self.extract_section(statement)

    def extract_section(self, statement):
        # to increase handling of data structures add case here
        if isinstance(statement, ast.Assign):
            self.process_assign(statement)
        elif isinstance(statement, ast.If):
            self.process_if(statement)
        elif isinstance(statement, ast.Return):
            self.process_return(statement)
        elif isinstance(statement, ast.While):
            self.process_while(statement)
        else:
            print("The statement, ", statement, " is not recognised by this process")

    # this method adds the name of the current node to active, then extracts recursively,
    # then pops the name back off active
    def recurse_node(self, name, node):
        self.active_code_block.append(name)
        self.extract_from(node)
        self.active_code_block.pop()

    # ###################################################################################################
    # ###       END OF EXTRACTOR TYPE - FUNCTION SELECTOR
    # ###       START OF ASSIGN EXTRACTOR
    # ###################################################################################################

    def process_assign(self, statement):
        log_info('Assign found on line {0}'.format(statement.lineno))

        variable_name_list = get_variable_name(statement)
        variable_value_list = get_variable_value(statement)
        variable_values = []
        if len(variable_name_list) > 1:
            if len(variable_value_list) > 1:
                # tuples on both sides, so zip them
                variable_values = list(zip(variable_name_list, variable_value_list))
        else:
            if len(variable_value_list) > 1:
                variable_values = [(variable_name_list[0], variable_value_list)]
            else:
                variable_values = [(variable_name_list[0], variable_value_list[0])]

        # check that each variable is in the variable list or else add it.
        for variable_name in variable_name_list:
            if variable_name not in self.variables:
                self.variables.append(variable_name)

        # need to make a copy of the state of this variable to prevent dynamic updating of list
        current_active_list = [node for node in self.active_code_block]
        self.list_of_statements_in_function.append(('Assign', statement.lineno, variable_values, current_active_list))
        log_info(str(variable_values))

    # ###################################################################################################
    # ###       END OF ASSIGN EXTRACTOR
    # ###       START OF IF EXTRACTOR
    # ###################################################################################################

    def process_if(self, statement):
        # generate a unique identify the current "if" statement starting at IF001
        self.conditional_count += 1
        this_ift = 'IF' + str.zfill(str(self.conditional_count), 3) + 'T'
        this_iff = 'IF' + str.zfill(str(self.conditional_count), 3) + 'F'

        # initiate variables to store linenos for the three conditional sections
        # the initial zero is for checking if there is any code in the section 0 means there isn't
        test_lineno, body_lineno, orelse_lineno = 0, 0, 0

        # extract the position and text of the test
        test_lineno = statement.test.lineno
        test_condition = decompile(statement.test)
        self.conditions_dict[this_ift] = [test_lineno, test_condition]

        # this might need adjusting to suit the phrasing of the prolog program
        self.conditions_dict[this_iff] = [test_lineno, ' not ( ' + test_condition + ' )']

        # if the body section exists get its start lineno
        if dhf.get_fields(statement.body):
            log_info('{0} exists'.format(this_ift))
            body_lineno = statement.body[0].lineno

        else:
            log_info('{0} does not exist'.format(this_ift))

        # if the orelse section exists get its start lineno
        if dhf.get_fields(statement.orelse):
            log_info('{0} exists'.format(this_iff))
            orelse_lineno = statement.orelse[0].lineno

        else:
            log_info('{0} does not exist'.format(this_iff))

        # add new paths to the path list
        active_paths_true = []
        active_paths_false = []
        log_info('paths contains {0}'.format(str(self.paths)))
        parents = self.active_code_block
        untouched_paths = []

        for path in self.paths:
            direct_parent = parents[-1]
            if direct_parent in path:
                log_info('{0} has {1}'.format(path, parents))
                if body_lineno != 0:
                    active_paths_true += [path + [this_ift]]

                # if there is an else statement, add the orelse to paths
                if orelse_lineno != 0:
                    active_paths_false += [path + [this_iff]]
            else:
                log_info("{0} doesn't have {1}".format(path, parents))
                untouched_paths.append(path)


        if active_paths_true or active_paths_false:
            self.paths = active_paths_true + active_paths_false + untouched_paths
            log_info('paths list now contains {0}'.format(self.paths))
        log_info(str(len(self.paths)))
        log_info('IF found, TEST= {0}, BODY on {1} ORELSE on {2}'.format(test_lineno, body_lineno, orelse_lineno))

        # first the body section
        if body_lineno != 0:
            self.recurse_node(this_ift, statement.body)

        # then the orelse 'False' path
        if orelse_lineno != 0:
            self.recurse_node(this_iff, statement.orelse)

    # ###################################################################################################
    # ###       END OF IF EXTRACTOR
    # ###       START OF RETURN EXTRACTOR
    # ###################################################################################################

    def process_return(self, statement):
        text = decompile(statement).strip('\n').replace("return ", "")
        line = statement.lineno
        current_active_list = [node for node in self.active_code_block]
        self.list_of_statements_in_function.append(('Return', line, [('return', text)], current_active_list))
        log_info('Return statement found, adding to list of statements = {0}'.format(text))

    # ###################################################################################################
    # ###       END OF RETURN EXTRACTOR
    # ###       START OF WHILE LOOPS EXTRACTOR
    # ###################################################################################################

    def process_while(self, statement):

        # first need to generate unique names for this loop structure
        self.conditional_count += 1
        this_wh_t = 'WH' + str.zfill(str(self.conditional_count), 3) + 'T'
        this_wh_f = 'WH' + str.zfill(str(self.conditional_count), 3) + 'F'
        loop_iteration_number = 0

        # set up the sections of the structure defaulting to not existing
        # initiate variables to store linenos for the three conditional sections
        # the initial zero is for checking if there is any code in the section 0 means there isn't
        test_lineno, body_lineno, orelse_lineno = 0, 0, 0

        # extract the position and text of the test
        test_lineno = statement.test.lineno
        test_condition = decompile(statement.test)
        self.conditions_dict[this_wh_t] = [test_lineno, test_condition]

        # this might need adjusting to suit the phrasing of the prolog program
        self.conditions_dict[this_wh_f] = [test_lineno, ' not ( ' + test_condition + ' )']

        # if the body section exists get its start lineno
        if dhf.get_fields(statement.body):
            log_info('{0} exists'.format(this_wh_t))
            body_lineno = statement.body[0].lineno
        else:
            log_info('{0} does not exist'.format(this_wh_t))

        # if the orelse section exists get its start lineno
        if dhf.get_fields(statement.orelse):
            log_info('{0} exists'.format(this_wh_f))
            orelse_lineno = statement.orelse[0].lineno
        else:
            log_info('{0} does not exist'.format(this_wh_f))

        # add new paths to the path list
        active_paths_true = []
        #active_paths_false = []
        untouched_paths = []
        log_info('paths contains {0}'.format(str(self.paths)))
        parents = self.active_code_block

        for a_path in self.paths:

            direct_parent_code_block = parents[-1]

            if direct_parent_code_block in a_path:
                log_info('{0} has {1}'.format(a_path, direct_parent_code_block))
                if body_lineno != 0:
                    for path_cycles in LOOP_LIST:
                        current_new_path = [a_path + [this_wh_f] + [this_wh_t] * path_cycles ]
                        active_paths_true += current_new_path
                        print('active_paths += ', current_new_path )
            else:
                log_info("{0} doesn't have {1}".format(a_path, parents))
                untouched_paths.append(a_path)

        if active_paths_true:
            self.paths = active_paths_true + untouched_paths
            log_info('paths list now contains {0}'.format(self.paths))
        log_info(str(len(self.paths)))
        log_info('IF found, TEST= {0}, BODY on {1} ORELSE on {2}'.format(test_lineno, body_lineno, orelse_lineno))

        # first the body section
        if body_lineno != 0:
            self.recurse_node(this_wh_t, statement.body)

        # then the orelse 'False' path
        if orelse_lineno != 0:
            self.recurse_node(this_wh_f, statement.orelse)

    # ###################################################################################################
    # ###       END OF WHILE LOOP EXTRACTOR
    # ###       START OF SYMBOLIC EXECUTION SECTION
    # ###################################################################################################

    def build_paths(self):
        """
        given a list of path conditions this function symbolically evaluates
        the conditions for satisfying this path
        """
        #
        block_code_dict = {}
        path_dicty = {}
        # Make the list of all code blocks in the function
        # e.g. ['IF001F', 'WH002F', 'IF001T', 'WH003T', 'list_identity', 'WH003F', 'WH002T']
        all_block_list = list(set(chain.from_iterable(self.paths)))

        # set up a dictionary to hold the code for each code block
        for block in all_block_list:
            block_code_dict.setdefault(block, [])
        for line in self.list_of_statements_in_function:
            # put each statement into its appropriate code block
            block_code_dict[line[3][-1]].append(line)

        # iterate paths to build constraints for each path
        for path in self.paths:

            #create the paths name
            function_name = [self.head.name]
            function_name.extend([item for item in path])
            path_name = 'xx'.join(function_name)

            # initialise the code list for this path
            basic_run = block_code_dict['list_identity']
            path.remove('list_identity')
            loops = Counter(path)

            # insert nested conditons and code blocks into paths code list
            for block_name in path:

                # lineno of the start of the inserted block
                block_start = self.conditions_dict[block_name][0]

                # constraint to insert
                block_value = self.conditions_dict[block_name][1]

                # get the list of statement in this code block
                block_statements = block_code_dict[block_name]

                # find the position of the insertion point in the list of statements
                # start is used to find the list insert position
                start = 0
                # increment start, until the next line of code should be after it
                if basic_run:
                    while start < len(basic_run) and basic_run[start][1] < block_start:
                        start += 1

                # if this code block only happens once, and it is not empty
                if loops[block_name] == 1 and not block_statements:
                    # if the code block is empty just insert the constarint into the basic run list
                    basic_run = basic_run[:start] + [[block_value,block_start]] + basic_run[start:]
                else:
                    # else insert the constraint and the code list into the basic_run list
                    basic_run = basic_run[:start] + ([[block_value,block_start]] + block_code_dict[block_name]) + basic_run[start:]

            path_dicty[path_name] = basic_run

        print('path building complete, paths found = {0}'.format(len(path_dicty)) )
        self.path_codes_list = path_dicty

    def symbolically_execute_paths(self):
        for path, codes_list in self.path_codes_list.items():
            self.symbolically_execute_a_path(path, codes_list)

    def symbolically_execute_a_path(self, path, codes_list):
        this_path_variables = {}
        this_path_constraints = {}
        for variable in self.variables:
            this_path_variables.setdefault(variable, [])

        for variable_name, symbolic_variable_name in self.symbolic_variables.items():
            this_path_variables[variable_name].append(symbolic_variable_name)

        for line in codes_list:
            if isinstance(line, tuple):
                # process an assignment
                target = line[2][0][0]
                # convert the equation into a list of infix elements
                value = str(line[2][0][1]).split(' ')
                value = dhf.postfix_from_infix_list(value)
                this_path_variables = dhf.symbolise(this_path_variables, target, value)

                pass
            elif isinstance(line, list):
                # process a conditional
                # when a conditional is met we need to extract its meaning from the current symbolic execution
                # and add the constraint to the set of path constraints
                constraint  =  dhf.extract(this_path_variables, line[0].split(' '))
                this_path_constraints.setdefault(path, []).append(constraint)
            else:
                print("Weird element has crawled into the the path structure, it is not a tuple or a list")
        self.path_dict[path] = {"Variables": [this_path_variables], "Conditions": [this_path_constraints]}

    def test_path_constraints(self):

        count=0
        for path in self.path_dict.keys():
            count +=1
            conditions = self.path_dict[path]["Conditions"]
            variables = self.path_dict[path]["Variables"]

            # this lambda takes a comma separated list and coverts it to a string
            # ['', 'not', '(', 'Sym0', '>', '5', ')'] gets converted to  "not ( Sym0 > 5)"
            lambdalise = lambda x: ' '.join(list(conditions[0].values())[0][x])
            count_of_constraints = len(list(conditions[0].values())[0])

            #creates asingle string with all constraints for ECLiPSe
            set_of_conditions = "(" + ') and ('.join([lambdalise(x) for x in list(range(count_of_constraints))])+")"

            # ECLiPSe uses a single = to denote equality, Python uses ==
            set_of_conditions = set_of_conditions.replace('==','=')

            # call to write and run ECLiPSe for each path
            out, result_dict = logic(count, self.output_dir, str(path),set_of_conditions, self.symbolic_variables)
            # print(out)
            print('result_dict',result_dict)
            self.return_dict[path] = []
            self.return_dict[path].append(result_dict)
            self.return_dict[path].append(variables[0]['return'])

            print("\nAnalysing Path for satisfiability\n")

    """
    This method takes the processed paths and removes unsatisfiable paths from
    the dictionary self.return_dict
    """
    def filter_returned_paths(self):
        self.return_dict = {key:value for key,value in self.return_dict.items() if value[0]}

    """
    This method processes the satisfiable paths into a dictionary of
    unit tests, each dictionary key is the flow path
     each dictionary value is a list containing the expected result """
    def evaluate_expected_results(self):
        #keys is the path name, itemz is a list with
        # itemz[0] = input values
        # itemz[1] = postfix return equation for path
        for keys, itemz in self.return_dict.items():
            symbolic_variables = itemz[0].keys()
            infix_path_return_eqn = dhf.post_to_in(itemz[1])
            return_eqn_with_inputs = []
            for operand in infix_path_return_eqn:
                if operand in symbolic_variables:
                    return_eqn_with_inputs.append(str(itemz[0][operand]))
                else:
                    return_eqn_with_inputs.append(operand)
            equation_string = ''.join(return_eqn_with_inputs)
            try:
                expected_return = eval(equation_string)
            except NameError:
                expected_return= "\'" + equation_string + "\'"
            print("##################################################################################\n")
            print(keys)
            print(self.path_dict[keys]['Conditions'])
            print("Producing Unit Test from satisfied results")
            print('Symbolic equation for path = ', ''.join(infix_path_return_eqn))
            print('Symbolic values for path   = ', itemz[0])
            print('equation with values       = ', equation_string)
            print('expected result            = ',expected_return,'\n')

            self.return_dict[keys].append([expected_return])
        print("##################################################################################\n")

def chunks(whole, size):
    """Yield successive n-sized chunks from list chunks."""
    for x in range(0, len(whole), size):
        yield whole[x : x + size]

# this needs a list of symbolic values and to create the files based on that list
def logic(number, output_dir, path, constraint, symbol_vars):
    output_dir = output_dir.replace('\\','/')
    filename = output_dir + "path" + str(number) + ".pl"
    # write a .pl file
    symbols = sorted([value for value in symbol_vars.values()])
    symboltext = ', '.join(symbols)

    with open(filename, 'w') as log:
        log.write(":- import ptc_solver.\n")
        log.write("example({0}):-\n".format(symboltext))
        log.write("    write(\"~~{0}~~{1}~~##\"),\n".format(path, constraint))
        log.write("    ptc_solver__clean_up,\n")
        log.write("    ptc_solver__default_declarations,\n")
        log.write("    ptc_solver__type(Type0, real, range_bounds({0})),\n".format(RANGE_BOUNDS))
        log.write("    ptc_solver__variable([{0}], Type0),\n".format(symboltext))
        log.write("    ptc_solver__sdl({0}),\n".format(constraint))
        log.write("    ptc_solver__label_reals([{0}]),\n".format(symboltext))
        extraction_text = []
        for symbol in symbols:
            extraction_text.append("    write(\"##{0}##\"),\n".format(symbol) + "    write({0})\n".format(symbol))
        extraction_text = ','.join(extraction_text) + "."
        log.write(extraction_text)
    vol = ""

    # run and get results from the .pl file
    result = Popen([vol+"eclipse", "-f", filename, "-e", "example({0}).".format(symboltext)], shell=True, stdout=PIPE)
    try:
        outs, errs = result.communicate(timeout=10)
    except TimeoutError:
        result.kill()
        outs, errs = result.communicate()

    result.wait()
    print("calling to ECLiPSe clp")

    full_eclipseclp_output_text = outs.decode(encoding="utf-8")
    path_condition_text = full_eclipseclp_output_text.split('~~')[1:3]

    symbolic_results_list_pairs = full_eclipseclp_output_text.split('##')[2:]

    result_dict = {}
    symbolic_value= None
    symbolic_result_list_rational = list(chunks(symbolic_results_list_pairs , 2))
    for result_list in symbolic_result_list_rational:
        symbolic_value= result_list
        # if the result is in rational number string form 63_2 = 63/2 = 31.5
        if '_' in result_list[1]:
            symbolic_value = result_list[1].split('_')
            symbolic_value = float(symbolic_value[0])/float(symbolic_value[1])
        result_dict[result_list[0]] = symbolic_value
    if path_condition_text and symbolic_value:
        print("results for path \n\t",path_condition_text[0],path_condition_text[1],symbolic_results_list_pairs, result_dict['Sym0'])
    elif path_condition_text:
        print("results for path \n\t",path_condition_text[0],path_condition_text[1])
    return outs, result_dict