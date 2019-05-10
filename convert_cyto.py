#!/usr/bin/env python
#
from __future__ import unicode_literals 

import sys, argparse, logging, os

import json

class CytoNodeData:
    def __init__(self, id, type):
        self.id = id
        self.type = type
        self.user_data = {}

    def __iter__(self):
        yield "id", self.id
        yield "type", self.type

class CytoEdgeData:
    def __init__(self, id, name, source, target):
        self.id = id
        self.name = name
        self.source = source
        self.target = target
        self.user_data = {}

    def __iter__(self):
        yield "id", self.id
        yield "name", self.name
        yield "source", self.source
        yield "target", self.target

def _decode_list(data):
    rv = []

    try:
        UNICODE_EXISTS = bool(type(unicode))
    except NameError:
        unicode = type(str)

    for item in data:
        if isinstance(item, unicode):
            item = item.encode('utf-8')
        elif isinstance(item, list):
            item = _decode_list(item)
        elif isinstance(item, dict):
            item = _decode_dict(item)
        rv.append(item)
    return rv

def _decode_dict(data):
    rv = {}

    try:
        UNICODE_EXISTS = bool(type(unicode))
    except NameError:
        unicode = type(str)

    for key, value in data.items():
        if isinstance(key, unicode):
            key = key.encode('utf-8')
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        elif isinstance(value, list):
            value = _decode_list(value)
        elif isinstance(value, dict):
            value = _decode_dict(value)
        rv[key] = value
    return rv

class CytoEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, CytoEdgeData):
            return obj.__dict__
        elif isinstance(obj, CytoNodeData):
            return obj.__dict__
        else:
            return json.JSONEncoder.default(self, obj)

def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    else:
        return open(arg, 'r')

nodes_map = {}
edges_map = {}

def parse(input, output):

    data = json.load(input, object_hook=_decode_dict, encoding='utf-8')

    json_root = {}
    nodes = json_root["nodes"] = []
    edges = json_root["edges"] = []

    parse_internal(data, nodes, edges)

    json_str = json.dumps(json_root,
                          indent=4, sort_keys=True,
                          ensure_ascii=False,
                          cls=CytoEncoder)

    output.write(str(json_str))

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
        node = CytoNodeData(id, t)
        nodes.append({"data" : node })
        nodes_map[id] = node

        for k in node_key:
            child = item [ k ]
            child_id = parse_internal(child, nodes, edges)

            edge = CytoEdgeData(id + "_" + child_id, k, id, child_id)
            edges.append({"data" : edge })
            edges_map[id + "_" + child_id] = edge

        for k in value_key:
            node.user_data[k] = item [ k ]

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

    args.infile.close()
    args.outfile.close()


loglevel = logging.DEBUG
main(args, loglevel)
