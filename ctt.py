import os
import sys
import gdb
import graphviz
import traceback
import logging
import io
import json
from graphviz import Digraph

def gdb_write(s):
    gdb.write("%s\n" % s)

def is_pointer(v):
    c = v.type.strip_typedefs().code
    return (c == gdb.TYPE_CODE_PTR)

def is_container(v):
    c = v.type.strip_typedefs().code
    return (c == gdb.TYPE_CODE_STRUCT or c == gdb.TYPE_CODE_UNION)

def is_array(v):
    c = v.type.strip_typedefs().code
    return (c == gdb.TYPE_CODE_ARRAY)

def is_nullptr(v):
    if is_pointer(v):
        return str(v) == '0x0' or str(v) == '0x1'
    return False

def is_accessable(v):
    try:
        str(v)
        return True
    except:
        return False

def is_enum(v):
    c = v.type.strip_typedefs().code
    return (c == gdb.TYPE_CODE_ENUM)
    

def is_primitive(v):
    c = v.type.strip_typedefs().code
    return (c == gdb.TYPE_CODE_INT or
            c == gdb.TYPE_CODE_FLT or
            c == gdb.TYPE_CODE_VOID or
            c == gdb.TYPE_CODE_CHAR or
            c == gdb.TYPE_CODE_BOOL or
            c == gdb.TYPE_CODE_DECFLOAT or
            c == gdb.TYPE_CODE_ENUM)

def check_type(v, name):
    lookup_type = gdb.lookup_type(name)
    if type(v) is gdb.Value:
        return (v.type.__str__() == lookup_type.__str__())
    else:
        return str(v) == str(lookup_type)

def make_type_enum(enum_name):
    enum_typedef = gdb.lookup_type(enum_name)
    node_type = gdb.types.get_basic_type(enum_typedef)
    return gdb.types.make_enum_dict (node_type)

