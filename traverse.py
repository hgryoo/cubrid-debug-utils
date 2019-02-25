import sys
import gdb
import graphviz

from graphviz import Digraph

def is_container(v):
    c = v.type.code
    return (c == gdb.TYPE_CODE_STRUCT or c == gdb.TYPE_CODE_UNION)

def is_pointer(v):
    return (v.type.code == gdb.TYPE_CODE_PTR)

program_name = sys.argv[0]
arguments = sys.argv[1:]
count = len(arguments)

def make_pt_node_type_enum():
    enum_typedef = gdb.lookup_type("PT_NODE_TYPE")
    gdb.write("%s\n" % enum_typedef.code)
    node_type = gdb.types.get_basic_type(enum_typedef)
    return gdb.types.make_enum_dict (node_type)

def is_pt_node(v):
    pt_node_type = gdb.lookup_type("PT_NODE")
    return (v.type.__str__() == pt_node_type.__str__())

def is_null(v):
    target = v.dereference()
    return str(target.address) == '0x0'

def cpt_parser(s):
    create_pt_node_internal(dot, s)

def create_pt_node_internal(graph, v):
    attr = create_node_attr(v)
    id = add_dot_node(attr)

    node_type = v['node_type']
    gdb_write(node_type)
    
    info = v['info']
    id2 = add_dot_node(attr)

    add_dot_edge(id, id2, 'a')
    gdb_write(dot.source)
    

def gdb_write(s):
    gdb.write("%s\n" % s)

def init_dot():
    global dot
    global node_cnt
    
    dot = Digraph()
    dot.body.append("newrank=true")
    node_cnt = 0

def init_cub_types():
    global type_pt_node
    global type_pt_nodetype
    global type_pt_statement_info

    type_pt_node = gdb.lookup_type("PT_NODE")
    type_pt_nodetype = gdb.lookup_type("PT_NODE_TYPE")
    type_pt_statement_info = gdb.lookup_type("PT_STATEMENT_INFO")


def create_node_attr(v):
    attr = {}
    attr['shape'] = 'record'
    attr['label'] = v.type.__str__()
    return attr

def attr_to_str(attr):
    return ' '.join(['%s=%s' % (key, value) for (key, value) in attr.items()])

def create_pt_node(s):
    node_s = add_brackets(s)
    this_v = eval_str(node_s)

    attr = create_node_attr(this_v)
    id = add_dot_node(attr)

    node_type_str = node_s + ".node_type"
    node_type = eval_str(node_type_str)
    gdb_write(node_type)

    info_str = node_s + ".info"
    info_id = create_info_node(info_str)
    
    add_dot_edge(id, info_id, 'a')
    gdb_write(dot.source)
   
def create_info_node(s):
    global node_cnt

    info_s = add_brackets(s)
    this_v = eval_str(info_s)
    attr = create_node_attr(this_v)
    id = add_dot_node(attr)

    #
    return id 

def add_dot_node(attr):
    global node_cnt
    label = attr['label']
    del attr['label']
    dot.node(str(node_cnt), label, attr_to_str(attr))
    node_cnt += 1
    return node_cnt - 1

def add_dot_edge(f, to, attr):
    dot.edge(str(f), str(to))

def eval_str(s):
    return gdb.parse_and_eval(s)

def add_brackets(s):
    return "(" + s + ")"

    
class CUBRID_PTNODE_Traversal(gdb.Command):
    '''
    cpt_parser PT_NODE
    '''
    def __init__(self): 
        super(CUBRID_PTNODE_Traversal, self).__init__(
            'cpt_parser',
            gdb.COMMAND_DATA, gdb.COMPLETE_SYMBOL, False)
        
        init_dot()
        init_cub_types()

    def invoke(self, arg, from_tty):
        try:
            v = gdb.parse_and_eval(arg)
            cpt_parser(v)
        except gdb.error, e:
            raise gdb.GdbError(e.message)

CUBRID_PTNODE_Traversal()
