
from delegator import *
from copy import copy
import sysutils as su


class ReadonlyDictAPI():
   # The required methods not implemented here:
   def __contains__(self, key): su.SUBCLASS_MUST_IMPLEMENT(self, "__contains__")
   def __getitem__(self, key): su.SUBCLASS_MUST_IMPLEMENT(self, "__getitem__")
   def __len__(self):  su.SUBCLASS_MUST_IMPLEMENT(self, "__getitem__")
   def copy(): su.SUBCLASS_MUST_IMPLEMENT(self, "copy")
   def items(self): su.SUBCLASS_MUST_IMPLEMENT(self, "items")
   def keys(self): su.SUBCLASS_MUST_IMPLEMENT(self, "keys")
   def values(self): su.SUBCLASS_MUST_IMPLEMENT(self, "values")
   # required methods that can be implemented in terms of those above:
   def __iter__(self): return iter(self.keys())
   def get(self, key, default=None):
      '''Return the value for `key` if present, `default` otherwise.'''
      try:
         return self[key]
      except:
         return default
   # methods that enforce the read-only discipline:
   def __setitem__(self, key, value): su.DOES_NOT_IMPLEMENT_ASSIGNMENT(self)
   def __delitem__(self, key): su.DOES_NOT_IMPLEMENT_DELETIONS(self)
   def clear(self): su.DOES_NOT_IMPLEMENT_DELETIONS(self)
   def pop(self, key, default = None): su.DOES_NOT_IMPLEMENT_DELETIONS(self)
   def popkey(self): su.DOES_NOT_IMPLEMENT_DELETIONS(self)
   def setdefault(self, key, default=None): su.DOES_NOT_IMPLEMENT_ASSIGNMENT(self)
   def update(self, other): su.DOES_NOT_IMPLEMENT_ASSIGNMENT(self)


   def isimplementedby(anObject):
      if su.isinstance(anObject, ReadonlyDictAPI):
         return True
      elif not su.implements(anObject, (
         "__getitem__", "__contains__", "__len__", "copy", "get", "items", "keys", "values"
      )):
         return False
      else:
         return (
            su.isindexable(anObject) and 
            su.isiterable(anObject.items()) and 
            su.isiterable(anObject.keys()) and 
            su.isiterable(anObject.values())
         ) 
