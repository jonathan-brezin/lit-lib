
from collections import namedtuple
from inspect import getmro
import re
import sys
import time


def hierarchyFor(objOrType):
   if isinstance(objOrType, type):
      return getmro(objOrType)
   else:
      return getmro(type(objOrType))

def owndir(aValue):
   return [s for s in dir(aValue) if not re.match("^__.*__$", s)]

def pubdir(aValue):
   return [s for s in dir(aValue) if not re.match("^_.*", s)]


from copy import copy
def mergepairs(tgt, src, clone=False):
   if not clone:
      actualTgt = tgt
   else:
      try:
         actualTgt = copy(tgt)
      except:
         actualTgt = type(tgt)()
         for key in tgt: actualTgt[key] = tgt[key]
   for key in src:
      if key not in actualTgt: actualTgt[key] = src[key]
   return actualTgt


def getattribute(owner, string, defaultValue=None):
   return getattr(owner, string, defaultValue)

def getitem(owner, key, defaultValue=None):
   return owner[key] if key in owner else defaultValue

def getvalue(owner, string, defaultValue=None):
   try: 
      return owner.__getattribute__(string) 
   except AttributeError: 
      try:
         return owner.__getitem__(string)
      except:
         return defaultValue

def isindexable(anObject, anIndex=None):
   try:
      anObject.__class__.__getattribute__("__getitem__")
   except AttributeError:
      return False
   if anIndex is None:
      return True
   try: # check that the index type is acceptable
      dummy = anObject[anIndex]
      return True
   except TypeError:
      return False
   except:
      return True

def isiterable(anObject):
   try:
      dummy = iter(anObject)
      return True
   except TypeError:
      try:
         dummy = iter(anObject, None)
         return True
      except TypeError:
         return False
   except:
      return False

def reverse_lookup(mapping):
   reverse = {}
   for key in mapping:
      reverse[mapping[key]] = key 
   return reverse

def harden(anObject, publicOnly=True, nonCallable=True, cleanup=False):
   rawAttrList = pubdir(anObject) if publicOnly else owndir(anObject)
   if nonCallable:
      rawAttrList = list(filter(lambda name: not callable(anObject.__dict__[name]), rawAttrList))
   badList = list(filter(lambda x: not x.isidentifier(), rawAttrList))
   if len(badList) == 0:
      attrList = rawAttrList
   elif cleanup:
      attrList = list(filter(lambda x: x.isidentifier(), rawAttrList))
   else:
      raise ValueError("Attribute names found that are not identifiers:\n  {}".format(badList))
   attrNames = ",".join(attrList)
   attrValues = [anObject.__dict__[name] for name in attrList]
   classname = anObject.__class__.__name__
   typeName = classname+"_obj"
   tupleType = namedtuple(typeName, attrNames)
   return tupleType(*attrValues)


from math import floor

def float_components(aNumber):
   if aNumber == 0: return (1,0,0)
   if aNumber < 0:
      sign = -1; aNumber = -aNumber
   else:
      sign = 1
   rest = aNumber
   order = 0
   while rest >= 10.0:
      order += 1
      rest /= 10.0
   while rest < 1:
      order -= 1
      rest *= 10.0
   return(sign*rest, order)

_BASE36_DIGITS = '0123456789abcdefghijklmnopqrstuvwxyz'
def str2int(raw, radix=None):
   lowered = raw.lower()
   if lowered[0] == "-":
      positive = False
      lowered = lowered[1:]
   else:
      positive = True
   if lowered[0] == '0':
      if lowered[1] == 'x':
         answer = int(lowered[2:], 16)
      elif lowered[1] == 'b':
         answer = int(lowered[2:], 2)
      else:
         answer = int(lowered[1:], 8)
   elif 'r' in lowered and radix==None: # eg "xyzr36"
      finalr = lowered.rfind("r")
      value = lowered[0:finalr]
      radix  = int(lowered[finalr+1:])
      answer = int(value, radix)
   else:
      answer = int(lowered, 10 if radix==None else radix)
   return answer if positive else -answer

def int2str(n, base=10):
   if base is 10:
      return str(n)
   elif type(base) is not int or base < 2 or base > 36:
      raise Exception("Illegal base, "+str(base)+". Only 2 <= base <= 36 is implemented.")
   elif type(n) is not int:
      if type(n) is not float:
         raise Exception("int2str expects n to be an integer, but got {0}".format(type(n)))
      elif n == floor(n): n = int(n)
      else: raise Exception("int2str expects n to be an integer, but got "+str(n)) 
   sign = (n < 0)
   answer = []
   while n > 0:           
      # floor, called in the loop below, returns a float. To play safe, convert to int explicitly:
      answer.append(_BASE36_DIGITS[int(n) % base])
      n = floor(n / base)
   if sign: answer.append('-')
   answer.reverse()       # does not return answer... because the reversal is done in place. 
   # Python asks the separator string to create the join so that the argument can be any kind of
   # iterator that yields str values.  
   return ''.join(answer) 

def time2IntLiteral(time_, base=10, placesToSave=0):
   scaleFactor = [1.0,10.0,100.0,1000.0,10000.0,100000.0,1000000.0][placesToSave]
   scaledTime = int(floor(time_ * scaleFactor))
   return int2str(scaledTime, base)

def time_units(placesToSave):
   return [
      "secs", "secs/10", "secs*100", "msecs", "secs*10000", "secs*100000", "mcrsecs"
   ][placesToSave]

