
from delegator import *
from copy import copy

@RO_Dict_Delegator("_map")
@Dynamic_Delegator("_map", excluded=set( # the "write" API and copy() are NOT delegated!
      ("__delitem__","__setitem__","clear","copy","pop","popitem","setdefault","update")
   )
)
class FrozenDict():
   def __init__(self, mapping):
      object.__setattr__(self, "_map", mapping.copy())

   def copy(self): # not a straightforward delegation: need self's class's constructor
      return self.__class__(object.__getattribute__(self, "_map"))

   def __str__(self):  # for our purposes, a frozen dict is just its mapping made read-only
      return object.__getattribute__(self, "_map").__str__()

   def __repr__(self): # but from Python's perspective it is constructed by FrozenDict()
      return "{0}({1})".format(self.__class__.__name__, self.__str__())

