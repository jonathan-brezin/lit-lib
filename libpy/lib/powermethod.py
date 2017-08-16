#! /usr/bin/env python



import cmdlineparser as clp
import dbg
import math
import numpy as np
import nputils as npu
from randomdist import RandomDist
import re
import sys
import sysutils as su
import time


def _nearest_rotation(v, w):
   best_delta = 4.0
   best_rotation = math.nan
   for n in range(0, v.size):
      try:
         rotation = (v[n]/abs(v[n]))*(abs(w[n])/w[n])
         # print("v[n]={}, w[n]={}, rot={}".format(v[n], w[n], rotation))
         delta  = npu.supnorm(v - (rotation*w))
         if delta < best_delta:
            best_delta = delta
            best_rotation = rotation
      except:
         pass
   return (best_delta, rotation)

class PowerMethodResult:
   def __init__(self, progress, time):
      self.progress = progress
      self.iterations = len(progress.lambdas) - 1
      self.time  = time
      self.absolute_multiplier = math.nan
      self.eigenvalue = math.nan
      self.vector = None
      self.converged = (progress.delta_lambdas[-1] <= progress.pm.length_limit)
      if self.converged:
         self.absolute_multiplier = progress.lambdas[-1]
         if progress.delta_norms[-1] <= progress.pm.two_norm_limit or \
               progress.delta_sups[-1] <= progress.pm.sup_norm_limit:
            self.eigenvalue = self.absolute_multiplier
            self.vector = progress.new
         else: # not a positive eigenvalue: may be negative or complex?
            best_delta, rotation = _nearest_rotation(progress.prior, progress.new)
            if best_delta <= progress.pm.sup_norm_limit:
               self.eigenvalue = self.absolute_multiplier * rotation
               self.vector = progress.new

   def to_str(self, entries_shown=None, perline = 10):
      v = self.vector
      if v is None:
         failurefmt = "failed after {} iterations with multiplier {}"
         failure = failurefmt.format(self.iterations, self.progress.lambdas[-1])
         if not self.converged:
            return failure+" and final delta  length {}".format(self.progress.delta_lambdas[-1])
         else:
            dn = self.progress.delta_norms[-1]
            ds = self.progress.delta_sups[-1]
            return failure+" with final delta norm {} and delta sup {}".format(dn, ds)
      else:
         if entries_shown == None: entries_shown = v.size
         delta = self.progress.delta_lambdas[-1]
         entries = npu.format_array(v, displaylimit=entries_shown,perline=perline)
         msg = "Eigenvalue {} after {} iterations and delta lambda: {}\nentries:[\n{}]\n"
         return msg.format(self.eigenvalue, self.iterations, delta, entries)

   def __str__(self):
      return self.to_str(perline = 10)


class PowerMethodResults:
   def __init__(self, options, path, matrix):
      if not isinstance(matrix, np.ndarray):
         matrix, column_headings, row_headings = npu.readarray(path, options)
         #print("matrix has type {} and is\n{}".format(type(matrix), matrix))
      if (len(matrix.shape) != 2) or (matrix.shape[0] != matrix.shape[1]):
         msg = "Expected a square matrix, but got shape {}".format(matrix.shape)
         raise ValueError(msg)
      self.matrix          = matrix
      self.rows            = matrix.shape[0]
      self.left            = None 
      self.right           = None
      self.qr_eigenvalues  = None 
      self.qr_eigenvectors = None
      self.time2init       = 0.0
      self.qr_time         = 0.0 # elapsed time, if any, spent in QR

   def powermethod_time(self):
      gettime = lambda ev: ev.time if ev != None else 0.0
      return gettime(self.left)  +  gettime(self.right)

   def total_time(self):
      return self.time2init + self.qr_time + self.powermethod_time()

   def to_str(self, entries_shown=None, perline = 10, timeunit=3):
      if self.left == None: firstleft = ""
      else: firstleft = "First left: "+self.left.to_str(entries_shown, perline)
      if self.right == None: firstright = ""
      else: firstright = "First right: "+self.right.to_str(entries_shown, perline)
      if isinstance(self.qr_eigenvalues, type(None)): qr_eigenvalues = ""
      else: 
         qr_eigenvalues = "QR eigenvalues: " + \
            npu.format_array(self.qr_eigenvalues, displaylimit=entries_shown, perline=perline)
      powertime = su.time2IntLiteral(self.powermethod_time(), placesToSave=timeunit)
      totaltime = su.time2IntLiteral(self.total_time(), placesToSave=timeunit)
      unit = su.time_units(timeunit)
      times = "\nPower time: {} {}, total time: {} {}\n".format(
         powertime, unit, totaltime, unit
      )
      return "{}\n{}\n{}\n{}\n".format(firstleft, firstright, qr_eigenvalues, times)

   def __str__(self):
      return self.to_str()



