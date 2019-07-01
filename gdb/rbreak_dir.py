"""
## rbreak all files in a directory
This method is dirty because it uses the gdb-only command to do the job, but works.
http://stackoverflow.com/questions/29437138/can-gdb-set-break-at-every-function-inside-a-directory
"""
import traceback
import os
import gdb
from gdb.FrameDecorator import FrameDecorator
import itertools

def gdb_write(s):
    gdb.write("%s\n" % s)

class MyFrameDecorator(FrameDecorator):

    def __init__(self, fobj):
        super(self.__class__, self).__init__(fobj)
        self.fobj = fobj

    def function(self):
        frame = self.fobj.inferior_frame()
        name = str(frame.name())

        return name

class MyFrameFilter():

    def __init__(self):
        # Frame filter attribute creation.
        #
        # 'name' is the name of the filter that GDB will display.
        #
        # 'priority' is the priority of the filter relative to other
        # filters.
        #
        # 'enabled' is a boolean that indicates whether this filter is
        # enabled and should be executed.

        self.name = "my_filter"
        self.priority = 100
        self.enabled = True

        # Register this frame filter with the global frame_filters
        # dictionary.
        gdb.frame_filters[self.name] = self

    def filter(self, frame_iter):
        frame_iter = itertools.imap(MyFrameDecorator, frame_iter)

        # Just return the original iterator.
        return frame_iter

class FunctionBreakpoint(gdb.Breakpoint):
    def __init__ (self, spec):
        gdb.Breakpoint.__init__(self, spec)
        self.silent = True

    def stop (self):
        gdb.execute('bt 1')
        return False

class RbreakDir(gdb.Command):
    def __init__(self):
        super(RbreakDir, self).__init__(
            'rb-dir',
            gdb.COMMAND_BREAKPOINTS,
            gdb.COMPLETE_NONE,
            False
        )

    def invoke(self, arg, from_tty):
        try:
            argv = gdb.string_to_argv(arg)

            path = argv[0]
            search_type = argv[1]
            search_list = []

            for i in range(2, len(argv)):
                search_list.append (argv[i])

            for root, dirs, files in os.walk(path):
                for basename in files:
                    if (search_type == 'i' and basename in search_list) or (search_type == 'e' and basename not in search_list):
                        path = os.path.join(root, basename)
                        gdb.execute('rbreak {}:.'.format(path), to_string=True)
            
            bps = gdb.breakpoints()
            for bp in bps:
                loc = bp.location
                bp.delete()
                FunctionBreakpoint(loc)

        except:
            gdb_write(traceback.format_exc())
            raise

RbreakDir()
MyFrameFilter()

# gdb.execute('file multifile/main.out', to_string=True)
# gdb.execute('rbreak-dir multifile/d')
