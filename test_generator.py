import data_handling_functions as dhf
import ast
from ast_decompiler import decompile
import collections
import logging
log_info = logging.info
"""This file is given the head node of a function and
returns a set of test data sets and results"""


class FuncDef(object):
    def __init__(self, node):
        self.head = node
        self.variables = []
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
        varvals = list(zip(varslist, valslist))
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

    def make_path_dict(self):
        a_statement = collections.namedtuple('a_statement', 'typz, lineno, equation ,parent')
        for line_of_code in self.list_of_statements_in_function:
            parent_sect = 'main'
            loc = a_statement(line_of_code[0],line_of_code[1],line_of_code[2],line_of_code[3])
            if loc.typz  == 'Assign':
                if dhf.iz(loc.parent):
                    parent_sect = loc.parent[-1]
                self.new_dict.setdefault(parent_sect, []).append(loc.equation[0])
            if loc.typz == 'Return':
                if dhf.iz(loc.parent):
                    parent_sect = loc.parent[-1]
                self.return_dict.setdefault(parent_sect, []).append(loc.equation[0])

    def solve_paths(self):
        for path in self.paths:
            self.solve_a_path(path)

    def solve_a_path(self, path):
        """
        given a list of path conditions this function symbolically evaluates
        the conditions for satisfying this path
        """
        path.remove('list_identity')

        a_statement = collections.namedtuple('a_statement', 'typz, lineno, equation ,parent')
        an_equation = collections.namedtuple('an_equation', 'target, value')
        this_path = {}

        this_path_conditions = {}
        for variable in self.variables:
            this_path.setdefault(variable, [])
        for symbol,symbolic_value in self.symbolic_variables.items():
            this_path[symbol].append(symbolic_value)

        # make the list of statements and conditions in the order they will be met.
        # can't really sort as we will get to looping later
        visited_blocks = []
        for line_of_code in self.list_of_statements_in_function:

            # named tuple extraction definitions
            loc = a_statement(line_of_code[0], line_of_code[1], line_of_code[2], line_of_code[3])
            leq = an_equation(line_of_code[2][0][0], line_of_code[2][0][1])

            # if this line of code has a block identifier then only add it if the identifier is for this path
            targ = leq.target
            valu = dhf.postfix_from_infix_list(leq.value.split(' '))

            # if the code is within a conditional section then loc.parent contains that value
            if loc.parent:

                # get the name of the containment area
                target = loc.parent[-1]
                if target in path:
                    if target not in visited_blocks:

                        # value is the areas condition split to a list
                        value = self.conditions_dict[target][1].split(' ')
                        value = dhf.extract(this_path, value)
                        this_path_conditions[target] = value
                        visited_blocks.append(target)

                    # this_path needs to update its variables to accommodate the new line of code
                    this_path = dhf.symbolise(this_path, targ, valu)

            # contd - or else it is the main section so it gets added
            else:
                this_path = dhf.symbolise(this_path, targ, valu)
            linetxt = 'xx'.join([item for item in path])
            self.new_dict[linetxt] = [this_path,this_path_conditions]
