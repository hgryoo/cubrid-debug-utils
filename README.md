# Development Support Utilities for CUBRID DBMS

This repository provides utilities for supporting the CUBRID DBMS development.
It may include debugging support, visualizing and profiling tools.

## Tools

### Prerequisites

```bash
# CentOS 7
yum install -y epel-release
yum install -y python-pip graphviz

pip install pyyaml
pip install graphviz
```

### GDB Parsing Node Visualizer (cpt.py)


#### Getting Started

```
(gdb) source /location/of/this-repo/cpt.py
(gdb) cpt write <name> *node
```
