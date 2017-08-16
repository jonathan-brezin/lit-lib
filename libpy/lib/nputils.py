

from functools import reduce
import math
import numpy as np
import os as os
import os.path as osp
import re
import sys
import sysutils as su

def to_shape(shape_info):
   if isinstance(shape_info, str):
      return tuple([int(x) for x in size_info.strip().split(',')])
   elif isinstance(shape_info, int):
      return (shape_info, )
   else:
      return tuple([int(x) for x in shape_info]) # a crude type check

def _mul(x,y):
   return x*y

def sizefromshape(shape_info):
   return reduce(_mul, to_shape(shape_info))

def supnorm(array):
   return np.amax(abs(array))

def twonorm(array):
   if len(array.shape) >= 2:
      return np.linalg.norm(array.reshape((sizefromshape(array.shape),)))
   else:
      return np.linalg.norm(array)

def sameentries(array1, array2):
   return (array1.shape == array2.shape) and (twonorm(array1-array2) == 0)

def isinshape(index, shape):
   if isinstance(index, int): index = [index]
   rank = len(shape)
   if len(index) != rank: return False
   for n in range(0, rank):
      if (index[n] >= shape[n]) or (index[n] < 0):
         return False
   return True

def index2entry(index, array):
   if isinstance(index, int): index = [index]
   if not isinshape(index, array.shape):
      msg = "Array has shape {}, so {} is not valid index"
      raise TypeError(msg.format(array.shape, index))
   working = array
   for k in index:
      working = working[k]
   return working

def entry_iter(array):
   rank = len(array.shape)
   nextindex = np.zeros(rank, dtype = int)
   working_n = rank-1
   while isinshape(nextindex, array.shape):
      rv = index2entry(nextindex, array)
      bumped = nextindex[working_n] + 1
      if bumped < array.shape[working_n]:
         nextindex[working_n] = bumped
         yield rv
      elif working_n > 0:
         for k in range(working_n, rank):
            nextindex[k] = 0
         working_n -= 1
         nextindex[working_n] += 1
         working_n = rank-1
         yield rv
      else:
         raise StopIteration()

def index_iter(shape):
   rank = len(shape)
   nextindex = np.zeros(rank, dtype = int)
   working_n = rank-1
   while isinshape(nextindex, shape):
      rv = nextindex.copy()
      bumped = nextindex[working_n] + 1
      if bumped < shape[working_n]:
         nextindex[working_n] = bumped
         yield rv
      elif working_n > 0:
         for k in range(working_n, rank):
            nextindex[k] = 0
         working_n -= 1
         nextindex[working_n] += 1
         working_n = rank-1
         yield rv
      else:
         raise StopIteration()

MACHINE_EPSILON = np.finfo(np.float).eps

def asunitnorm(array, tolerance = None):
   if tolerance is None:
      tolerance = max(array.size, 128)*MACHINE_EPSILON 
   norm = twonorm(array)
   if norm < tolerance:
      raise ValueError("Array norm, {:g} too near zero to normalize.".format(norm))
   else:
      return array/norm

def _nth_index(n, shape):
   # in the size check, a shape with one or more zeros--e.g. (3,0,1)--will have size
   # 0, and hence will cause the error to be raised, because such an array must be
   # empty.
   if not isinstance(n, int):
      ValueError("Expected an integer, but got {}".su.a_classname(n))
   elif n < 0 or n >= sizefromshape(shape):
      msg = "{}-th entry requested, but there are only {}."
      raise ValueError(msg.format(n, sizefromshape(shape)))
   raw_list = [0 for k in range(0, len(shape))]
   for k in range(len(shape)-1, -1, -1):
      coord = n % shape[k]
      raw_list[k] = coord
      n = (n - coord)//shape[k]
      if n == 0: return tuple(raw_list)

