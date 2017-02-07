import data_handling_functions as dhf
import logging
log_info = logging.info

class SourceTree(object):
    def __init__(self,source):
        self.tree = source
        self.name = 'tree'
        self.count = 0
        self.queue = [(self.count, self.name)]
        self.all_nodes_list = []
        self.child_array = {}
        self.parent_array = {}
        self.nodevals = []

    def process_source_code(self):
        while len(self.queue) > 0:
            parent_sent = self.queue[0]
            current_parent_number = parent_sent[0]
            current_nodes_children = self.get_child_nodes_of(parent_sent)
            for child_node in current_nodes_children:
                if child_node == parent_sent:
                    self.all_nodes_list.append(parent_sent)
                    self.queue_del(child_node)
                else:
                    self.count += 1
                    log_info("{0}, {1} is being added to the queue".format(self.count, child_node))
                    self.queue.append((self.count, child_node))
                    self.parent_array[self.count] = current_parent_number
                    self.child_array.setdefault(current_parent_number, []).append(self.count)

    def construct_node_data_list(self):
        # this function takes each node in the end_list and adds more detail
        for node_tuple in self.all_nodes_list:
            node_number, node_str = node_tuple
            valtype = eval('str(type((self.{0})))'.format(node_str))
            child_node_numbers_list = self.child_array[node_number] if node_number in self.child_array.keys() else []
            parent_node_number = self.parent_array[node_number] if node_number in self.parent_array.keys() else []
            if "class '_ast." in valtype:
                node_ast_type = str(valtype)[13:-2]
            else:
                node_ast_type = str(valtype)[8:-2]

            # each node gets the following details recorded in a tuple
            self.nodevals.append(
                                    (
                                        node_number,
                                        parent_node_number,
                                        child_node_numbers_list,
                                        node_str,
                                        valtype,
                                        node_ast_type,
                                        eval('self.' + node_tuple[1])
                                    )
                                 )

    def queue_del(self, queue_item):
        try:
            self.queue.remove(queue_item)
        except IndexError:
            print("the item {0} was not found in the queue, (called by sourceTree.mainrun())".format(queue_item))

    def get_child_nodes_of(self, parent_sent):
        (count, parent_full_name) = parent_sent
        child_list = [(count, parent_full_name)]
        log_info('starting analysis of {0}'.format( parent_full_name))

        # this uses the built-in eval method to process the chained nodes to find its type
        parent_is_list = eval('isinstance(self.{0}, list)'.format(parent_full_name))

        # if the parent node is a list then return the child nodes using child_array numbers to get the nodes
        # or else get the child node values based on the PLD _fields reference
        if parent_is_list:
            child_list_len = len(eval('self.' + parent_full_name))
            list_of_children = list(map(lambda x: '[{0}]'.format(x), range(child_list_len)))
            child_list.extend(dhf.add_to_list(parent_full_name, '', list_of_children))
        else:
            parent = eval('type(self.{0})'.format(parent_full_name))
            parent_value = str(parent)

            # hack extraction of type name from a node, but they don't have names - need alternative
            parent_node_type = parent_value[13:-2] if parent_value.startswith("<class '_ast.") else parent_value[8:-2]

            if parent_node_type in dhf.PLD:
                child_nodes_list = dhf.PLD[parent_node_type]
                log_info("{0} found in PLD".format(parent_node_type))
                for child_node in child_nodes_list:
                    child_list.append('.'.join([parent_full_name, child_node]))
            else:
                log_info("{0} not found in PLD".format(parent_node_type))
                log_info("child_list returning for '{0}' analysis = {1}".format(parent_full_name, child_list))
        return child_list
