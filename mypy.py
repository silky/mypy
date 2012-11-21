import os
import os.path
import sys

from build import build
from pythongen import PythonGenerator
from errors import CompileError


void main():
    verbose = False
    pyversion = 3
    args = sys.argv[1:]
    while args and args[0].startswith('-'):
        if args[0] == '--verbose':
            verbose = True
            args = args[1:]
        elif args[0] == '--py2':
            pyversion = 2
            args = args[1:]
        else:
            fail('Invalid option {}'.format(args[0]))
    
    if not args:
        fail()
    
    path = args[0]
    
    mainfile = open(path)
    text = mainfile.read()
    mainfile.close()
    
    try:
        # TODO determine directory more intelligently
        # TODO make sure only the current user can access the directory
        output_dir = '/tmp/mypy-xx'
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir, 0o777)
        
        # Parse and type check the program and dependencies.
        trees, symtable, infos, types = build(text, path, False, None, True)
        
        # Translate each file in the program to Python.
        # TODO support packages
        for t in trees:
            if not is_stub(t.path):
                out_path = os.path.join(output_dir, os.path.basename(t.path))
                if verbose:
                    print('LOG: translate {} to {}'.format(t.path, out_path))
                v = PythonGenerator(pyversion)
                t.accept(v)
                outfile = open(out_path, 'w')
                outfile.write(v.output())
                outfile.close()
        
        # Run the translated program.
        # TODO determine path to Python interpreter reliably
        
        a = <str> []
        for arg in args[1:]:
            # TODO escape arguments etc.
            a.append('"{}"'.format(arg))

        cmd = 'python3'
        if pyversion == 2:
            cmd = 'python'
        
        os.system('{} "{}/{}" {}'.format(
                             cmd, output_dir, os.path.basename(path),
                             ' '.join(a)))
    except CompileError as e:
        for m in e.messages:
            print(m)
        sys.exit(2)


def fail(msg=None):
    if msg:
        sys.stderr.write('%s\n' % msg)
    sys.stderr.write('Usage: mypy.py [--verbose] PROGRAM\n')
    sys.exit(1)


def is_stub(path):
    # TODO make the check more precise
    return path.startswith('stubs/') or '/stubs/' in path


# TODO if __name__ == '__main__'
main()