def _format(array, begins, ends, perline, formatter, separator, ender):
   total = begins+ends
   available = array.size
   if available > total:
      use = total
   else: # we can display the whole array
      begins = available
      ends = 0
      use = available
   shape_in = array.shape
   array.shape = (array.size,)
   left = ""
   for n in range(0, begins):
      suffix = ender if (n+1) % perline is 0 else separator
      array_n = array[n]
      if isinstance(array_n, complex) and array_n.imag == 0.0:
         array_n = array_n.real 
      left += formatter.format(_nth_index(n,shape_in),array_n)+suffix
   left_trimmed = left if left.endswith(ender) else left[0:-len(separator)]
   right = ""
   first = array.size - ends
   for m in range(first, array.size):
      suffix = ender if (m-first+1) % perline is 0 else separator
      array_m = array[m]
      if isinstance(array_m, complex) and array_m.imag == 0.0:
         array_m = array_m.real 
      right += formatter.format(_nth_index(m, shape_in),array_m)+suffix
   right_trimmed = right[0:-len(ender)] if right.endswith(ender) else right[0:-len(separator)]
   array.shape = shape_in
   if begins > 0:
      if ends > 0:
         if use<=perline:
            between = "{0}...{0}".format(separator)  
         elif left.endswith(ender):
            between = "  ...{0}".format(ender)
         else:
            between = "{1}...{0}   ...{0}".format(ender, separator)
         return left_trimmed+between+right_trimmed
      elif left_trimmed.endswith(ender):
         return left_trimmed[0:-len(ender)]
      else: return left_trimmed
   else:
      return right_trimmed

def format_arrayhead(
      array, displaylimit=None, perline=1, formatter="{1:g}", separator=' ', ender="\n"
   ):
   if displaylimit is None: displaylimit = array.size
   return _format(array, displaylimit, 0, perline, formatter, separator, ender)

def format_arraytail(
      array, displaylimit=None, perline=1, formatter="{1:g}", separator=' ', ender="\n"
   ):
   if displaylimit is None: displaylimit = array.size
   return _format(array, 0, displaylimit, perline, formatter, separator, ender)

def format_array(
      array, displaylimit=None, perline=1, formatter="{1:g}", separator=' ', ender="\n"
   ):
   if displaylimit is None:
      return _format(array, array.size, 0, perline, formatter, separator, ender)
   else:
      begins = math.ceil(displaylimit/2)
      ends = displaylimit - begins
      return _format(array, begins, ends, perline, formatter, separator, ender)


_TYPENAME2TYPE = {
   'bool_': np.bool_,      # Boolean (True or False) stored as a byte
   'int_': np.int_,        # Default integer type (= C long; normally int64 or int32)
   'intc': np.intc,        # Identical to C int (normally int32 or int64)
   'intp': np.intp,        # Integer for indexing (= C ssize_t; normally int32 or int64)
   'int8': np.int8,        # Byte (-128 to 127)
   'int16': np.int16,      # Integer (-32768 to 32767)
   'int32': np.int32,      # Integer (-2147483648 to 2147483647)
   'int64': np.int64,      # Integer (-9223372036854775808 to 9223372036854775807)
   'uint8': np.uint8,      # Unsigned integer (0 to 255)
   'uint16': np.uint16,    # Unsigned integer (0 to 65535)
   'uint32': np.uint32,    # Unsigned integer (0 to 4294967295)
   'uint64': np.uint64,    # Unsigned integer (0 to 18446744073709551615)
   'float_': np.float_,    # Shorthand for float64.
   'float16': np.float16,  # sign bit, 5 bits exponent, 10 bits mantissa
   'float32': np.float32,  # Sign bit, 8 bits exponent, 23 bits mantissa
   'float64': np.float64,  # Sign bit, 11 bits exponent, 52 bits mantissa
   'complex_': np.complex_,    # Shorthand for complex128.
   'complex64': np.complex64,  # Complex number: two 32-bit floats
   'complex128': np.complex128 # Complex number: two 64-bit floats
}

