from PLD2 import PLD
import easygui
import logging
import pickle
import os

log_info = logging.info

def create_config():
    """
    this function is to ask a bunch of questions and create a configuration file
    to set up the project
    """
    configs = {}
    configs['ECLIPSE_DIR'] = easygui.diropenbox(msg='Please select ECLiPSe Program Directory', title='Select ECLiPSe program directory', default='C:/')
    configs['ECLIPSE_FILES_DIR'] = easygui.diropenbox(msg='Please select ECLiPSe working files Directory', title='Select Working files directory for ECLiPSe', default='C:/')
    configs['SOURCE_DIR'] = easygui.diropenbox(msg='Select Python Code Source folder', title='Select Source Directory', default='c:/')
    configs['PYGEN_DIR'] =  os.path.dirname(__file__)

    with open("pygenConfig.cfg",'wb') as cfg:
        pickle.dump(configs, cfg)
    return configs

def get_config():
    try:
        with open('pygenConfig.cfg','rb') as cfg_file:
            config = pickle.load(cfg_file)
    except FileNotFoundError:
        print("Config file not found, running config setup")
        config = create_config()
    return config

def add_to_list(base, separator, sub_nodes):

    """
    example ("Hi", "..", ['dave','chris',greg'])  will return ['Hi..dave','Hi..chris','Hi..greg']
    useful for concatenating the node attributes to a nodename for traversing the node tree
    :param base: this is the first part of each entry
    :param separator:   this is the joining string
    :param bits:   list of endings
    :return:   list of joined strings
    """
    return [separator.join([base, sub_node]) for sub_node in sub_nodes]


def iz(x):
    log_info(str(x))
    return True if x else False


# get the fields for any given ast type
def get_fields(tree_object):
    log_info(str(tree_object))
    """
    the get_fields function looks up the PLD Python Language Dictionary
    PLD contains the _fields connected to each language structure in Python
    """
    node_fields = []
    if tree_object:
        node_fields.append(PLD[str(tree_object[0]).split(".")[1].split(' ')[0]])
    return node_fields


def chunks(whole, size):

    """Yield successive n-element chunks from a list of chunks.
    whole: list
    size: int
    return: list of size-element lists
    e.g. whole = [1,2,3,4,5,6,7,8,9,10,11,12], size = 3, return = [1,2,3] [4,5,6] [7,8,9] [10,11,12]
    chunks([a,b,c,d,e,f,g,h,i,j,k,l,m,n,o],5) [a,b,c,d,e] [f,g,h,i,j] [k,l,m,n,o]
    """
    for x in range(0, len(whole), size):
        yield whole[x: x + size]


def postfix_from_infix_list(input_list):
    log_info(str(input_list))
    """
    This function takes in a list of tokens with infix notation and converts it
    to a postfix notation (string list) to simplify the evaluation of Symbolic Assignments
    """

    operator_stack = []
    output_list = []
    operator_precedence_list = ['(', '+', '-', '*', '/', '**']

    for element in input_list:
        precedence = 10
        try:

            precedence = operator_precedence_list.index(element)
            print(element, " is an operator, with precedence level ", precedence )
        except ValueError:
            print(element," is not an operator, send it to the output list")
        if element == ')':
            closing_brackets = True
            while closing_brackets:
                popped = operator_stack.pop()
                if popped == '(':
                    closing_brackets = False
                else:
                    output_list.append(popped)
        elif ']' in element:
            group = element
            its_a_list = True
            while its_a_list:
                popped = output_list.pop()
                if '[' in popped:
                    its_a_list = False
                    group = popped + group
                    output_list.append(group)
                else:
                    group = popped + group
        elif precedence == 10:
            output_list.append(element)
        else:
            length_stack = len(operator_stack)
            if length_stack == 0:
                operator_stack.append(element)
            else:
                while len(operator_stack) > 0 and (operator_precedence_list.index(operator_stack[-1]) >= precedence):
                    removed_operator = operator_stack.pop()
                    output_list.append(removed_operator)
                operator_stack.append(element)
    while len(operator_stack) > 0:
        output_list.append(operator_stack.pop())
    print('output_list=', output_list)
    return output_list


def post_to_in(postfix_list):

    """
    this function accepts a postfix expression as a list of the contents and returns a string
    :param postfix_list:
    :return: returns the infix expression correlating to a postfix expression
    """
    log_info(str(postfix_list))
    result = ""
    stack = []
    operators_list = ['+', '-', '*', '/', '**']

    for item in postfix_list:
        if item in operators_list:
            partb = stack.pop()
            parta = stack.pop()
            stack.append( "( " + parta +' '+ item + ' ' + partb + " )" )
        else:
            stack.append(item)
    if len(stack) == 1:
        return stack.pop().split(' ')
    else:
        print("error in postfix expression")


def symbolise(symbolic_dict, target,  assignment):
    """
    This function takes as arguments
    1: a dictionary of variables and their symbolic values
    2: an equation
    the equation will be used to alter the symbolic values of a variable
    """
    return_list = []
    for elem in assignment:
        if elem in symbolic_dict.keys():
            return_list.extend(symbolic_dict[elem])
            print('added ', symbolic_dict[elem], ' to return list')
        else:
            print(elem, " not found in assignment, adding", elem, "to the return list")
            return_list.append(elem)
    symbolic_dict[target] = return_list
    return symbolic_dict


def extract(symbolic_dict, condition):
    """
    this function takes the current symbolic dictionary and a condition and
    returns the symbolic expression as a list of operators and operands

    :param symbolic_dict:
    :param condition:
    :return:
    """
    return_list = []
    for elem in condition:
        if elem in symbolic_dict.keys():
            elem_value = symbolic_dict[elem]
            return_list.extend(post_to_in(elem_value))
        else:
            return_list.append(elem)
    return return_list


def get_source_file(source_directory):
    print("Please select a target file using the file selection dialogue.")
    source_file = easygui.fileopenbox(filetypes=["*.py"],msg="Select a Python File to Analyse", title="Select Target File Dialogue",multiple=False)
    return source_file


def read_source_file(source_file):
    with open(source_file, 'r') as text:
        content = text.read()
    return content


def main():
    create_config()
    """
    sym_dict = {
        'x': ['Sym0', '*', '5', '+', '4'],
    }
    sym_dict2 = {key: postfix_from_infix_list(value) for key, value in sym_dict.items()}

    f = postfix_from_infix_list(['3', '+', 'x', '*', '6'])
    print(f)
    t= 'y'
    sym_dict3 = symbolise(sym_dict2, t, f)
    print(sym_dict3)
    ret = post_to_in(['3','5','*','5','6','+','*'])
    print(ret)
    """
if __name__ == '__main__':
    main()