class PowerMethodProgress:
   def __init__(self, pm, first_vector):
      self.pm = pm
      self.size = first_vector.size
      self.shape = first_vector.shape
      self.new = first_vector.reshape((self.size,))
      self.lambdas = [npu.twonorm(self.new)]
      self.new /= self.lambdas[0]
      self.prior = None
      self.delta_lambdas = []
      self.delta_sups = []
      self.delta_norms = []

   def check(self, new_vector):
      if (self.shape != new_vector.shape):
         msg = "Wrong shape: expected={}, got={}"
         raise ValueError(msg.format(self.shape, new_vector.shape))
      self.prior = self.new
      self.new = new_vector.reshape((self.size,))
      new_lambda = npu.twonorm(self.new)
      if new_lambda < self.pm.two_norm_limit:
         msg = "New vector is too close to 0: its 2-norm: {} and sup-norm: {}"
         raise ValueError(msg.format(new_lambda, npu.supnorm(self.new)))
      self.new /= new_lambda    
      relative_delta = abs((self.lambdas[-1]-new_lambda)/new_lambda)
      self.lambdas.append(new_lambda)
      self.delta_lambdas.append(relative_delta)
      delta = self.new - self.prior
      self.delta_sups.append(npu.supnorm(delta))
      self.delta_norms.append(npu.twonorm(delta))
      if "allpow" in self.pm.dbgmgr:
         msg = "{}. progress deltas are norm: {}, sup: {}, lengths: {}"
         formatted = msg.format(
            len(self.delta_norms), self.delta_norms[-1],
            self.delta_sups[-1],self.delta_lambdas[-1]
         )
         self.pm.dbgmgr.dbg("allpow", formatted)
      return (self.delta_norms[-1], self.delta_sups[-1],self.delta_lambdas[-1])


