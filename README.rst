====
Prep
====

Prep is a pre-deployment configuration generator that works by parsing template
files using a simple syntax.  Variables are loaded in a cascading fashion so
that you can have granular control based both on intended network zone (e.g.
dev or prod), or specific hostnames or subnets (e.g. www, www.prod,
www.prod.example.com).

Overview
~~~~~~~~

When I started developing a large web application in Python, I couldn't find
a simple config generator that wasn't tied to a much larger system (e.g.
CFEngine), or wasn't written for a significantly different platform (e.g.
Capistrano).

I had the following goals in mind:

* Easy to configure, and flexible.
* Simple one-line command to reconfigure every part of my application for any
  deployment environment I chose (specifically:  dev, qa, staging, production).
* Support multiple application pieces (several wsgi apps, nginx, gearman jobs,
  elasticsearch)
* Not interfere with the current deployment system (rsync) or whichever more
  robust one I eventually choose to use.

I think that Prep meets these, though it also has a lot of room for improvement.

Usage
~~~~~

See the included sample files for a working installation::

    cd /path/to/prep/sample/
    prep --dev

Alternately, you can use the long form, and specify the directory name
manually::

    prep --mode=production /path/to/prep/sample/

When you run prep, it scans the entire specified directory tree for files named
**prep.cfg**.  These are standard python ConfigParser files (like Windows INI)
containing the directives described below.

prep.cfg
~~~~~~~~

prep
  - Directives to control how prep should render templates for this directory.
  - At the moment, this only includes the required ``template = simple``.
    Eventually there will be more options and probably even other template
    parsing engines.

vars
  - These are the variables that will be injected into your template files.
  - All values are strings

files
  - List of files to process, specified as ``source path = destination path``
  - Relative path names will be in relation to prep.cfg but you are welcome
    to use absolute pathnames.

pre
  - Items in this section are processed before prep touches any files
  - Currently supports the following commands:

    - run (or run.name1, run.name2, ...)
    - set.NAME (runs a shell command and sets var NAME to its output)

  - Values that look like python repr() data for basic structures will be
    interpreted as such (e.g. ``['item1','item2']`` will be interpreted as a
    list object).

post
  - Identical to **pre** above, but runs after file processing

|

Template interpolation is allowed in **files**, **pre**, and **post** so you
can do things like use the output of a command to set a variable containing
a password value, or send generated files to environment-specific directory
names.

Except for **prep**, you can also create mode- and host- and user-specific
variants of each directive, which will override the common config options
with the conditional one you have provided::

    [vars]
    var1 = val1
    var2 = val2
    var3 = val3

    [vars:mode=dev]
    var1 = dev-val1

    [vars:host=www]
    var2 = www-val2

    [vars:user=root]
    var3 = root-val3

Please see sample/ directory for a set of working examples.

Simple Template Syntax
~~~~~~~~~~~~~~~~~~~~~~

There are only 3 things you can do in the simple syntax.  They are listed below
in order of operation.  You can mix and match as necessary.

Basic logic
-----------

Positive and negative matching against mode or host::

    ##if:mode=dev##
    This content will only exist in the final file
    if prep was invoked with --mode=dev
    ##endif##

    ##if:host!=www##
    This content will only exist in the final file
    if prep was invoked on a host not named www
    ##endif##

    This other content will always be in the final file.

Sorry, no ``else`` clause yet.

Includes
--------

I have included a basic include command.  It looks for the filename first in
the same directory as the file that requested the include, and second in the
directory containing the prep.cfg file currently being acted on.::


    ##inc:logging.inc##

Variables
---------

The whole point of this system is to parse variables into your config files::

    [myapp]
    domain = ##domain##
    port = ##port##

In addition to the variables defined in your prep.cfg file, prep provides the
following variables:

root
    The absolute pathname for the directory containing prep.cfg
user
    $USER from the current shell environment
time
    The current unix epoch timestamp.

Prep will also include any --variable=value pairs provided on the command line
when it was invoked.  These command line arguments will override any values
from prep.cfg.

Download
~~~~~~~~

* https://github.com/ex-nerd/prep
* http://pypi.python.org/pypi/prep/
