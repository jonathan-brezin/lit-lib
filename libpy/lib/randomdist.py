
import cmdlineparser as clp
import math
import numpy as np
import nputils as npu
import os
import random as rndm
import sysutils as su


_DEFAULTS = {
   'dbg':    "",       # usual debugging output comma-separated list of keys
   'dist':  'uniform', # see https://docs.python.org/3.4/library/random.html for others
   'dtype':  np.float, # NumPy numeric type: see the NumPy.matrix documentation
   'int':    False,    # wants integer values only?
   'lambd':  1.0,      # in case dist is "exponential"
   'max':    32767,    # bound on the value of an individual entry that fits in 16 bits
   'mode':   None,     # for the triangular distribution: no obvious default
   'min':   -32767,    # lower bound on the value of an individual entry
   'mu':     0.0,      # the mean for the normal-like distributions
   'path':   '.',      # locates a directory where any generated files are stored
   'pct':    100.0,    # for random matrices: what percentage of the entries to fill in
   'save':   None,     # the extension to use for the generated file if any.
                       # The default is not to save the matrix at all.
   'sigma':  1.0,      # standard deviation for the normal-like distributions,
   'shape':  None,     # the shape to use for NumPy matrices
}

_DISTRIBUTIONS = { # I wrap some of the "random" module's distributions
   'uniform':     lambda options: lambda: rndm.uniform(options.min, options.max),
   'triangular':  lambda options: lambda: rndm.triangular(options.min, options.max, options.mode),
   'exponential': lambda options: lambda: rndm.expovariate(options.lambd),
   'gaussian':    lambda options: lambda: rndm.gauss(options.mu, options.sigma),
   'logNormal':   lambda options: lambda: rndm.lognormvariate(options.mu, options.sigma),
   'normal':      lambda options: lambda: rndm.normalvariate(options.mu, options.sigma)
}

_PARAMETERS = { # maps distribution names to what parameters they depend on
   'uniform':     ("min", "max"),
   'triangular':  ("min", "max", "mode"),
   'exponential': ("lambd",),
   'gaussian':    ("mu", "sigma"),
   'logNormal':   ("mu", "sigma"),
   'normal':      ("mu", "sigma")
} 

