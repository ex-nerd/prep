"""
prep
====

Main callable module
"""

__version__ = '0.1.8'

import os, re, sys, time, socket
import subprocess
import ConfigParser

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

_conf_file = 'prep.cfg'
_conf_sections = ['prep', 'pre', 'post', 'files', 'vars']

def prep():
    # Lazy import so setup.py can load the version directly from this module
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mode', nargs='?', help='Preparation mode (can also specify as --MODE)')
    parser.add_argument('-H', '--host', default=socket.gethostname(), nargs='?', help='Hostname to prepare for')
    parser.add_argument('path', default='.', nargs='?', type=_arg_is_dir, help="Path to prepare (default .)")
    (args, unknown_args) = parser.parse_known_args()
    # Attempt "smart" mode detection when no explicit mode has been provided
    for arg in unknown_args[:]:
        if not arg.startswith('--'):
            continue
        # Arbitrary conf override argument
        if '=' in arg:
            (var,val) = arg[2:].split('=')
            setattr(args, var, val)
            unknown_args.remove(arg)
        # single --arg shortcut can be used instead of --mode=arg
        elif not args.mode:
            args.mode = arg[2:]
            unknown_args.remove(arg)
    #print args
    #print vars(args).items()
    #print unknown_args
    #print sys.argv
    #print "-------------------"
    # Need a mode
    if not args.mode:
        parser.error("Please specify --mode=MODE or --MODE")
    # Walk the specified path
    path = os.path.abspath(args.path)
    for (dirpath, dirnames, filenames) in os.walk(path):
        if _conf_file not in filenames:
            continue
        conf = _load_conf(dirpath, args)
        _do_prep(dirpath, conf)

def _do_prep(dirpath, conf):
    #print conf
    os.chdir(dirpath)
    # Load our template handler
    template = None
    if conf['prep']['template'].lower() == 'simple':
        template = SimpleTemplate(conf)
    else:
        raise ValueError('Missing or unknown template type specified in {0} or via --template=TEMPLATE'.format(_conf_file))
    # Process the pre-prep tasks
    _do_pre_post('pre', conf, template)
    # Process files
    for src, dest in conf['files'].items():
        # Parse variables in the names
        src  = template.render(src)
        dest = template.render(dest)
        # Make sure the file exists
        if not os.path.isfile(src):
            raise ValueError('No such file:  {0}'.format(src))
        print "{0} -> {1}".format(src, dest)
        # Render
        data = template.render_file(src)
        # Create target directory path?
        newdir = os.path.dirname(dest)
        if newdir and not os.path.isdir(newdir):
            os.makedirs(newdir)
        # Write out the rendered file
        open(dest, 'w').write(data)
    # Process the post-prep tasks
    _do_pre_post('post', conf, template)

def _do_pre_post(which, conf, template=None):
    """
    Currently only supports the "run" command family.
    @todo more macros: chmod, mkdir, create-file, ???
    """
    for k, v in conf[which].items():
        if k == 'run' or k.startswith('run.') or k.startswith('set.'):
            _run_commands(k, v, conf, template)
        else:
            raise ValueError('Unrecognized "{0}" command "{1}"'.format(which, k))

def _run_commands(name, commands, conf, template=None):
    """Run one or more shell commands"""
    # Set a config value to the result?
    setvar = None
    if name.startswith('set.'):
        setvar = name[4:]
        commands = [commands]
    # Cleanup
    if isinstance(commands, str):
        commands = [commands]
    # Go
    for task in commands:
        if not task:
            continue
        if isinstance(task, str):
            task = [task]
        if template:
            task = map(lambda x: template.render(x), task)
        use_shell = len(task) == 1
        if setvar:
            ret = subprocess.Popen(task, stdout=subprocess.PIPE, shell=use_shell).communicate()[0]
            # Only in 2.7:
            # ret = subprocess.check_output(task)
            conf['vars'] = _smart_merge(conf['vars'], [(setvar, ret.strip())])
        else:
            subprocess.call(task, shell=use_shell)

def _smart_merge(thelist, new):
    """
    We want to maintain the sort order of the configuration value lists, which
    we would lose if we merely wrapped things in dict() or set().  This scans
    the original list, adding or replacing values as necessary.
    """
    if not new:
        return thelist
    # Then scan through the new list, adding or replacing as necessary
    if not isinstance(new, list):
        new = OrderedDict(new).items()
    for k, v in new:
        thelist[k] = v
    return thelist