class TreeParser:
    def __init__(self):
        self.node = {}
        
        self.CONCRETE_INFO = {
         'PT_SELECT'    : ['PT_QUERY_INFO', 'query'],
         'PT_EXPR'      : ['PT_EXPR_INFO', 'expr'],
         'PT_FUNCTION'  : ['PT_FUNCTION_INFO', 'function'],
         'PT_VALUE'     : ['PT_VALUE_INFO', 'value'],
         'PT_SPEC'      : ['PT_SPEC_INFO', 'spec'],
         'PT_NAME'      : ['PT_NAME_INFO', 'name']
        }
    
    def parse_PTNODE_root(self, name, v):
        self.node[name] = {}
        self.parse_internal(self.node[name], v)
    
    def parse_PTNODE_internal(self, cur_n, v):

        cur_n['TYPE'] = 'PT_NODE'

        fields = v.type.fields()
        for f in fields:
            f_name = f.name
            f_type = f.type
            
            val = v[f_name]
            if is_nullptr(val):
                continue

            if self.is_pt_node(val):
                next_pt_node = cur_n[str(f_name)] = {}
                self.parse_PTNODE_internal(next_pt_node, val)
            elif self.is_info_node(val):
                concrete_info_type = self.CONCRETE_INFO[str(v["node_type"])]
                # HACK
                if concrete_info_type is None:
                    concrete_info_type = [f_type, (str(v["node_type"]))[3:].lower()]
                    
                if concrete_info_type is not None:
                    concrete_info_name = concrete_info_type[1]
                    concrete_info = val[ concrete_info_name ]
                    info_name = concrete_info_type[0]
                    info_node = cur_n['info [' + info_name + ']'] = {}
                    info_node['TYPE'] = info_name 
                    self.parse_PTINFO(info_node, concrete_info)
                        
            elif is_container(val):
                next = cur_n[str(f_name)] = {}
                self.parse_internal(next, val)
            else:
                cur_n[f_name] = str(val)

    def parse_internal(self, cur_n, v):
        cur_n['TYPE'] = str(v.type)

        fields = v.type.fields()
        for f in fields:
            f_name = f.name
            f_type = f.type
            
            val = v[f_name]
            if is_nullptr(val):
                continue

            if is_pointer(val):
                try:
                    val = val.dereference()
                except:
                    # gdb_write("dereference failed, maybe xasl")
                    continue

            if not is_accessable(val):
                continue

            if self.is_pt_node(val):
                next_pt_node = cur_n[str(f_name)] = {}
                self.parse_internal(next_pt_node, val)
            elif self.is_info_node(val):
                try:
                    node_type = str(v["node_type"])
                    concrete_info_type = None
                    if node_type in self.CONCRETE_INFO:
                        concrete_info_type = self.CONCRETE_INFO[node_type]
                    # HACK
                    if concrete_info_type is None:
                        concrete_info_type = [str(f_type), (str(f_type))[3:].lower()]
                    
                    if concrete_info_type is not None:
                        concrete_info_name = concrete_info_type[1]
                        concrete_info = val[ concrete_info_name ]
                        info_name = concrete_info_type[0]
                        info_node = cur_n['info [' + info_name + ']'] = {}
                        self.parse_internal(info_node, concrete_info)
                except:
                    gdb_write(str(f_name) + ":" + str(f_type) + " has failed to parse for " + str(node_type))
                        
            elif is_container(val):
                next = cur_n[str(f_name)] = {}
                self.parse_internal(next, val)

            elif is_array(val) or is_primitive(val):
                cur_n[f_name] = str(val)
            else:
                gdb_write(str(f_type) + "=>" + str(val))
                # just go inside
                # gdb_write(str(f_type) + "=>" + str(val))

    def parse_PTINFO(self, cur_n, v):
        fields = v.type.fields()
        
        for f in fields:
            f_name = f.name
            f_type = f.type

            val = v[f_name]
            if is_nullptr(val):
                continue
            
            if self.is_pt_node(val):
                next = cur_n[str(f_name)] = {}
                self.parse_PTNODE_internal(next, val)
            elif is_container(val):
                next = cur_n[str(f_name)] = {}
                cur_n[f_name] = str(val)
            else:
                cur_n[f_name] = str(val)
   
    def get_PTNODE(self, name):
        return self.node[name]
    
    def is_pt_node(self, v):
        return check_type(v, "PT_NODE")

    def is_info_node(self, v):
        return check_type(v, "PT_STATEMENT_INFO")
    
class CUBRID_PARSER_Traverser(gdb.Command):
    '''
    cpt <command> <options>
    '''
    def __init__(self):
        super(CUBRID_PARSER_Traverser, self).__init__(
            'cpt',
            gdb.COMMAND_DATA, gdb.COMPLETE_SYMBOL, False)
        
        self.parser = TreeParser()
       

    def init(self, params):
        if len(params) > 1:
            
            path = params[0]
            

        else:
            gdb_write("wrong params")
 
    def write(self, params):
        if len(params) > 1:
            
            name = params[0]
            value = gdb.parse_and_eval(params[1])
            
            if not name in self.parser.node:
            
                self.parser.parse_PTNODE_root(name, value)
                
                os.chdir("..")
                user = os.path.expanduser("~")
                directory = os.path.join(user, "cpt")

                if not os.path.exists(directory): 
                    os.makedirs(directory)

                path = os.path.join(directory , name + ".json")
                with io.open(path, 'w+') as f:
                    json_str = json.dumps(self.parser.node[name],
                                         indent=4, sort_keys=True,
                                         ensure_ascii=False)
                    f.write(unicode(json_str))
            
            else:
                gdb_write("Duplicated name")
            
    def invoke(self, arg, from_tty):
        try:
            argv = gdb.string_to_argv(arg)

            if len(argv) < 2:
                return

            cmd = argv[0]
            params = argv[1:]

            if cmd == "create":
                # self.create(params)
                pass
            elif cmd == "write":
                self.write(params)
            elif cmd == "clear":
                pass
            elif cmd == "init":
                # self.init(params)
                pass
            elif cmd == "merge":
                pass
            elif cmd == "list":
                pass
                # self.list()
            else:
                gdb_write("Unknown command")
        except:
            gdb_write(traceback.format_exc())
            raise
            
CUBRID_PARSER_Traverser()