def now2IntLiteral(base=10, placesToSave=0):
   return time2IntLiteral(time.time(), base=base, placesToSave=placesToSave)

def now4FileName(dayOnly=False):
   gmt = time.gmtime()
   pad = lambda x: str(x) if x > 9 else "0"+str(x)
   gmtdate = str(gmt.tm_year) + pad(gmt.tm_mon) + pad(gmt.tm_mday)
   if dayOnly:
      return gmtdate
   else:
      gmttime = pad(gmt.tm_hour)+pad(gmt.tm_min)+pad(gmt.tm_sec)
      return gmtdate + "." + gmttime


def aOrAn(string, capitalize=False):
   if len(string) == 0: 
      return ""
   else:
      first = string[0].lower()
      if len(string) == 1:
         firstImpliesAn = first in set(['a', 'e', 'f', 'h', 'i', 'm', 'n', 'o', 'r', 's', 'x'])
      elif first in "aiou":
         firstImpliesAn = True 
      elif first == 'e':
         firstImpliesAn = string[1].lower() != 'u'
      else: firstImpliesAn = False
   return [['a ','an '],['A ','An ']][capitalize][firstImpliesAn] + string

def a_classname(aClassOrInstance):
   theClass = aClassOrInstance if type(aClassOrInstance) is type else aClassOrInstance.__class__
   return aOrAn(theClass.__name__, False)

def A_classname(aClassOrInstance): 
   theClass = aClassOrInstance if type(aClassOrInstance) is type else aClassOrInstance.__class__
   return aOrAn(theClass.__name__, True)

def quote_if_str(value):
   if not isinstance(value, str):
      return value
   else:
      return repr(value)

REG_EXP_STR_AS_RE = re.compile("^re.compile\(.(.*).\)$")
def uncompileRegExp(aRegExp):
   return REG_EXP_STR_AS_RE.match(str(aRegExp)).group(1)


def slice2range(s, min=0, max=None):
   if int is type(s.start):
      start =  s.start if s.start >= 0 else max + s.start
   else:
      start = min
   if int is type(s.stop):
      stop  = s.stop if s.stop >= 0 else max + s.stop
   else:
      stop = max
   step  = s.step if int is type(s.step) else 1
   # print("range is {0} and max was {1}".format(range(start, stop, step), max))
   return range(start, stop, step)

def firstMlastN(alist, m, n):
   all = m + n
   if len(alist) <= m + n:
      return repr(alist)
   left = repr(alist[0:m])[:-1]
   right = repr(alist[-n:])[1:]
   return left+", ..., "+right



_TRUE_ = set(
   ("yes", "si", "oui", "ja", "true", "vrai", "wahr", "cierto", "vero", "ok", "on", "1", 1, True)
)
_FALSE_ = set(
   ("no", "non", "nein", "false", "faux", "falsch", "falso", "off", "0", 0, None, False)
)

def asboolean(value):
   global _TRUE_, _FALSE_
   if value in _TRUE_:
      return True
   elif value in _FALSE_:
      return False
   elif type(value) == str:
      lowered = value.lower()
      if lowered in _TRUE_:
         return True
      elif lowered in _FALSE_:
         return False
      else:
         raise ValueError("'{0}' is not a recognized Boolean literal".format(value))
   else:
      msg = "argument type, '{0}', is not legal : use str or bool, or values None, 0, or 1"
      raise ValueError(msg.format(valuetype))

def sameboolean(this, that):
   try:
      left = asboolean(this)
      right = asboolean(that)
      return left is right
   except ValueError:
      return False
         
def addBooleanTerms(trueOrFalse, *terms):
   global _TRUE_, _FALSE_
   lowered = set([((isinstance(x,str) and x.lower()) or x) for x in terms])
   if trueOrFalse:
      _TRUE_ |= lowered
   else:
      _FALSE_ |= lowered

def delBooleanTerms(*terms):
   global _TRUE_, _FALSE_
   lowered = set([((isinstance(x,str) and x.lower()) or x) for x in terms])
   _TRUE_ -= lowered
   _FALSE_ -= lowered


from blist import *
_collection_types = set((blist, btuple, list, set, sortedlist, sortedset, tuple))

def flatten(a_list, *, depth=1, types=None):
   global _collection_types
   if types is None:
      types = _collection_types
      arg_type = type(a_list)
      if not (arg_type in types):
         types.add(arg_type)
   do_not_stop = True # true ==> we may still have some lists to expand
   if depth is None: depth = sys.maxsize
   while depth > 0 and do_not_stop:
      do_not_stop = False
      n = len(a_list) - 1
      while n >= 0:
         item = a_list[n]
         if type(item) in types:
            del a_list[n]
            m = n
            for stuff in item:
               a_list.insert(m, stuff)
               m += 1
            do_not_stop = True
         n -= 1
      depth -= 1


def DOES_NOT_IMPLEMENT_ASSIGNMENT(obj):
   msg = A_classname(obj) + " is read-only. It does not implement any form of assignment"
   raise NotImplementedError(msg)

def DOES_NOT_IMPLEMENT_DELETIONS(obj):
   msg = A_classname(obj) + " is read-only.  It does not implement any form of deletion"
   raise NotImplementedError(msg)

def SUBCLASS_MUST_IMPLEMENT(offendingClassOrObject, methodName):
   raisersName = A_classname(offendingClassOrObject)
   raise NotImplementedError("{0} must implement {1}()".format(raisersName, methodName))

class IllegalOpError(Exception):
   pass

