#!/usr/bin/env python3.5

# exercising descriptor classes.  You might like to hide the attribute "_d" of the Base object, but
# short of overriding the default __setattr__() method, there's no good way to do that.  Also, you 
# cannot have the descriptor own the object that is _d's value, because Dsc's constructor gets
# called exactly once, namely when Base defines its attribute y. 

print("Good descriptor plays off 'hidden' field:")
class Value:
   def __init__(self, x):
      self.x = x
   def __repr__(self):
      return "Value({})".format(self.x)

class Dsc: # short for "descriptor"
   def __get__(self, obj, type=None): 
      print("Dsc.__get__")
      return obj._d.x
   def __set__(self, obj, value): obj._d.x = value

class Base:
   y = Dsc()
   def __init__(self, d):
      self._d  = d # destined for the descriptor's use

b = Base(Value(3))
print("b._d.x={}, which should equal b.y: {}".format(b._d.x, b.y))
print("Assign 4 to b.y.  Both b._d.x and b.y should then be 4")
b.y = 4
print("You should see 'Dsc.__get__' printed from the next access to b.y.")
print("That shows that b.y did NOT get clobbered and really get the value 4.")
print("b._d.x={} and b.y={}".format(b._d.x, b.y))
# just to prove we have not fallen into the immutable attribute trap:
c = Base(Value(5))
print("c.y is {}, but b.y is still {}".format(c.y, b.y))

print("\nAttempt to ditch the hidden field by saving its value in the descriptor fails.")
# Descriptors lose their magic when assigned to instance fields by a method like the instance
# initializer __init__().  Here's an example.  It shows why you cannot use the descriptor's 
# instance fields directly for carrying the value of the attribute it represents.
class BadDsc:
   def __init__(self, value):
      self.value = value.x
   def __get__(self, obj, type=None): 
      print("BadDsc.__get__")
      return self.value
   def __set__(self, obj, value): self.value = value
   def __repr__(self):
      return "BadDsc({})".format(self.value)

class BadBase:
   def __init__(self, d):
      self.y = BadDsc(d)
   def __repr__(self):
      return "BadBase({})".format(self.y)

badb = BadBase(Value(30))
print("badb.y={}".format(badb.y))
print("We didn't call badb.y.__get__, since we don't see 'BadDsc.__get__' above")
print("badb.y.value={}".format(badb.y.value))
print("Assign 40 to b.y. Note that the next fetch does not print 'BadDsc.__get__'")
print("It does show '40', so we actually have overwritten badb.y with the value 40")
badb.y = 40
print("badb.y={}".format(badb.y))
try:
   print("badb.y.value={}".format(badb.y.value))
except:
   print("badb.y really IS 40, not a descriptor")

# You could collect all the uses in Dsc, as in the second go-round below.  This doesn't
# really hide the "Value", but it does localize where assignments can be tracked (namely
# the class object Dsc2's users dict), at the cost of creating a memory leak--you will
# remember to delete a Base2 instance from users when you are done with it, won't you?.

print("\nBut saving the value in a collection in the descriptor works!")
class Dsc2:
   users = {}
   def __get__(self, obj, type=None): return self.users[obj].x
   def __set__(self, obj, value): self.users[obj].x = value
   def __delete__(self, obj): del self.users[obj]

class Base2:
   y = Dsc2()
   def __init__(self, d):
      Dsc2.users[self] = d
   def __repr__(self):
      return "Base2({})".format(self.y)

b2 = Base2(Value(6))
print("b2.y: {}".format(b2.y))
print("Assign 7 to b2.y.")
b2.y = 7
print("b2.y={}".format(b2.y))
# just to prove we have not fallen into the immutable attribute trap:
c2 = Base2(Value(8))
print("c2.y is {}, but b2.y is still {}".format(c2.y, b2.y))
# you get to do your own garbage collection
del b2.y
print("Dsc2.users is {}".format(Dsc2.users))
