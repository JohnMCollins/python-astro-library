# Get columns from a text file, ignoring blank lines

import sys


class Column_error(Exception):
    pass


def col_from_file(f, colnum=0):
    """Process file object given to return array of selected column.
    Ignore blank or incomplete lines."""

    res = []
    for lin in f:
        bits = lin.split()
        try:
            c = bits[colnum]
        except IndexError:
            continue
        res.append(c)
    return  res


def int_col_from_file(f, descr, colnum=0):
    """Same but return integral values"""
    try:
        return  [int(x) for x in col_from_file(f, colnum)]
    except ValueError:
        raise  Column_error("Non numeric column %d value in %s" % (colnum, descr))


def ids_from_file_list(files):
    """Extract ids list of files or numeric ids
    If nothing given, use standard input
    Retrun (idlist, noumber of errors)"""

    idlist = []
    errors = 0

    if len(files) == 0:
        try:
            idlist = int_col_from_file(sys.stdin, "Standard input")
        except Column_error as e:
            print(e.args[0], file=sys.stderr)
            errors += 1
    else:
        for f in files:
            if f.isnumeric():
                idlist.append(int(f))
            else:
                try:
                    fl = open(f)
                except OSError as e:
                    print("Cannot open", f, "error was", e.args[1], file=sys.stderr)
                    errors += 1
                    continue
                try:
                    nl = int_col_from_file.int_col_from_file(fl, f)
                except Column_error as e:
                    print(e.args[0], file=sys.stderr)
                    errors += 1
                    continue
                finally:
                    fl.close()

                idlist += nl

        return (idlist, errors)