_FORMAT_DICTIONARY = {
   'b': "d",   # boolean--should be 0 or 1?
   'c': "e",   # complex number: a pair of floating-point numbers
   'f': "e",   # floating point number
   'i': "d",   # decimal integer
   'u': "u"    # unsigned (ie non-negative) decimal integer
}

def numpytype(strOrType):
   return _TYPENAME2TYPE[strOrType] if isinstance(strOrType, str) else strOrType

def typename(strOrType):
   return strOrType if isinstance(strOrType, str) else strOrType.name

def typeformat(strOrType):
   name = typename(strOrType)
   return  _FORMAT_DICTIONARY[name[0]]

def typefromvalue(value):
   if isinstance(value, int): return np.int32
   elif isinstance(value, float): return np.float64
   elif isinstance(value, complex): return np.complex128
   elif isinstance(value, bool): return np.bool_
   else:
      msg = "Unsupported numpy type for value {} of type {}"
      raise ValueError(msg.format(value, type(value)))


def readarray(path, options={}):
   ignore, basetype = osp.splitext(path)
   if basetype.startswith('.np'):
      if basetype.startswith('.npz#'): # field name in the loaded file's dict
         namestart = 5 + path.rfind('.npz#')
         path = path[0:namestart+4]
         name = path[namestart:]
         return (np.load(path)[name], [], [])
      else:
         return (np.load(path), [], [])
   elif basetype == ".csv":
      return readcsv(path, options)
   elif basetype == ".tbl": 
      return readtable(path, options)
   else:
      raise ValueError("Unexpected file type, '{}', for a matrix".format(basetype))

def writearray(path, array, ext="npy", **kwargs):
   path, ext = _resolve_basename(path, array, ext)
   if ext == '.npy':
      np.save(path, array, **kwargs)
   elif ext == '.csv':
      writecsv(path, array, **kwargs)
   elif ext == '.tbl':
      writetable(path, array, **kwargs)
   else:
      raise ValueError("Unexpected extension, '{}', for array path.".format(ext))



def optiondefaults():
   return {
      "shape"  : None,    # same meaning as for an ndarray
      "dtype"  : "int32", # again: same meaning as for an ndarray
      "sep"    : '|',     # a single character that is the field separator
      "dbgnpu" : False,   # show debugging printouts?
                          # the two below are needed only for readtable/writetable
      "rskip"  : 0,       # the number of heading rows to skip
      "cskip"  : 0        # the number of heading columns to skip
   }
_PATH_PARM_RE = re.compile("([^?]+)(\?([^?]+))?$")
_BASEPATTERN = re.compile("array_([x\d]+)\.(\w+)\.(\w+)\.(\w+)")

def _parseparms(path, options):
   defaults = optiondefaults()
   (path, ignore, parms) = _PATH_PARM_RE.match(path).groups()
   basename = osp.basename(path)
   match = _BASEPATTERN.match(basename)
   local_options = {}
   if match != None:
      shape, dtype, ignore = match.groups()
      local_options["shape"] = shape
      local_options["dtype"] = dtype
   if parms != None:
      _parseurlparms(parms, local_options, defaults)
   su.mergepairs(local_options, options)
   su.mergepairs(local_options, defaults)
   return path, local_options

def _readfirstline(f, options, defaults):
   line = f.readline()
   _parseurlparms(line[2:].lstrip(), options, defaults)
   # translate string values to their desired types:
   if isinstance(options['shape'], str):
      options['shape'] = tuple([int(n) for n in options['shape'].split('x')])
   else:
      # make sure (a) value is a tuple, and (b) entries are integers
      options['shape'] = tuple([int(n) for n in options['shape']])
   options['dtype'] = numpytype(options['dtype'])
   if not isinstance(options['dtype'], type):
      msg = "expected valid NumPy data type, got '{}'"
      raise ValueError(msg.format(options['dtype']))
   options['rskip'] = int(options['rskip'])
   options['cskip'] = int(options['cskip'])
   options["dbgnpu"] = su.asboolean(options['dbgnpu'])
   return f.readline() if line.startswith("#?") else line   

