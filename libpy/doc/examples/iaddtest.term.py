#!/usr/bin/env python3.5

# This is an example that shows the need to be careful when implementing the delegation of
# the  so-called "augmented assignment" or "in-place" versions of the binary operators.
# Here I use "+" as an example.  
#
# What seems to be the conclusion on should draw from this code is that the semantics of 
# evaluating x += y, when that uses x.__iadd__(), is the same as writing x = x.__iadd__(y),
# at least for the Python interpreter
#
# Python 3.5.2 |Continuum Analytics, Inc.| (default, Jul  2 2016, 17:52:12) 
# [GCC 4.2.1 Compatible Apple LLVM 4.2 (clang-425.0.28)] on darwin.
#
# Indeed, when there is no __iadd__ attribute, x += y becomes x=x.__add__(y) or if that fails,
# y.__radd__(x).

class C: # delegates addition to its field 'x'
   def __init__(self, x): self.x = x
   def __add__(self, y):  return self.x + (y.x if isinstance(y, C) else y)
   def __iadd__(self, y): 
      self.x += (y.x if isinstance(y, C) else y)
      return self
   def __repr__(self):
      return "C({})".format(self.x)

class D:  # delegates addition to its 'x' field, which is a C
   def __init__(self, x): self.c = C(x)
   def __add__(self, y): return self.c + (y.c if isinstance(y, D) else y)
   def __iadd__(self, y):
      self.c += (y.c if isinstance(y, D) else y)
      return self
   def __repr__(self):
      return "D({})".format(self.c.x)
   def __str__(self):
      return "D(C({}))".format(self.c.x)


d = D(9)
d += 1
print( "d should be D(C(10)): {}".format(d) )
d = D(9)
print( "D(9)+D(1) should be 10: {}".format(d + D(1)))
print( "D(9)+C(2) should be 11: {}".format(d+C(2)))
d += C(2)
print( "d = D(9). After d+=C(2), d should be D(C(11)): {}".format(d))
print("Try evaluating 'x=3; y=x+=4' in the python interpreter")
print("You can see why the return value of __iadd__ might not be critical!")

print("Let's try a variation on C with a different return value, None:")

class CC: # delegates addition to its field 'x'
   def __init__(self, x): self.x = x
   def __add__(self, y):  return self.x + (y.x if isinstance(y, C) else y)
   def __iadd__(self, y): 
      self.x += (y.x if isinstance(y, C) else y)
      return None
   def __repr__(self):
      return "CC({})".format(self.x)

c = CC(5)
c += 7

print("c = CC(5).  After c+=7, c should be CC(12): {}".format(c))
print("Oh my!  That's not good... let's try another, return a 'random' value:")

class CCC: # delegates addition to its field 'x'
   def __init__(self, x): self.x = x
   def __add__(self, y):  return self.x + (y.x if isinstance(y, C) else y)
   def __iadd__(self, y): 
      self.x += (y.x if isinstance(y, C) else y)
      return y*2
   def __repr__(self):
      return "CCC({})".format(self.x)

c = CCC(4)
c += 8
print("c = CCC(4).  After c+=8, c should be CCC(12), not 16: {}".format(c))

print("One last try: __iadd__ returns the sum that actually should get assigned:")

class CCCC: # delegates addition to its field 'x'
   def __init__(self, x): self.x = x
   def __add__(self, y):  return self.x + (y.x if isinstance(y, C) else y)
   def __iadd__(self, y): 
      self.x += (y.x if isinstance(y, C) else y)
      return self.x
   def __repr__(self):
      return "CCCC({})".format(self.x)

c = CCCC(3)
c += 9

print("c = CCCC(3).  After c+=9, c should be CCCC(12), not 12: {}".format(c))
print("This is sad: c is now an integer, not a CCCC")
print("Bottom line: it really does matter that __iadd__ returns `self`")
