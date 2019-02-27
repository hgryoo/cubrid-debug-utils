import sys
import gdb
import graphviz
import traceback
import logging

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
    if type(v) is gdb.Value:
        return (v.type.__str__() == pt_node_type.__str__())
    else:
        return str(v) == str(pt_node_type)

def is_null(v):
    target = v.dereference()
    return str(target.address) == '0x0'

def cpt_parser(s):
    global dot
    create_pt_node_internal(dot, s)

def create_pt_node_internal(graph, v):
    logging.debug('create_pt_node_internal')
    attr = create_node_attr(v)

    node_type = v['node_type']
    attr['label'] = "<PT_NODE> " + str(node_type)
    
    data_type = v['data_type']
    if not is_null(data_type):
        create_pt_node_internal(graph, data_type)
    
    info = v['info']
    concrete_info_type = (str(node_type))[3:].lower()
    gdb_write(concrete_info_type)
    concrete_info = info[concrete_info_type]
    info_id = create_pt_node_info(graph, concrete_info)

    id = add_dot_node(graph, attr)
    add_dot_edge(graph, id, info_id, 'info')
    return id

def create_pt_node_info(graph, v):
    gdb_write('create_pt_node_info')
    attr = create_node_attr(v)

    attr['label'] = "<PT_STATEMENT_INFO> " + str(v.type)

    conn_dict = {}

    fields = v.type.fields()
    for f in fields:
        f_name = f.name
        f_type = f.type

        val = v[f_name]

        if is_pointer(val):
            if not is_null(val):
                val_p = val.dereference()       
                if is_pt_node(val_p):
                    pt_id = create_pt_node_internal(graph, val_p)
                    conn_dict[f_name] = pt_id
                else:
                    attr['label'] += "|" + str(f_name) + " = " + str(val_p)
        else:
            # hack
            attr['label'] += "|" + str(f_name) + " = " + str(val)

    id = add_dot_node(graph, attr)            

    for key, value in conn_dict.iteritems():
        add_dot_edge(graph, id, value, key)       
    
    return id 

def gdb_write(s):
    gdb.write("%s\n" % s)

def init_dot():
    global node_cnt
    global dot
    
    node_cnt = 0
    dot = Digraph()
    dot.body.append("newrank=true")

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


def add_dot_node(graph, attr):
    global node_cnt
    label = "{" + attr['label'] + "}"
    del attr['label']

    graph.node(str(node_cnt), label, attr)
    node_cnt += 1
    gdb_write(node_cnt)
    return node_cnt - 1

def add_dot_edge(graph, f, to, attr):
    graph.edge(str(f), str(to))

def eval_str(s):
    return gdb.parse_and_eval(s)
    
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
            init_dot()
            argv = gdb.string_to_argv(arg)
            v = gdb.parse_and_eval(argv[0])

            if len(argv) > 1 and "debug" in argv:
                logging.basicConfig(filename='debug.log', level=logging.DEBUG)
                getattr(logging, "DEBUG")
                gdb.write("debugging mode")

            cpt_parser(v)
            gdb_write(dot.source)
        except gdb.error, e:
            raise gdb.GdbError(e.message)
        except:
            gdb_write(traceback.format_exc())
            raise

CUBRID_PTNODE_Traversal()