def _parseurlparms(urlparms, local_options, defaults):
   # urlparms ?key=value&key=value...
   parms = urlparms.rstrip().split('&')
   if defaults["dbgnpu"]: print("parms is '{}'".format(parms))
   for parm in parms:
      if defaults["dbgnpu"]: print("parm is '{}'".format(parm))
      (name, value) = parm.split('=')  # 
      if name in defaults:
         oldvalue = local_options[name]
         default = defaults[name] 
         if name in local_options and oldvalue != default and oldvalue != value:
            msg = "WARNING: {} is '{}' in the path, but '{}' in the parameters"
            print(msg.format(name, oldvalue, value), file=sys.stderr)
         #print("'{}' --> '{}'".format(name, value))
         local_options[name] = value
      elif defaults["dbgnpu"]: # ignore ???
         print("Unexpected option in the path parameters: '{}'".format(name))
         print(defaults)
   return local_options

def readtable(path, options={}):
   path, options = _parseparms(path, options)
   with open(path) as f:
      line = _readfirstline(f, options, optiondefaults())
      if options["dbgnpu"]: print("line after first is '{}'".format(line))
      separator = options['sep']
      column_headings = []
      row_headings = []
      # ignore any header lines to get to the first line of data
      first_data_column = options['cskip']
      for n in range(0, options['rskip']):
         headings = line.strip().split(separator)
         column_headings.append(headings[first_data_column:])
         line = f.readline()
         if options["dbgnpu"]: print("headings {}: '{}'".format(n, line))
      # read the first row containing real data and use it to determine the matrix
      # size, if the options do not already do that.
      row = line.strip().split(separator)
      if options['dbgnpu']:
         msg = "Matrix starts at column {}; separator: '{}'" 
         print(msg.format(first_data_column, separator))
         print("First row: {}".format(row))
      fields_per_line = len(row)
      cols = fields_per_line - first_data_column
      shape = options['shape']
      if shape != None: 
         expected = shape[1] if len(shape) > 1 else shape[0]
         if cols != expected:
            msg = "Expected {} data columns, but first line has {}"
            raise ValueError(msg.format(expected,cols))
         rows = shape[0] if len(shape) > 1 else 1
      else:
         rows = cols
         shape = (cols, cols)
         print("WARNING: no shape specified: {} assumed.".format(shape),file=sys.stderr)
      if options['dbgnpu']: print("{} data fields in the first row.".format(cols))
      data_range = range(first_data_column, fields_per_line)

      # allocate and fill in the matrix
      entrytype = options["dtype"]
      matrix    = np.zeros(shape, dtype=entrytype)

      # we've already read the first row
      if first_data_column > 0: 
         row_headings.append(row[0:first_data_column])
      for j in data_range:
         matrix[0, j-first_data_column] = entrytype(row[j].strip()) 

      # now read the remaining rows
      i = 1 # next row to update
      while i < rows:
         line = f.readline()
         if options["dbgnpu"]: print("row {}: {}".format(i, line))
         if len(line) == 0:
            raise IOError("{} rows found at EOF, but {} were expected".format(i,rows))
         row = line.strip().split(separator)
         if len(row) != fields_per_line:
            msg = "{} fields found in row {}, but {} were expected"
            raise IOError(msg.format(len(row), i, cols))
         if first_data_column > 0:
            row_headings.append(row[0:first_data_column])
            for j in data_range:
               matrix[i, j-first_data_column] = entrytype(row[j].strip())
         i += 1
   return (matrix, column_headings, row_headings)

