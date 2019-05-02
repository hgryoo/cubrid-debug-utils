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

def typecode(n):
    if type(n) is gdb.Value:
        c = n.type.strip_typedefs().code
    elif type(n) is gdb.Type:
        c = n.strip_typedefs().code
    else:
        c = None
    return c

def is_pointer(v):
    c = typecode(v)
    return (c == gdb.TYPE_CODE_PTR)

def is_container(v):
    c = typecode(v)
    return (c == gdb.TYPE_CODE_STRUCT or c == gdb.TYPE_CODE_UNION)

def is_array(v):
    c = typecode(v)
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
    c = typecode(v)
    return (c == gdb.TYPE_CODE_ENUM)
    

def is_primitive(v):
    c = typecode(v)    
    return (c == gdb.TYPE_CODE_INT or
            c == gdb.TYPE_CODE_FLT or
            c == gdb.TYPE_CODE_VOID or
            c == gdb.TYPE_CODE_CHAR or
            c == gdb.TYPE_CODE_BOOL or
            c == gdb.TYPE_CODE_DECFLOAT or
            c == gdb.TYPE_CODE_ENUM)

def is_string(v):
    char_ptr = gdb.lookup_type('char').pointer()
    return str(v.type) == str(char_ptr)

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
         'PT_UNION'     : ['PT_QUERY_INFO', 'query'],
         'PT_EXPR'      : ['PT_EXPR_INFO', 'expr'],
         'PT_FUNCTION'  : ['PT_FUNCTION_INFO', 'function'],
         'PT_VALUE'     : ['PT_VALUE_INFO', 'value'],
         'PT_SPEC'      : ['PT_SPEC_INFO', 'spec'],
         'PT_NAME'      : ['PT_NAME_INFO', 'name']
        }

        self.RESERVED_FUNC = {
         'PT_NODE' : self.next_internal,
         'PT_STATEMENT_INFO' : self.next_PT_STATEMENT_INFO,
         'PT_VALUE_INFO' : self.next_PT_VALUE_INFO,
         'PT_QUERY_INFO' : self.next_PT_QUERY_INFO,
         'PT_SPEC_INFO' : self.next_PT_SPEC_INFO
        }

        self.TYPE_ENUM = make_type_enum("PT_TYPE_ENUM")
        
        self.DEFAULT_FILTER = ["qo_summary", "xasl"]

    def default_filter(self):
        return ["qo_summary", "xasl"]   
 
    def parse_PTNODE_root(self, name, v):
        self.node[name] = {}
        self.parse_internal(self.node[name], [], None, v)

    def next_internal(self, cur_n, f, p, v):
        try:
            next_node = cur_n[str(f.name)] = {}
            self.parse_internal(next_node, [], p, v)
        except:
            gdb_write("error occured in next_internal")

    def next_PT_STATEMENT_INFO(self, cur_n, f, p, v):
        if self.is_pt_node(p):
            node_type = str(p["node_type"])
            try:
                concrete_info_type = None
                if node_type in self.CONCRETE_INFO:
                    concrete_info_type = self.CONCRETE_INFO[node_type]
                # HACK
                if concrete_info_type is None:
                    concrete_info_type = [str(f.type), (str(f.type)).replace("PT_", "").replace("_INFO", "").lower()]
                concrete_info_name = concrete_info_type[1]
                concrete_info = v[ concrete_info_name ]
                info_name = concrete_info_type[0]
                info_node = cur_n['info'] = {}
                
                if info_name in self.RESERVED_FUNC:
                    func = self.RESERVED_FUNC[info_name]
                    func(info_node, concrete_info.type, p, concrete_info)
                else:
                    self.parse_internal(info_node, [] , p, concrete_info) 
            except:
                gdb_write(str(f.name) + ":" + str(f.type) + " has failed to parse for " + node_type)
        else:
            gdb_write("unknown type : " + str(f.type))

    def next_PT_QUERY_INFO(self, cur_n, f, p, v):
        if self.is_pt_node(p):

           node_type = str(p["node_type"])

           filter = []
           if node_type == "PT_SELECT":
                filter.append("union_")
           elif node_type == "PT_UNION":
                filter.append("select")

           q_union = v["q"]
           self.parse_internal(cur_n, filter, v, q_union)
           self.parse_internal(cur_n, ["q"], p, v)

        else:
            gdb_write("unknown type : " + str(f.type))
    
    def next_PT_VALUE_INFO(self, cur_n, f, p, v):
        if self.is_pt_node(p):
            try:
                type_enum = p["type_enum"]

                type_lower = str(type_enum).replace("PT_TYPE_", "").lower()

                t1 = ["logical", "float", "double", "numeric", "integer", "bigint", "smallint"]
                t2 = ["date", "time", "timestamp", "timestamptz", "timestampltz", "datetime", "datetimetz", "datetimeltz"]
                t3 = ["char", "nchar", "bit", "varchar", "varnchar", "varbit"] 

                if type_lower in t1:
                    if not is_nullptr(v["text"]):
                        cur_n["value"] = str(v["text"])
                    else:
                        if type_lower == "float":
                            cur_n["value"] = str(v["data_value"]["f"])
                        elif type_lower == "double":
                            cur_n["value"] = str(v["data_value"]["d"])
                        elif type_lower == "numeric":
                            cur_n["value"] = str(v["data_value"]["str"]["bytes"])
                        elif type_lower == "integer" or type_lower == "logical" or type_lower == "smallint":
                            cur_n["value"] = str(v["data_value"]["i"])
                        elif type_lower == "bigint":
                            cur_n["value"] = str(v["data_value"]["bigint"])

                if type_lower in t2:
                    cur_n["value"] = str(v["date_value"]["str"]["bytes"])

                if type_lower in t3:
                    if not is_nullptr(v["text"]):
                        cur_n["value"] = (v["text"]).string()
                    else:
                        cur_n["value"] = (v["data_value"]["str"]).string()
                cur_n["value_type"] = type_lower

                self.parse_internal(cur_n, ["data_value", "db_value", "text"], p, v)
            except:
                gdb_write("error occured in next_PT_VALUE_INFO")
        else:
            gdb_write("unknown type : " + str(f.type))

    def next_PT_SPEC_INFO(self, cur_n, f, p, v):
        if self.is_pt_node(p):
            try:
                fields = map(lambda x: str(x.name), v.type.fields())
                entity_name = v["entity_name"]
                is_entity = not is_nullptr(entity_name)
                if is_entity and p["partition_pruned"] == 1:
                    fields.remove("flat_entity_list") 
                elif is_entity and not is_nullptr(entity_name["next"]):
                    fields.remove("entity_name")
                elif is_entity:
                    fields.remove("meta_class")
                    fields.remove("only_all")
                    fields.remove("entity_name")
                    fields.remove("partition")
                    fields.remove("except_list")
                elif not is_nullptr(v["derived_table"]):
                    fields.remove("derived_table_type")
                    fields.remove("derived_table")
                    fields.remove("range_var")

                as_attr_list = v["as_attr_list"]
                cte_pointer = v["cte_pointer"]
                if not is_nullptr(as_attr_list) and is_nullptr(cte_pointer) and str(v["derived_table_type"]) != "PT_DERIVED_JSON_TABLE":
                    fields.remove("as_attr_list")

                fields.remove("on_cond")
                fields.remove("using_cond")

                primitives = []
                for name in fields:
                    if is_primitive(v[name]) or is_enum(v[name]):
                        primitives.append(name)

                fields = [i for i in fields if i not in primitives]
                self.parse_internal(cur_n, fields, p, v)
                    
            except:
                gdb_write("error occured in next_PT_SPEC_INFO")
                gdb_write(sys.exc_info())
        else:
            gdb_write("unknown type : " + str(f.type))

    def parse_internal(self, cur_n, filter, p, v):
        cur_n['TYPE'] = str(v.type)
        filter.extend(self.DEFAULT_FILTER)

        fields = v.type.fields()
        for f in fields:
            f_name = f.name
            f_type = f.type

            if str(f.name) in filter:
                continue            

            val = v[f.name]
            if is_nullptr(val):
                continue

            if is_pointer(val):
                try:
                    if is_string(val):
                        cur_n[f.name] = val.string()
                        continue
                    val = val.dereference()
                except:
                    # gdb_write("dereference failed, maybe xasl")
                    continue

            if not is_accessable(val):
                continue

            if str(f.type) in self.RESERVED_FUNC:
                func = self.RESERVED_FUNC[str(f.type)]
                func(cur_n, f, v, val)
            
            elif is_container(val):
                next = cur_n[str(f_name)] = {}
                self.parse_internal(next, [], v, val)

            elif is_primitive(val):
                cur_n[f_name] = str(val)

            elif is_array(val):
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
