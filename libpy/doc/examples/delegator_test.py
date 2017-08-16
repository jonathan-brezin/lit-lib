###########################################################################################
#
# Some basic code to test the functions in the delegator module 
#
###########################################################################################
from delegator import *
from types import SimpleNamespace
import sysutils as su

@Indexing_Delegator(delegate_name="indexed")
class TheDelegator(SimpleNamespace):
   def __init__(self, n):
      self.indexed = [k for k in range(0, n)]
      self.anumber = 0

td = TheDelegator(12)
print("td[3] is ", td[3])
td[3] = 123
print("td3 should be 123 now: ", td[3])

@List_Delegator(delegate_name="array")
class WrappedList(SimpleNamespace):
   def __init__(self, n):
      self.array = [k for k in range(0, n)]

wl = WrappedList(5)
print("wl.array is", wl.array)
print("pubdir(wl) =", su.pubdir(wl))

wl.append(1 + wl[-1])
for n in wl:
   print(n, "is there, with value '"+str(wl[n])+"'")

print("4 in wl is", 4 in wl)
wl[0] = 44
print("wl array is now", wl.array)
del wl[1]
print("and after deleting wl[1]", wl)


@Tuple_Delegator(delegate_name="tp")
class WrappedTuple(SimpleNamespace):
   def __init__(self, n):
      self.tp = tuple(x*2 for x in range(0, n))

wt = WrappedTuple(4)
print("wt.tp is", wt.tp)
print("pubdir(wt) =", su.pubdir(wt))
print("wt[2] is ", wt[2])

for n in range(0, len(wt)):
   print(n, "is there, with value '"+str(wt[n])+"'")

print("1 in wt is", 1 in wt)
print("4 in wt is", 4 in wt)

try:
   print("try to remove the 0-th entry of wt")
   del wt[0]
except su.IllegalOpError as e:
   print(e)

try:
   print("now try to remove the 0-th entry of wt.tp")
   del wt.tp[0]
except Exception as e:
   print(e)


@Dynamic_Delegator(delegate_name="ro", included=set(("__getitem__",)), excluded=set(("__setitem__", "__delitem__")))
class RODict(SimpleNamespace):
   def __init__(self, d):
      object.__setattr__(self, "ro", d)

d = {"a":1, "b": 2, "c": 3}
rod = RODict(d)
print("rod['a'] is '"+str(rod["a"])+"'")
print("'b is in rod:", "b" in rod)
print("all of rod:", [x for x in rod])
d["d"] = 4
print("after adding 'd', all of rod:", [x for x in rod])
try:
   rod["e"] = 5
except su.IllegalOpError as e:
   print(e)

@Delegate_Protector(delegate_name="tp")
@Tuple_Delegator(delegate_name="tp")
class PrivateTuple(SimpleNamespace):
   def __init__(self, n):
      object.__setattr__(self, "tp", tuple(x*2 for x in range(0, n)))

pt = PrivateTuple(4)
print("pt[2] is ", pt[2])

for n in range(0, len(pt)):
   print(n, "is there, with value '"+str(pt[n])+"'")

print("1 in pt is", 1 in pt)
print("4 in pt is", 4 in pt)

try:
   del pt[0]
except su.IllegalOpError as e:
   print(e)

try:
   print("pt.tp is", pt.tp)
except su.IllegalOpError as e:
   print(e)

@RO_Dict_Delegator("_map")
@Dynamic_Delegator("_map", included=(("__str__",)), excluded=set(
         ("__delitem__", "__setitem__", "clear", "copy", "pop", "popitem", "setdefault", "update")
      ))
class FrozenDict():
   def __init__(self, aMap):
      try:
         theMap = aMap.copy()
      except:
         theMap = dict(aMap.items())
      object.__setattr__(self, "_map", theMap)
   def copy(self): # not a straightforward delegation: need self's class's constructor
      return self.__class__(object.__getattribute__(self, "_map"))
   def __str__(self):
      return object.__getattribute__(self, "_map").__str__()

