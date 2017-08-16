#! /usr/bin/env python

from delegator import *
from frozendict import FrozenDict
#from readonlydict import ReadonlyDictAPI
import sysutils as su

print("Inheritance delegation overrides test begins.")

class xdict(dict):
   def __init__(self, mappingOrIterable):
      dict.__init__(self, mappingOrIterable)
   def slam(self, x): return "I don't like "+str(x)+"."
   def myclass(self): return self.__class__
   myfield = "xdict's own field: not an instance field"
   def copy(self):
      return xdict(self)

xd = xdict({"a": 1, "b": 2})
fd = FrozenDict(xd)
theMap = object.__getattribute__(fd, "_map")
print("xd is {1}{0}".format(xd, type(xd)))
print("fd is {1}{0}".format(fd, type(fd)))
print("fd._map is {1}{0}".format(theMap, type(theMap)))
print("xd and fd have the same myfield attribute? {}".format(xd.myfield==fd.myfield))
if xd.myfield!=fd.myfield:
   print("xd.myfield = {0}".format(xd.myfield))
   print("fd.myfield = {0}".format(fd.myfield))

print("Check that fd delegates attribute lookup to its read-only copy of xd")
xslam = xd.slam("liars")
fslam = fd.slam("liars")
if xslam != fslam:
   print("slam test failed: '{0}' vs '{1}'".format(xslam, fslam))
else:
   print("slam call delegated succesfully")
if fd.myclass() != xd.myclass():
   print("myclass test failed: '{0}' vs '{1}'".format(xd.myclass(), fd.myclass()))
else:
   print("myclass call delegated succesfully")

xdall = list(x for x in xd)
fdall = list(x for x in fd)
xdall.sort()
fdall.sort()
print("Check that xd and fd have the same lists.")
if fdall != xdall:
   print("They don't: \n   xdall: {0}".format(xdall))
   print("   fdall: {0}".format(fdall))
else:
   print("'x in fd' delegation works.")

xd["c"] = 3
try: 
   print("What is fd['c']? '{}'".format(fd["c"]))
except KeyError:
   print("fd['c'] is an error, but xd['c'] is '{}'".format(xd['c']))
try:
   fd['d'] = 4
   print("Successfully set fd['d'] to '{}'".format(fd['d']))
except:
   print("Failed to set fd['d']")
print("after assigning fd['d'], fd is {}".format(fd))

fd2 = fd.copy()
print("Try copying fd.")
if fd2 == fd:
   print("The copy succeeded")
else:
   print("The copy failed.  Here is the copy:")
   for x in fd2: print("   fd2[{0}] is {1}".format(x, fd2[x]))

print("Delegate missing method test")

class inner:
   def a(self, x): print("   {0}.a is '{1}'".format(id(self), x))
   def b(self, x, y="y"): print("   {0}.b({1}, y={2})".format(id(self), x, y))
   i = "I am the inner i"

class outer:
   i = None
   def __init__(self):
      self.i = inner()

o = outer()
print("before delegating, pubdir(o) is: {0}".format(su.pubdir(o)))
outer = delegate_from_source(outer, "i", inner)
o = outer()
print("after delegating, pubdir(o) is: {0}".format(su.pubdir(o)))
print("in 'o' id(i) is {0}. A call to o.a and three to o.b follows.".format(id(o.i)))
print("The id should start each line.")
o.a("oh dot a!")
o.b("bbb")
o.b("first", y="second")
o.b("third", "fourth")
print("o.i.i should be 'I am the inner i': it is '{}'".format(o.i.i))

print("Delegation test ended")
