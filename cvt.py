import sys
import gdb
import graphviz
import traceback
import logging

class DotManager:
    def __init__(self):
        self.dot =  Digraph(format='png')

class CUBRID_Variable_Traversal(gdb.Command):
    '''
    cvt <command> <options>
    '''

    def __init__(self):
        super(CUBRID_Variable_Traversal, self).__init__(
            'cvt',
            gdb.COMMAND_DATA, gdb.COMPLETE_SYMBOL, False)

        init_dot()
        init_cub_types()

    def invoke(self, arg, from_tty):
        try:
            argv = gdb.string_to_argv(arg)
            v = gdb.parse_and_eval(argv[0])

            if len(argv) > 2 and "debug" in argv:
                logging.basicConfig(filename='debug.log', level=logging.DEBUG)
                getattr(logging, "DEBUG")
                gdb.write("debugging mode")

        except gdb.error, e:
            raise gdb.GdbError(e.message)
        except:
            gdb_write(traceback.format_exc())
            raise


CUBRID_Variable_Traversal()