# I am freezing a dict here, so all I really need is @Delegate_Protector, not @Dynamic_Delegator
# But that all changes in the next example, where I freeze an extension of dict
fd = FrozenDict(d)
print("fd['a'] is 1? {}".format(fd['a'] is 1))
try:
   fd['d'] = 4
   print("You should not see this!")
except Exception as e:
   print(e)

for x in fd: print(x, fd[x])

try:
   x = fd.pop()
   print("Should not pop, but got", x)
except Exception as e:
   print(e)

try:
   fd._map
   print("Should not allow a reference to _map")
except Exception as e:
   print(e)

fk = fd.fromkeys((str(x) for x in range(3,7)), "!")
print("fk['4'] is '{}'".format(fk['4']))

# I raise the stakes now.  DictPlus has a "name" attribute that I want to allow access to.  The
# dynamic lookup means it is found, even though it is not part of the RO_Dict set of included
# attributes.
class DictPlus(dict):
   def __init__(self, name, *args, **kwargs):
      dict.__init__(self, *args, **kwargs)
      self. name = name
   def copy(self):
      return self.__class__(self.name, self)
   def __str__(self):
      return "{}".format(self.name)+dict.__str__(self)

dplus = DictPlus("bigD", d)
# Now I am freezing a DictPlus.  Only because of the dynamic delegation is 'name' visible.
fdplus = FrozenDict(dplus)

print("fdplus.name should be 'bigD': '{}'.".format(fdplus.name))
print("And its keys should be a through d:", [x for x in fdplus])
print("str(fdplus) is {}.".format(fdplus))
try:
   fdplus['d'] = 76
   print("Successfully set fdplus['d'] to {}!".format(fdplus['d']))
except Exception as e:
   print(e)

noname = "name" not in su.pubdir(fdplus)
print("name should not be a directly visible attribute of fdplus: {}".format(noname))

# Finally, some very minimal dynamic delegation:
class Ref:
   def __init__(self):
      self.a = "a"
      self.b = 2
      self.c = "see?"
   def __getitem__(self, key):
      if hasattr(self, key):
         return self.__getattribute__(key)
      else:
         raise AttributeError("a Ref has no such key, '{}'".format(key))

class IndirectRef:
   def __init__(self, aRef):
      object.__setattr__(self, "_ref", aRef)

basic_delegate_attr(IndirectRef, "_ref") 

ir = IndirectRef(Ref())
print("ir.c is '{}'".format(ir.c))
try:
   print("ir._ref is ", ir._ref)
except Exception as e:
   print(e)

try:
   print("ir.__getitem__", ir.__getitem__)
   print("ir['c'] is '{}'".format(ir['c']))
except  Exception as e:
   print(e)

class IndirectRef2:
   def __init__(self, aRef):
      object.__setattr__(self, "_ref", aRef)

basic_delegate_attr(IndirectRef2, "_ref", protect=False) 

ir2 = IndirectRef2(Ref())
print("ir2.c is '{}'".format(ir2.c))
try: # just in case you forgot that __getitem__ doesn't work unless it is a class attribute
   print("ir2._ref is ", ir2._ref)
   print("ir2._ref['c'] is '{}'".format(ir2._ref['c']))
   print("ir2.__getitem__ is {}".format(ir2.__getitem__))
   print("ir2['c'] is '{}'".format(ir2['c'])) # this should fail
except Exception as e:
   print(e)

# To drive home that last point:

class IndirectRef3:
   def __init__(self, aRef):
      object.__setattr__(self, "_ref", aRef)
   def __getitem__(self, key):  # add the def for __getitem__, unlike IndirectRef2
      return self._ref[key]

ir3 = IndirectRef3(Ref())
try: 
   print("ir3._ref is ", ir3._ref)
   print("ir3._ref['c'] is '{}'".format(ir3._ref['c']))
   print("ir3.__getitem__ is {}".format(ir3.__getitem__))
   print("ir3['c'] is '{}'".format(ir3['c'])) # this now works
except Exception as e:
   print(e)
