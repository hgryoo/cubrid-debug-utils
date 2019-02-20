import sys
import gdb
import graphviz

def is_container(v):
    c = v.type.code
    return (c == gdb.TYPE_CODE_STRUCT or c == gdb.TYPE_CODE_UNION)

def is_pointer(v):
    return (v.type.code == gdb.TYPE_CODE_PTR)

program_name = sys.argv[0]
arguments = sys.argv[1:]
count = len(arguments)

def cpt_parser(s):
    if is_container(s) or is_pointer(s) :
        gdb.write("%s\n" % "container");
    
class CUBRID_PTNODE_Traversal(gdb.Command):
    '''
    print-struct-follow-pointers [/LEVEL_LIMIT] STRUCT-VALUE
    '''
    def __init__(self): 
        super(CUBRID_PTNODE_Traversal, self).__init__(
            'cpt_parser',
            gdb.COMMAND_DATA, gdb.COMPLETE_SYMBOL, False)

    def invoke(self, arg, from_tty):
        try:
            v = gdb.parse_and_eval(arg)
        except gdb.error, e:
            raise gdb.GdbError(e.message)
        cpt_parser(v)

CUBRID_PTNODE_Traversal()