def _load_conf(dirpath, args):
    parser = ConfigParser.SafeConfigParser(dict_type = OrderedDict)
    parser.read(os.path.join(dirpath, _conf_file))
    conf = OrderedDict()
    for key in _conf_sections:
        try:
            conf[key] = OrderedDict(parser.items(key))
        except ConfigParser.NoSectionError:
            conf[key] = OrderedDict()
    # print repr(conf)
    # Parse conditional subsections
    for section in filter(lambda x: ':' in x, parser.sections()):
        for key in _conf_sections:
            if section.startswith(str(key)+':'):
                if '=' not in section:
                    raise ValueError('Invalid configuration section: {0}'.format(section))
                #print section[len(key)+1:]
                (type,value) = section[len(key)+1:].split('=', 2)
                if type == 'mode':
                    if value.lower() == args.mode.lower():
                        conf[key] = _smart_merge(conf[key], parser.items(section))
                        #print "ADD SECTION "+section
                        #print parser.items(section)
                elif type =='host':
                    if args.host.lower() == value.lower() or args.host.lower().startswith(value.lower() + '.'):
                        conf[key] = _smart_merge(conf[key], parser.items(section))
                        #print "ADD SECTION "+section
                        #print parser.items(section)
                    elif value.startswith('.'):
                        if (args.host.endswith(value) or args.host == value[1:]):
                            conf[key] = _smart_merge(conf[key], parser.items(section))
                            #print "ADD SECTION "+section
                            #print parser.items(section)
                elif type == 'user':
                    if value.lower() == os.environ['USER'].lower():
                        conf[key] = _smart_merge(conf[key], parser.items(section))
                        #print "ADD SECTION "+section
                        #print parser.items(section)
                else:
                    raise ValueError('Invalid configuration section "{0}" in "{1}"'.format(type, section))
    # Expand certain data types for pre and post conf items
    for key in ('pre', 'post'):
        for k, v in conf[key].items():
            if not v:
                continue
            if v[0] in ('"', "'", '(', '[', '{'):
                conf[key][k] = eval(v)
            elif val.title() in ('True', 'False', 'None'):
                conf[key][k] = eval(v.title())
    # Override app-config vars with CLI argument values
    conf['prep'] = _smart_merge(
        conf['prep'],
        filter(lambda x: x[0] in ('template'), vars(args).items())
        )
    # Override conf vars with CLI argument values, and provide some additional
    # real-time values from the environment
    conf['vars'] = _smart_merge(
        conf['vars'],
        filter(lambda x: x[0] not in ('path', 'template'), vars(args).items()) + [
            ('root', dirpath),
            ('user', os.environ['USER']),
            ('time', str(int(time.time()))),
        ]
        )
    # Return
    return conf

#####################################
# Template handlers

class Template(object):
    def __init__(self, conf):
        """
        Note:  We pass in the full conf here because pre/post process can alter
               conf['vars'], so we want to make sure we get those updates.
        """
        self._cache = {}
        self.conf   = conf
    @property
    def vars(self):
        if isinstance(self.conf['vars'], dict):
            return self.conf['vars']
        else:
            return dict(self.conf['vars'])
    def render_file(self, file, stack=None):
        raise NotImplementedError('Override this method in template child classes.')
    def render(self, data, file=None, stack=None):
        raise NotImplementedError('Override this method in template child classes.')

class SimpleTemplate(Template):
    # Compile some re patterns
    re_inc = re.compile(r'##inc:([^#]+)##')
    re_if  = re.compile(r'##if:(\S+)## *\n?(.+?) *##endif## *\n?', re.S)
    re_var = re.compile(r'##([\w\.\-]+)##')
    # Implement the two requisite methods
    def render_file(self, file, stack=None):
        data = open(file, 'r').read()
        return self.render(data, file, stack)
    def render(self, data, file=None, stack=None):
        if not isinstance(stack, list):
            stack = []
        # Define the replacement functions the closure way, so we have "self"
        # Note:  Don't be overzealous trapping exceptions here.  We want these
        #        to raise exceptions if there are missing var definitions, etc.
        def repl_inc(m):
            incfile = m.group(1)
            # No cache.  Render?
            if incfile not in self._cache:
                # Make sure we're not already trying to process this file (recursion)
                if isinstance(stack, list) and incfile in stack:
                    raise ValueError('Recusion loop including {0}'.format(incfile))
                # Check first for the include file relative to the one we are
                # currently rendering
                if file and os.path.exists(os.path.join(os.path.dirname(file), incfile)):
                    incpath = os.path.join(os.path.dirname(file), incfile)
                # If that fails, just assume it's relative to the current conf file
                else:
                    incpath = incfile
                # Render the include
                self._cache[incfile] = self.render_file(incpath, stack = stack + [incfile])
            return self._cache[incfile]
        def repl_if(m):
            if '!=' in m.group(1):
                (var, val) = m.group(1).split('!=')
                neg = True
            else:
                (var, val) = m.group(1).split('=')
                neg = False
            if ',' in val:
                val = val.split(',')
            else:
                val = [val]
            if neg and self.vars[var] not in val:
                return m.group(2)
            if not neg and self.vars[var] in val:
                return m.group(2)
            return ''
        def repl_var(m):
            return self.vars[m.group(1)]
        # Process basic logic
        while True:
            (data, n) = re.subn(self.re_if, repl_if, data)
            if not n:
                break
        # Process includes
        data = re.sub(self.re_inc, repl_inc, data)
        # Process variables
        while True:
            (data, n) = re.subn(self.re_var, repl_var, data)
            if not n:
                break
        # Return
        return data

#####################################
# Utility methods

def _arg_is_dir(path):
    """argparse "type" function to validate a directory path"""
    if os.path.isdir(path):
        return path
    raise argparse.ArgumentTypeError(msg = "{0} is not a directory".format(path))

#####################################
# Main

if __name__ == '__main__':
    prep()

# vim:ts=4:sw=4:ai:et:si:sts=4

