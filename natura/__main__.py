import sys
from natura import Finder

try:
    from pprint import print as print
except ImportError:
    pass


def main():
    """ This is the function that is run from commandline with `natura` """
    if "--lang" == sys.argv[1]:
        f = Finder(sys.argv[2])
        args = sys.argv[3:]
    else:
        f = Finder()
        args = sys.argv[1:]
    text_string = " ".join(args)
    print(f.findall(text_string))