class PowerMethod:
   def getOptionDefaults():
      return {
         'mindrl':  1.0/16384.0,   # quit when (delta length over length) is less than this
         'mind2n':  1.0/16384.0,   # quit when the 2-norm of the delta is less than this 
         'mindsup': 1.0/16384.0,   # quit when the sup-norm of the delta is less than this
         'min_v':   0.001,         # for the coordinates of the random vector
         'max_v':   0.999 ,        #    ditto

         'iter': 10,     # quit after at most this many iterations
         'size': 0,      # number of rows if we are generating a random square matrix
         'both': False,  # get both left and right eigenvectors
         'all': False,   # use QR to compute all of the eigenvalues
         'dbg': "",      # debugging keys: show debug output for these keys
      }

   def _option(self, name):
      try:
         return self.options.__getattribute__(name) 
      except:  # options' keys include all of the options which have defaults
         return self.options[name]

   def __init__(self, options={}, initial_vector=None):
      # fields constraining which computations are done and how they are done
      self.options = su.mergepairs(options, PowerMethod.getOptionDefaults(), clone=True)
      self.options['max']   = self.options['max_v']
      self.options['min']   = self.options['min_v']
      self.random_vector    = RandomDist(self.options)
      self.length_limit     = self._option("mindrl")
      self.two_norm_limit   = self._option("mind2n")
      self.sup_norm_limit   = self._option("mindsup")
      self.max_iterations   = self._option("iter")
      self.iteration_range  = range(1, 1+self.max_iterations)

      # and just in case we need to monitor things:
      self.dbgmgr = dbg.DbgMgr()
      self.dbgmgr.dbg("rd", "vector distribution is {}".format(self.random_vector.__str__()))

   def compute(self, path=None, matrix=None, initial_left=None, initial_right=None):
      start = time.time()
      results = PowerMethodResults(self.options, path, matrix)
      rows = results.rows
      results.time2init = time.time() - start
      if isinstance(initial_left, np.ndarray):
         initial_left = (1.0+0.0j)*initial_left.reshape(rows, 1)
      else:
         initial_left = (1.0+0.0j)*self.random_vector.unit_vector((rows,1))
      try:
         self.compute_largest_eigenvalue(results, initial_left)
         if self._option("both"):
            if isinstance(initial_right, np.ndarray):
               initial_right = (1.0+0.0j)*initial_right.reshape(1, rows)
            elif isinstance(initial_left, np.ndarray):
               initial_right = initial_left.copy().reshape(1, rows)
            else:
               initial_right = (1.0+0.0j)*self.random_vector.unit_vector((1, rows))
            self.compute_largest_eigenvalue(results, initial_right)
         if self._option("all"):
            self.compute_all_eigenvalues_via_qr(results)
      except Exception as exc:
         if self.dbgmgr != None:
            self.dbgmgr.err(str(exc))
            self.dbgmgr.flush()
         raise
      return results


   def compute_largest_eigenvalue(self, results, initial_vector):
      matrix = results.matrix
      wants_left = (initial_vector.shape[0] > 1)
      vector     = initial_vector/np.linalg.norm(initial_vector)
      product    = (lambda m, v: np.dot(m, v)) if wants_left else (lambda m, v: np.dot(v, m))
      self.dbgmgr.dbg("pow", "Iteration over: {} for {}".format(self.iteration_range, vector))
      progress = PowerMethodProgress(self, vector)
      before = time.time()
      for n in self.iteration_range:
         new_vector = product(matrix, vector)
         delta_n, delta_s, delta_l = progress.check(new_vector)
         if (delta_n <= self.two_norm_limit or delta_s <= self.sup_norm_limit) and \
               delta_l <= self.length_limit:
            break
         else:
            vector = new_vector
      result = PowerMethodResult(progress, time.time() - before)
      if wants_left:
         results.left = result
      else:
         results.right = result
      pass_name = "Left multiplying:\n" if wants_left else "Right multiplying:\n"
      self.dbgmgr.dbg("pow", pass_name + str(result))
      return result

   def compute_all_eigenvalues_via_qr(self, results):  
      before = time.time()
      evalues, evectors = np.linalg.eig(results.matrix)
      results.qr_time = time.time() - before
      results.qr_eigenvectors = evectors
      results.qr_eigenvalues = evalues
      if not ("allqr" in self.dbgmgr or "qr" in self.dbgmgr):
         return
      # That is correct: everything from here on down is only for debugging output.
      evs = results.qr_eigenvalues
      max_index = np.argmax(abs(evs))
      evmax = abs(evs[max_index])
      min_index = np.argmin(abs(evs))
      evmin = abs(evs[min_index])
      answer = "The eigenvalue size range is [{}, {}]\n".format(evmin, evmax)
      if "allqr" in self.dbgmgr:
         answer += "Eigenvalues:\n   "+npu.format_array(evs, displaylimit=10)+"\n";\
         vctrs = results.qr_eigenvectors
         answer += "Eigenvectors:\n   "+npu.format_array(vctrs, displaylimit=10)+"\n";          
      largestEV = results.left.eigenvalue
      answer += "The relative difference between power's eignvalue and QR's is"
      answer += "{}".format(abs(largestEV - evs[max_index])/largestEV)
      powervector = results.left.vector
      qrvector = results.qr_eigenvectors[max_index]
      qrvector.shape = powervector.shape
      (diff, r) = _nearest_rotation(qrvector, powervector)
      msg = "The difference in the two eigenvectors, power's - eig's, is\n{}"
      self.dbgmgr.dbg("qr", msg.format(npu.format_array(diff, displaylimit=10)))
      normmsg = "\nThe 2 norm of this difference is {} and the sup norm is {}."
      norm = npu.twonorm(diff)
      sup  = npu.supnorm(diff)
      self.dbgmgr.dbg("qr", normmsg.format(norm, sup))

