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
    
    dt_id = -1
    data_type = v['data_type']
    if not is_null(data_type):
        dt_id = create_pt_node_internal(graph, data_type)
    
    info = v['info']
    concrete_info_type = (str(node_type))[3:].lower()
    gdb_write(concrete_info_type)
    concrete_info = info[concrete_info_type]
    info_id = create_pt_node_info(graph, concrete_info)

    id = add_dot_node(graph, attr)

    add_dot_edge(graph, id, info_id, 'info')
    if not dt_id == -1:
        add_dot_edge(graph, id, dt_id, 'data_type')
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
                    # TODO
                    pass
        elif is_container(val):
            pass
            # TODO
        else:
            # hack
            attr['label'] += "|{" + str(f_name) + "|" + str(val) + "}"

    attr['label'] = attr['label'].replace(',','|')
    attr['label'] = attr['label'].replace('= {', '| {')
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
    dot = Digraph(format='png')
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
    return attr

def add_dot_node(graph, attr):
    global node_cnt
    label = '{' + attr['label'] + '}'
    del attr['label']

    graph.node(str(node_cnt), label, attr)
    node_cnt += 1
    gdb_write(node_cnt)
    return node_cnt - 1

def add_dot_edge(graph, f, to, attr):
    graph.edge(str(f), str(to))

def eval_str(s):
    return gdb.parse_and_eval(s)

class Graph:
    
    def __init__(self, name):
        self.name = name
        self.dot = Digraph(format='png')
        self.dot.body.append("newrank=true")
        
        self.sub_graph = []
        self.node_list = {}
        self.edge_list = {}

    def add_node(self, f_name, path):
        idx = -1
        if not path in sub_graph:
            self.sub_graph.append(path)
        else:
            idx = self.sub_graph.index(path)

        self.node_list[f_name] = idx

    def add_edge(self, start, end, value):
        if start in self.edge_list:
        self.edge_list[start].add(end)

class GraphManager:
    def __init__(self):
        self.graph_dict = {}

    def has_graph(name):
        if name in self.graph_dict:
            return False
        else:
            return True

    def create_graph(name):
        if not name in self.graph_dict:
            self.graph_dict[name] = Graph(name)
            return self.graph_dict[name]
        else:
            gdb_write("there is same graph name")
            return None

    def write_graph(name):
        if name in self.graph_dict:
            return self.graph_dict[name].dot.source
        else:
            return ''
                     
 
class CUBRID_BT_Visualizer(gdb.Command):
    '''
    bt_viz <command> <options>
    '''
    def __init__(self): 
        super(CUBRID_BT_Visualizer, self).__init__(
            'bt_viz',
            gdb.COMMAND_DATA, gdb.COMPLETE_SYMBOL, False)

        self.gm = GraphManager()

    def invoke(self, arg, from_tty):
        try:
            argv = gdb.string_to_argv(arg)

            if len(argv) < 2:
                return

            cmd = argv[0]
            params = argv[1:]

            gdb_write(params)

            if cmd == "create":
                self.create(params)
            elif cmd == "write":
                pass
            elif cmd == "clear":
                pass
            else:
                gdb_write("Unknown command")

        except gdb.error, e:
            raise gdb.GdbError(e.message)
        except:
            gdb_write(traceback.format_exc())
            raise

    def create(self, params):
        if len(params) > 0:
            graph_name = params[0]

            if self.gm.has_graph(graph_name):
                return False

            g = self.gm.create_graph(graph_name)

            backtrace = gdb.execute('bt', to_string=True)
            bt_list = backtrace.splitlines().reverse()

            for f in bt_list:
                spl_in = f.split(' in ')
                spl_at = spl_in[1].split(' at ')

                func_info = spl_at[0].split(' ')
                file_info = spl_at[1].split(':')

                path_list = file_info.split('/')


    def write(self, params):
        pass
        

CUBRID_BT_Visualizer()
