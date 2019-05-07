#!/usr/bin/env python
#

import sys, argparse, logging, os

import json

class CytoNodeData:
    def __init__(self, id, type):
        self.id = id
        self.type = type
        self.user_data = {}

    def __iter__(self):
        yield ("id", self.id)
        yield ("type", self.type)
        
        for k, v in self.user_data:
            yield (k, v)

class CytoEdgeData:
     def __init__(self, id, source, target):
        self.id = id
        self.source = source
        self.target = target
        self.user_data = {}

     def __iter__(self):
        for name, attr in self._get_attributes().items():
            if isinstance(attr, MapAttribute):
                yield name, getattr(self, name).as_dict()
            if isinstance(attr, ListAttribute):
                yield name, [el.as_dict() for el in getattr(self, name)]
            else:
                yield name, attr.serialize(getattr(self, name))
        
def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    else:
        return open(arg, 'r')

nodes_map = {}
edges_map = {}

def parse(input, output):
    data = json.load(input)

    json_root = {}
    json_root["elements"] = {}
    nodes = json_root["elements"]["nodes"] = []
    edges = json_root["elements"]["edges"] = []

    parse_internal(data, nodes, edges)

    json_str = json.dumps(json_root,
                          indent=4, sort_keys=True,
                          ensure_ascii=False)

    output.write(unicode(json_str))

def parse_internal(item, nodes, edges):

    node_key = []
    value_key = []

    for k in item.keys():
        if type(item[k]) is dict and "ADDRESS" in item[k]:
            node_key.append(k)
        else:
            value_key.append(k)

    id = None
    t = None
    if "ADDRESS" in value_key:
        id = item["ADDRESS"]
        value_key.remove("ADDRESS")
    
    if "TYPE" in value_key:
        t = item["TYPE"]
        value_key.remove("TYPE")

    if not id is None:
        node = {}
        
        data = CytoNodeData(id, type)
        nodes.append(data)
        nodes_map[id] = data

        for k in node_key:
            child = item [ k ]
            child_id = parse_internal(child, nodes, edges)

            edge = CytoEdgeData(id + "_" + child_id, id, child_id)
            edges.append(edge)
            edges_map[id + "_" + child_id] = edge

        for k in value_key:
            data.user_data[k] = item [ k ]
 
    else:
        pass
        # never happend

    return id
        
    

def main(args, loglevel):
  logging.basicConfig(format="%(levelname)s: %(message)s", level=loglevel)

if __name__ == '__main__':
    parser = argparse.ArgumentParser( 
                                    description = "Does a thing to some stuff.",
                                    epilog = "As an alternative to the commandline, params can be placed in a file, one per line, and specified on the commandline like '%(prog)s @params.conf'.",
                                    fromfile_prefix_chars = '@' )
  # TODO Specify your real parameters here.
    parser.add_argument(
                      "-i",
                      dest="infile",
                      required=True,
                      help = "pass ARG to the program",
                      metavar = "FILE",
                      type=argparse.FileType('r'))
    parser.add_argument(
                      "-o",
                      dest="outfile",
                      required=True,
                      help = "pass ARG to the program",
                      metavar = "FILE",
                      type=argparse.FileType('w'))

    args = parser.parse_args()
  
  # Setup logging
  #if verbose in args:
  #  loglevel = logging.DEBUG
  #else:
  #  loglevel = logging.INFO

    parse(args.infile, args.outfile)

    print "success"
    args.infile.close()
    args.outfile.close()


loglevel = logging.DEBUG 
main(args, loglevel)