def readcsv(path, options={}):
   path, options = _parseparms(path, options)
   if options["dbgnpu"]: print("options before: {}".format(options))
   with open(path, 'rt') as f:
      line = _readfirstline(f, options, optiondefaults())
      separator = options['sep']
      shape = options['shape']
      totalsize = sizefromshape(shape)
      entrytype = options['dtype']
      array = np.zeros((totalsize,), dtype=entrytype)
      n = 0
      headers = []
      while len(line) > 0 and line[0] == '#':
         headers.append(line[1:])
         line = f.readline()
      while len(line) > 0 and line[0] != '#':
         if line != "\n":
            for entry in line.split(separator):
               array[n] = entrytype(entry)
               n += 1
         line = f.readline()
      footers = []
      while len(line)>0:
         footers.append(line[1:])
         line = f.readline()
      if n != totalsize:
         raise ValueError("Read {} entries, but expected {}".format(n, totalsize))
      return (array.reshape(shape), headers, footers)

def _resolve_basename(path, array, ext):
   if not osp.isdir(path):
      (ignore, actual_ext) = osp.splitext(path)
      if len(actual_ext) == 0:
         actual_ext = ext
      return (path, actual_ext)
   else:
      if not path.endswith(os.sep): path += os.sep
      shape_str = 'x'.join([str(n) for n in array.shape])
      formatString = "{0}array_{1}{2}{3}{2}{4}{2}{5}"
      entrytype = typename(numpytype(kind) if kind != None else array.dtype)
      timestamp = su.now2IntLiteral(36)[-4:]
      resolved = formatString.format(
         path, shape_str, os.extsep, entrytype, timestamp, ext
      )
      return (path, ext)

def writetable(path, matrix, rowheaders=None, colheaders=None, sep='|', selfid=True):
   if len(matrix.shape) == 1:
      matrix = matrix.reshape(1, matrix.shape(0))
   elif len(matrix.shape) != 2:
      raise TypeError("Expected a vector or matrix, but got shape {}".format(shape))
   path, ignore = _resolve_basename(path, matrix, "tbl")
   (rows, cols) = matrix.shape
   if rowheaders is None: rskip = 0
   else:
      shape = rowheaders.shape
      rskip = 1 if len(shape) == 1 else shape[0]
   if colheaders is None: cskip = 0
   else:
       shape = colheaders.shape
       cskip = 1 if len(shape) == 1 else shape[1]
   entrytype = typename(matrix.dtype)
   formatString = "{0:"+typeformat(entrytype)+"}"
   with open(path, "wt") as f:
      if selfid:
         firstlinefmt = "#? shape={}x{}&rskip={}&cskip={}&dtype={}&sep={}\n"
         f.write(firstlinefmt.format(rows, cols, rskip, cskip, entrytype, sep))
      if rskip != 0:
         f.write(sep.join([str(x) for row in rowheaders for x in row])+"\n")
      if cskip == 0:
         for row in matrix:
            fwrite(sep.join([formatString.format(x) for x in row])+"\n" )
      else:
         for n in range(0, rows):
            headers = sep.join([str(x) for x in colheaders[n]])
            the_row = sep.join([formatString.format(x) for x in matrix[n]])
            f.write(sep.join([headers, the_row]) + "\n")

def writecsv(path, array, headers="", footers="", perline=10, sep='|', selfid=True):
   path, ignore = _resolve_basename(path, array, "csv")
   entrytype = typename(array.dtype)
   formatString = "{0:"+typeformat(entrytype)+"}"
   shape = array.shape
   if len(shape)==1:
      rows = 1
      cols = array.size 
   else:
      rows = shape[0]
      cols = shape[1]
   reshaped = array.reshape((array.size,))
   with open(path, "wt") as f:
      if selfid:
         f.write("#? shape={}x{}&dtype={}\n".format(rows, cols, entrytype))
      if len(headers) > 0:
         for line in headers.split("\n"):
            f.write("#"+line+"\n")
      n = 0
      while n < array.size:
         next_n = n + perline
         slice_n = reshaped[n : next_n] 
         f.write(sep.join([formatString.format(x) for x in slice_n])+"\n" )
         n = next_n
      if len(footers) > 0:
         for line in footers.split("\n"):
            f.write("#"+line+"\n")
