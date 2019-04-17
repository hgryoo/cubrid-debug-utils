import sys
import gdb
import graphviz
import traceback
import logging
import json
import gdb_helper as ghelper

from graphviz import Digraph

def is_pointer(v):
	return (v.type.code == gdb.TYPE_CODE_PTR)

def is_container(v):
	c = v.type.code
	return (c == gdb.TYPE_CODE_STRUCT or c == gdb.TYPE_CODE_UNION)
		
def is_null(v):
	if is_pointer(v):
		target = v.dereference()
		return str(target.address) == '0x0'
	return False
	
class TreeParser():
	def __init__(self):
		self.node = {}
		
		self.CONCRETE_INFO = {
		 'PT_SELECT' : ['PT_QUERY_INFO', 'query'],
		 'PT_EXPR' : ['PT_EXPR_INFO', 'expr']
		}
	
	def parsePTNODE_root(self, name, v):
		self.node[name] = {}
		parsePTNODE_internal(self.node[name], v)
	
	def parsePTNODE_internal(self, cur_n, v):
		fields = v.type.fields()
		for f in fields:
			f_name = f.name
			f_type = f.type
			
			val = v[f_name]
			
			if is_pointer(val) and not is_null(val):
				if self.is_pt_node(val):
					next_pt_node = cur_n[f.type] = {}
					parsePTNODE_internal(next_pt_node, val)
				elif self.is_info_node(val):
					concrete_info_type = self.CONCRETE_INFO[node_type]
					# HACK
					if(concrete_info_type == None):
						concrete_info_type = [f_type, (str(f_type))[3:].lower()]
					
					concrete_info = val[ concrete_info_type[1] ]
					info_name = val[ concrete_info_type[0] ]
					info_node = cur_n[info_name] = {}
					self.parsePTINFO(info_node, concrete_info)
				else:
					pass
			else:
				if is_container(val):
					cur_n[f_name] = str(val)
				else:
					cur_n[f_name] = val
		
		
	def parsePTINFO(self, cur_n, v):
		fields = v.type.fields()
		
		for f in fields:
			f_name = f.name
			f_type = f.type

			val = v[f_name]
			
			if self.is_pt_node(val):
				cur_n[f.type] = {}
				parsePTNODE_internal(
			elif is_pointer(val):
				pass
			else:
				pass
		
	def getPTNODE(self, name):
		return self.node[name]
	
	def is_pt_node(self, v):
		pt_node_type = gdb.lookup_type("PT_NODE")
		if type(v) is gdb.Value:
			return (v.type.__str__() == pt_node_type.__str__())
		else:
			return str(v) == str(pt_node_type)

	def is_info_node(self, v):
		info_node_type = gdb.lookup_type("PT_STATEMENT_INFO")
		if type(v) is gdb.Value:
			return (v.type.__str__() == info_node_type.__str__())
		else:
			return str(v) == str(info_node_type)

class CUBRID_PARSER_Traverser(gdb.Command):
    '''
    cpt <command> <options>
    '''
    def __init__(self): 
        super(CUBRID_PARSER_Traverser, self).__init__(
            'cpt',
            gdb.COMMAND_DATA, gdb.COMPLETE_SYMBOL, False)
		
		self.parser = TreeParser()
		
    def write(self, params):
        if len(params) > 0:
			
				
	def invoke(self, arg, from_tty):
	try:
		argv = gdb.string_to_argv(arg)

		if len(argv) < 2:
			return

		cmd = argv[0]
		params = argv[1:]

		if cmd == "create":
			# self.create(params)
		elif cmd == "write":
			self.write(params)
		elif cmd == "clear":
			pass
		elif cmd == "init":
			# self.init(params)
		elif cmd == "merge":
			pass
		elif cmd == "list":
			# self.list()
		else:
			ghelper.gdb_write("Unknown command")
	except:
        ghelper.gdb_write(traceback.format_exc())
        raise
			
CUBRID_PARSER_Traverser()