#############################################################################


   def setCmdLineArgs(parser):
      DEFAULTS = PowerMethod.getOptionDefaults()
      RandomDist.setCmdLineArgs(parser) # do these first so that the path positional is LAST!
      parser.add_a_flag("-all",  "use QR to get all the eignenvalues")
      parser.add_a_flag("-both", "get both left and right vectors")
      parser.add_a_flag("-eig",  "compare with NumPy eig call")
      parser.add_a_flag("-sym",  "generate a symmetric random matrix")

      parser.add_a_float("-mindrl",  DEFAULTS["mindrl"],
         "min acceptable relative length change")
      parser.add_a_float("-mind2n",  DEFAULTS["mind2n"], 
         "min acceptable 2-norm vector change") 
      parser.add_a_float("-mindsup", DEFAULTS["mindsup"],
         "min acceptable sup-norm vector change")
      parser.add_a_float("-min_m", -1023.0,
         "minimum value for random matrix entries")
      parser.add_a_float("-max_m", 1023.0,
         "maximum value for random matrix entries")
      parser.add_an_int("-iter",  DEFAULTS["iter"],
         "quit after at most this many iterations")
      parser.add_an_int("-size", DEFAULTS["size"], 
         "for random matrices, the number of rows, and integer >= 2")

      parser.add_a_str("-np_type", "int16", 
         "for random matrices, the NumPy type for an entry")

      parser.add_an_optional_list("paths", "path(s) to matrix source file(s)")

   def fromCmdLine():
      USAGE = """\
Apply the power method and, optionally, the QR method to a matrix.

The final argument in the call is a (possibly empty) list of paths.  If it is non-empty,
each will be read for a matrix to compute.  If it is empty, a random matrix will be
generated with the number of rows and columns both equal to the value the "-size"
argument.  This random matrix will be made symmetric if "-sym" is one of the arguments.

      """
      options = clp.args_dict(clp.parse_args(PowerMethod, usage=USAGE))
      #if options["dbg"] == "": options["dbg"] = "*"
      pm =  PowerMethod(options)
      paths = options["paths"]
      with dbg.initDbgMgr(low=(options["dbg"] or "")) as dbgmgr:
         if len(paths) > 0:
            for path in paths:
               results = pm.compute(path=path)
               print(str(results))
         else:
            options['max'] = options['max_m']
            options['min'] = options['min_m']
            options['dtype'] = npu.numpytype(options['np_type'])
            matrix_rd = RandomDist(options)
            size = options["size"]
            if (size < 2) or not isinstance(size, int):
               raise ValueError("The size must be an integer >= 2, not {}".format(size))
            matrix = matrix_rd.square_matrix(dim=size)
            if options["sym"]: matrix = (matrix + matrix.transpose())/2
            if size < 10:
               print("Array:\n{}\n".format(npu.format_array(matrix, perline=size)))
            results = pm.compute(matrix=matrix)
            print(results.to_str(entries_shown=100))

if __name__ == '__main__': # we are testing this code from the command line

   PowerMethod.fromCmdLine()
     