class RandomDist:

   def __init__(self, options):
      for attr in _DEFAULTS: 
         # make sure that self has all possible attributes with some value
         self.__setattr__(attr, su.getvalue(options, attr, _DEFAULTS[attr]))
      if self.dist in _PARAMETERS: 
         parms = _PARAMETERS[self.dist]
         distDescription = "" # strictly for debugging
         for parm in parms:
            value = su.getvalue(options, parm, _DEFAULTS[parm])
            distDescription += "{} = {},". format(parm, value)
         distDescription = self.dist+"(" + distDescription[0:-1] +")"
         self.__str__  = lambda: distDescription
         floatDist = _DISTRIBUTIONS[self.dist](self)
         intOnly   = su.getvalue(options, "int", _DEFAULTS["int"])
         self.dist = lambda: math.floor(floatDist()) if intOnly else floatDist()
      else:
         msg = "'{0}' is not a recognized distribution name."
         raise AttributeError(msg.format(self.dist))
      # Set and vet self.shape: on entry it is either None, a string, a tuple, or an int 
      if self.shape is not None:
         if isinstance(self.shape, str): 
            parts = tuple([int(part) for part in self.shape.split(',')])
         elif isinstance(self.shape, int):
            self.shape = (self.shape,)
         elif not isinstance(self.shape, tuple):
            msg = "Expected a str, tuple, or int, but got {0}"
            raise TypeError(msg.format(su.a_classname(self.shape)))
      self.dtype = npu.numpytype(self.dtype)
      self.generated = ([],[]) if self.save == 'npz' else None


   def setCmdLineArgs(parser):
      defaults = _DEFAULTS
      parser.add_a_flag('-int',   'random integer values only')
      parser.add_a_str('-dbg',     defaults['dbg'],   'turn on debugging output')
      parser.add_a_str('-dist',    defaults['dist'],  'probability distribution to use')
      parser.add_a_str('-dtype',   defaults['dtype'], 'NumPy type name for the entries')
      parser.add_a_str('-shape',   defaults['shape'], 'rowsxcols,... string')
      parser.add_a_float('-lambd', defaults['lambd'], 'for the exponential distribution')
      parser.add_a_float('-max',   defaults['max'],   'upper bound on entries')
      parser.add_a_float('-min',   defaults['min'],   'lower bound on entries')
      parser.add_a_float('-mode',  defaults['mode'],  'mode for triangular distribution')
      parser.add_a_float('-mu',    defaults['mu'],    'mean for normal distribution')
      parser.add_a_float('-pct',   defaults['pct'],   'percentage of entries to fill in')
      parser.add_a_float('-sigma', defaults['sigma'], 'std. dev. for the normal distribution')

   def fromCmdLine():
      args = clp.parse_args(RandomDist, usage="generate sets of random values")
      return RandomDist(args)


   def _size2tuple(size):
      the_tuple = npu.to_shape(size)
      if len(the_tuple) == 1: 
         return the_tuple
      else:
         raise ValueError("Expected an integer 1-tuple, but got {}.".format(the_tuple))

   def list(self, size):
      return [self.dist() for n in range(0, RandomDist._size2tuple(size)[0])]

   def vector(self, size, path=None, ext="npy"):
      vector = np.zeros(RandomDist._size2tuple(size), dtype=self.dtype)
      for n in range(0,len(vector)): vector[n] = self.dist()
      if path != None:
         npu.writearray(path, vector, ext)
      return vector

   def unit_vector(self, shape_info, path=None, ext="npy"):
      shape = npu.to_shape(shape_info)
      vector = np.zeros(shape)
      norm_squared = 0.0
      flat = vector.reshape((npu.sizefromshape(shape),))
      for n in range(0, vector.size):
         vector[n] = x = self.dist()
         norm_squared += x*x
      vector /= math.sqrt(norm_squared)
      if path != None:
         npu.writearray(path, vector, ext)
      return vector



   def randomindex(shape):
      return tuple((rndm.randrange(0, n) for n in shape))

   def sparse_array(self, shape=None, pct=None, path=None, ext="npy"):
      if shape is None: shape = self.shape
      if pct is None: pct = self.pct
      entriesToFill = math.floor((npu.sizefromshape(shape)*pct)/100.0)
      array = np.zeros(shape, dtype=self.dtype)
      for n in range(0, entriesToFill):
         index = randomindex(shape)
         while array[index] != 0:
            index = randomindex(shape)
         newvalue = self.dist()
         while value == 0:
            newvalue = self.dist()
         array[index] = newvalue
      if path != None: npu.writearray(path, array, ext)
      return array

   def matrix(self, shape = None, path=None, ext="npy"):
      if shape is None: shape = self.shape
      matrix = np.zeros(shape, dtype=self.dtype)
      (rows, columns) = shape   
      for i in range(0,rows):
         for j in range(0, columns): matrix[i,j] = self.dist()
      if path != None: npu.writearray(path, matrix, ext)
      return matrix

   def square_matrix(self, dim=None, path=None, ext="npy"):
      shape = (dim, dim) if dim != None else self.shape
      return self.matrix(shape, path, ext)

   def diagonally_dominant_matrix(self, dim=None, pct=None, path=None, ext="npy"):
      shape = (dim, dim) if dim != None else self.shape
      matrix = np.zeros(shape, dtype=self.dtype)
      diagonal = np.zeros(dim, dtype=self.dtype)
      if pct is None: pct = self.pct
      entriesToFill = math.floor((dim*dim*pct)/100.0) - dim
      for n in range(0,dim):
         while diagonal[n] == 0: matrix[n,n] = diagonal[n] = self.dist()
      for n in range(0, entriesToFill):
         i = rndm.randrange(0,dim); j = rndm.randrange(0,dim)
         while matrix[i,j] == 0:
            i = rndm.randrange(0,dim); j = rndm.randrange(0,dim)
         maxAllowed = 1 + min(diagonal[i], diagonal[j]) # m[i,j] in range(1, maxAllowed) ...
         matrix[i,j] = self.dist() % maxAllowed         #     note the "mod" operation here
         while matrix[i,j] == 0:                        #     and we don't want 0's
            matrix[i,j] = self.dist() % maxAllowed
      if path != None: npu.writearray(path, matrix, ext)
      return matrix
      
