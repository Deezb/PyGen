import data_handling_functions as dhf
import ast
from ast_decompiler import decompile
import collections
from uuid import uuid4
from subprocess import Popen, PIPE
import logging
log_info = logging.info
"""This file is given the head node of a function and
returns a set of test data sets and results"""


class FuncDef(object):
    def __init__(self, node, output_dir):
        self.head = node
        self.variables = []
        self.output_dir = output_dir
        self.symbolic_variables = {}
        self.constraint_list = []
        self.paths = [['list_identity']]
        self.if_count = 0
        self.list_of_statements_in_function = []
        self.conditions_dict = {}
        self.linecount = 0
        self.symbol_count = 0
        self.variable_count = 0
        self.active_ifs = []
        self.new_dict = {}
        self.path_dict = {}
        self.return_dict = {}

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

    def extract_section(self, statement):
        # to increase handling of data structures add case here
        if isinstance(statement, ast.Assign):
            self.process_assign(statement)
        elif isinstance(statement, ast.If):
            self.process_if(statement)
        elif isinstance(statement, ast.Return):
            self.process_return(statement)

    def process_assign(self, statement):
        log_info('Assign found on line {0}'.format(statement.lineno))

        varslist = self.get_vars(statement)
        valslist = self.get_vals(statement)
        varvals = []
        if len(varslist) > 1:
            if len(valslist) > 1:
                # tuples on both sides, so zip them
                varvals = list(zip(varslist, valslist))
        else:
            if len(valslist) > 1:
                varvals = [(varslist[0], valslist)]
            else:
                varvals = [(varslist[0], valslist[0])]

        #check that each variable is in the variable list or else add it.
        for varp in varslist:
            if varp in self.variables:
                pass
            else:
                self.variables.append(varp)
        exlist = [node for node in self.active_ifs]
        self.list_of_statements_in_function.append(('Assign', statement.lineno, varvals, exlist))
        log_info(str(varvals))

    # get variable names from tree node
    def get_vars(self, section):

        varslist = []
        for target in section.targets:

            # for single entries
            if hasattr(target, 'id'):
                return [target.id]

            # for multiple entries
            for elt in target.elts:
                # each elt represents a separate variable name
                if str(elt.ctx).startswith("<_ast.Store object at"):
                    varslist.append(elt.id)
                elif str(elt.ctx).startswith("<_ast.Load object at"):
                    log_info("Load in vars, not allowed")
        return varslist

    # get assignment values from tree node
    def get_vals(self, section):
        vals = []
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
                vals.append(value.n)
        return vals


    def process_if(self, statement):
        # generate a unique identify the current "if" statement starting at IF001
        self.if_count += 1
        this_ift = 'IF' + str.zfill(str(self.if_count), 3) + 'T'
        this_iff = 'IF' + str.zfill(str(self.if_count), 3) + 'F'

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
        parent = self.active_ifs
        untouched_paths = []

        for path in self.paths:
            if parent:
                if parent[-1] in path:
                    log_info('{0} has {1}'.format(path, parent))
                    if body_lineno != 0:
                        active_paths_true += [path + [this_ift]]

                    # if there is an else statement, add the orelse to paths
                    if orelse_lineno != 0:
                        active_paths_false += [path + [this_iff]]
                else:
                    log_info("{0} doesn't have {1}".format(path, parent))
                    untouched_paths.append(path)

            else:
                if body_lineno != 0:
                    active_paths_true += [path + [this_ift]]

                # if there is an else statement, add the orelse to paths
                if orelse_lineno != 0:
                    active_paths_false += [path + [this_iff]]

        if active_paths_true or active_paths_false:
            self.paths = active_paths_true + active_paths_false + untouched_paths
            log_info('paths list now contains {0}'.format(self.paths))
        log_info(str(len(self.paths)))
        log_info('If found test on line {0}, body on {1} orelse on {2}'.format(test_lineno, body_lineno, orelse_lineno))

        # scan body children for nested items
        if body_lineno != 0:
            self.active_ifs.append(this_ift)
            self.extract_if(statement.body)
            self.active_ifs.pop()
        # scan orelse children for nested items
        if orelse_lineno != 0:
            self.active_ifs.append(this_iff)
            self.extract_if(statement.orelse)
            self.active_ifs.pop()

    # this function takes an if statement and combines the contents into a
    # triple list.
    def extract_if(self, node):
        for section in node:
            self.extract_section(section)

    def process_return(self, statement):
        text = decompile(statement).strip('\n').replace("return ", "")
        line = statement.lineno
        self.list_of_statements_in_function.append(('Return', line, [('return', text)], self.active_ifs))
        log_info('Return statement found, adding to list of statements = {0}'.format(text))

    # ###################################################################################################
    # ###     THE EXTRACTION OF PATHS HAS FINISHED NOW THE PATHS MUST BE PROCESSED
    # ###################################################################################################
    # ###################################################################################################
    # ###     THE EXTRACTION OF PATHS HAS FINISHED NOW THE PATHS MUST BE PROCESSED
    # ###################################################################################################
    # ###################################################################################################
    # ###     THE EXTRACTION OF PATHS HAS FINISHED NOW THE PATHS MUST BE PROCESSED
    # ###################################################################################################


    def symbolically_execute_paths(self):
        for path in self.paths:
            self.symbolically_execute_a_path(path)

    def symbolically_execute_a_path(self, path):
        """
        given a list of path conditions this function symbolically evaluates
        the conditions for satisfying this path
        """
        path.remove('list_identity')

        # create an empty directory for storing postfix {symbol:symbolic value}
        #  e.g.{'x': ['2','Sym0','*','5','+'], 'y': [ 'Sym1', '2', '+'] }
        this_path = {}

        # create empty dict for storing a condition's name and its infix Symbolic variable expression
        # i.e. {'IF001T' : ['Sym0', '>=', '10', 'and', 'Sym0', '<=', '20']}
        this_path_conditions = {}

        # set-up an empty list to contain values for each variable as key
        for variable in self.variables:
            this_path.setdefault(variable, [])

        # for each function parameter add the Symbolic Variable to the parameter variable
        for symbol,symbolic_value in self.symbolic_variables.items():
            this_path[symbol].append(symbolic_value)

        # list to store the set
        visited_blocks = []

        # named tuple definitions
        a_statement = collections.namedtuple('a_statement', 'typz, lineno, equation ,parent')
        an_equation = collections.namedtuple('an_equation', 'target, value')


        # iterate through the code to see if the line is in this path

        for line_of_code in self.list_of_statements_in_function:

            # named tuple extraction definitions
            loc = a_statement(line_of_code[0], line_of_code[1], line_of_code[2], line_of_code[3])
            leq = an_equation(loc.equation[0][0], loc.equation[0][1])

            targ = leq.target
            # turn an equation into a postfix list representation
            valu = dhf.postfix_from_infix_list(str(leq.value).split(' '))

            # if the code is within a conditional section then loc.parent contains that value
            if loc.parent:

                # get the name of the containment area
                target = loc.parent[-1]

                # if the line of code has a block identifier then only
                # add it if the identifier exists in this path
                if target in path:
                    for zone in loc.parent:
                        if zone not in visited_blocks:
                            # value is the areas condition split to a list
                            value = self.conditions_dict[zone][1].split(' ')
                            value = dhf.extract(this_path, value)
                            this_path_conditions[zone] = value
                            visited_blocks.append(zone)

                    # this_path needs to update its variables to accommodate the new line of code
                    this_path = dhf.symbolise(this_path, targ, valu)

            # contd - or else it is the main section so it gets added
            else:
                this_path = dhf.symbolise(this_path, targ, valu)
            linetx = [self.head.name]
            linetx.extend([item for item in path])
            linetxt = 'xx'.join(linetx)
            self.path_dict[linetxt] = {"Variables": [this_path],"Conditions": [this_path_conditions]}
        print("finished adding path sequences to path_dict")

    def test_path_constraints(self):

        count=0
        for path in self.path_dict.keys():
            count +=1
            conditions = self.path_dict[path]["Conditions"]
            variables = self.path_dict[path]["Variables"]
            f = lambda x: ' '.join(list(conditions[0].values())[x])
            set_of_conditions = "(" + ') and ('.join([f(x) for x in list(range(len(list(conditions[0].values()))))])+")"
            set_of_conditions = set_of_conditions.replace('==','=')
            out, result_dict = logic(count, self.output_dir, str(path),set_of_conditions, self.symbolic_variables)
            # print(out)
            print('result_dict',result_dict)
            self.return_dict[path] = []
            self.return_dict[path].append(result_dict)
            self.return_dict[path].append(self.path_dict[path]['Variables'][0]['return'])

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
        log.write("    ptc_solver__type(Type0, real, range_bounds(-10.0, 30.0)),\n")
        log.write("    ptc_solver__variable([{0}], Type0),\n".format(symboltext))
        log.write("    ptc_solver__sdl({0}),\n".format(constraint))
        log.write("    ptc_solver__label_reals([{0}]),\n".format(symboltext))
        extraction_text = []
        for symbol in symbols:
            extraction_text.append("    write(\"##{0}##\"),\n".format(symbol) + "    write({0})\n".format(symbol))
        extraction_text = ','.join(extraction_text) + "."
        log.write(extraction_text)
    vol = ""
    if output_dir == "/Volumes/C/EclipsePTC/solver/":
        vol = "/Volumes/C/Program\ Files/ECLiPSe\ 6.1/lib/x86_64_nt/"

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
    pathuuid = path_condition_text[1]
    result_dict = {}
    symbolic_value= None
    symbolic_result_list_rational = list(chunks(symbolic_results_list_pairs , 2))
    for result_list in symbolic_result_list_rational:
        symbolic_value= result_list
        if '_' in result_list[1]:
            symbolic_value = result_list[1].split('_')
            symbolic_value = float(symbolic_value[0])/float(symbolic_value[1])
        result_dict[result_list[0]] = symbolic_value
    if path_condition_text and symbolic_value:
        print("results for path \n\t",path_condition_text[0],path_condition_text[1],symbolic_results_list_pairs, result_dict['Sym0'])
    elif path_condition_text:
        print("results for path \n\t",path_condition_text[0],path_condition_text[1])
    return outs, result_dict