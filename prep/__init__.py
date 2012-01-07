"""
prep
====

Main callable module
"""

__version__ = '0.1.0'

import os, re, sys, time, socket
import subprocess
import ConfigParser
import argparse

_conf_file = '.prep'
_conf_sections = ['prep', 'pre', 'post', 'files', 'includes', 'vars']

def prep():
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mode', nargs='?', help='Preparation mode')
    parser.add_argument('-H', '--host', default=socket.gethostname(), nargs='?', help='Hostname to prepare for')
    parser.add_argument('path', default='.', nargs='?', type=_arg_is_dir, help="Path to prepare (default .)")
    (args, unknown_args) = parser.parse_known_args()
    # Attempt "smart" mode detection when no explicit mode has been provided
    if not args.mode:
        for arg in unknown_args:
            if arg.startswith('--') and '=' not in arg:
                unknown_args.remove(arg)
                args.mode = arg[2:]
                break
    #print args
    #print unknown_args
    #print sys.argv
    #print "-------------------"
    # Walk the specified path
    path = os.path.abspath(args.path)
    for (dirpath, dirnames, filenames) in os.walk(path):
        if _conf_file not in filenames:
            continue
        conf = _load_conf(dirpath, args)
        _do_prep(dirpath, conf)

def _arg_is_dir(path):
    """argparse "type" function to validate a directory path"""
    if os.path.isdir(path):
        return path
    raise argparse.ArgumentTypeError(msg = "{0} is not a directory".format(path))

def _do_prep(dirpath, conf):
    print conf
    os.chdir(dirpath)
    # Process the pre-prep tasks
    _do_pre_post('pre', conf['pre'])
    # Process variables
    pass
    # Process includes
    pass
    # Process files
    pass
    # Process the post-prep tasks
    _do_pre_post('post', conf['post'])

def _do_pre_post(which, items):
    """
    Currently only supports the "run" command.
    @todo Standardize sequential commands like run.2
    @todo natural sort sequential commands (i.e. run.2 < run.10)
    @todo more macros: chmod, mkdir, ???
    """
    for item in items:
        (k, v) = item
        if k == 'run' or k.startswith('run.'):
            _run_commands(v)
        else:
            raise ValueError('Unrecognized "{0}" command "{1}"'.format(which, k))

def _run_commands(commands):
    """Run one or more shell commands"""
    if isinstance(commands, str):
        commands = [commands]
    for task in commands:
        if isinstance(task, str):
            subprocess.call([task])
        else:
            subprocess.call(task)

def _smart_merge(thelist, new):
    """
    We want to maintain the sort order of the configuration value lists, which
    we would lose if we merely wrapped things in dict() or set().  This scans
    the original list, adding or replacing values as necessary.
    """
    if not new:
        return thelist
    # Take note of the placement of the sub-keys in the original list
    keyloc = {}
    for i, item in enumerate(thelist):
        keyloc[item[0]] = i
    # Then scan through the new list, adding or replacing as necessary
    for item in new:
        if item[0] in keyloc:
            #print "REPLACE {0} with {1}".format(thelist[keyloc[item[0]]], item)
            thelist[keyloc[item[0]]] = item
        else:
            #print "ADD {0}".format(item)
            thelist.append(item)
    return thelist

def _load_conf(dirpath, args):
    parser = ConfigParser.SafeConfigParser(allow_no_value=False)
    parser.read(os.path.join(dirpath, _conf_file))
    conf = {}
    for key in _conf_sections:
        try:
            conf[key] = parser.items(key)
        except ConfigParser.NoSectionError:
            conf[key] = []
    #print conf
    # Parse conditional subsections
    for section in filter(lambda x: ':' in x, parser.sections()):
        for key in _conf_sections:
            if section.startswith(str(key)+':'):
                if '=' not in section:
                    raise ValueError('Invalid configuration section: {0}'.format(section))
                #print section[len(key)+1:]
                (type,value) = section[len(key)+1:].split('=', 2)
                if type == 'mode':
                    if value == args.mode:
                        conf[key] = _smart_merge(conf[key], parser.items(section))
                        #print "ADD SECTION "+section
                        #print parser.items(section)
                elif type =='host':
                    if args.host == value or args.host.startswith(value + '.'):
                        conf[key] = _smart_merge(conf[key], parser.items(section))
                        #print "ADD SECTION "+section
                        #print parser.items(section)
                    elif value.startswith('.'):
                        if (args.host.endswith(value) or args.host == value[1:]):
                            conf[key] = _smart_merge(conf[key], parser.items(section))
                            #print "ADD SECTION "+section
                            #print parser.items(section)
                else:
                    raise ValueError('Invalid configuration section "{0}" in "{1}"'.format(type, section))
    # Expand certain data types for pre and post conf items
    for key in ('pre', 'post'):
        for i, item in enumerate(conf[key]):
            if item[1]:
                val = item[1]
                if val[0] in ('"', "'", '(', '[', '{'):
                    conf[key][i] = (item[0], eval(val))
                elif val.title() in ('True', 'False', 'None'):
                    conf[key][i] = (item[0], eval(val.title()))
    # Return
    return conf

def _init():
    pass

if __name__ == '__main__':
    prep()
