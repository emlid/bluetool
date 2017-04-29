import sys


def print_error(*objs):
    objs = [str(obj) for obj in objs]
    sys.stderr.write(", ".join(objs))
    sys.stderr.flush()


def print_info(*objs):
    objs = [str(obj) for obj in objs]
    sys.stdout.write(", ".join(objs))
    sys.stdout.flush()
