
import sysutils as su
from collections import UserList
from delegator import *
from copy import copy
from itertools import chain
from readonlydict import ReadonlyDictAPI
import reprlib


class ReadOnlyInheritance(ReadonlyDictAPI):
   def __init__(self, *args):
      theList = []
      for arg in args:
         if ReadonlyDictAPI.isimplementedby(arg):
            theList.append(arg)
         else:
            for entry in arg:
               if ReadonlyDictAPI.isimplementedby(arg):
                  theList.append(entry)
               else:
                  msg ="A read-only dictionary was expected, but {0} was provided"
                  raise TypeError(msg.format(su.a_classname(entry)))
      self._all = tuple(theList)
      self._size = None # computed lazily--may never be needed

   def __len__(self):
      if self._size is None:
         keys = set()
         for dcnry in self._all:
            for key in dcnry: keys.add(key)
         self._size = len(keys)
      return self._size

   def __getitem__(self, key):
      for dcnry in self._all:
         if key in dcnry: return dcnry[key]
      raise KeyError("'{0}' was not found".format(key))

   def __contains__(self, key):
      for dcnry in self._all:
         if key in dcnry: return True
      return False

   def __iter__(self):  # no, you cannot just chain the dcnry.iters for dcnry in self._all
      return self.keys()

   def __repr__(self):
      return "{0}{1}".format(self.__class__.__name__, reprlib.repr(self._all))

   def __str__(self): return str(self._all)

   def get(self, key, default=None):
      '''Return the value for `key` if present, `default` otherwise.'''
      for dcnry in self._all:
         if key in dcnry:
            return dcnry[key]
      return default

   def copy(self):
      return self.__class__(self._all)

   def items(self):
      keys = set()
      for dcnry in self._all:
         for key in dcnry: 
            if not key in keys:
               keys.add(key)
               yield (key, dcnry[key]) 

   def keys(self):
      keys = set()
      for dcnry in self._all:
         for key in dcnry:
            if not key in keys:
               keys.add(key)
               yield key  

   def values(self):
      keys = set()
      for dcnry in self._all:
         for key in dcnry: 
            if not key in keys:
               keys.add(key)
               yield dcnry[key]

class InheritanceDict:

   def __init__(self, inherited=ReadOnlyInheritance(), keytype=str):
      self.own = {}              # cf JavaScript's "own" versus "inherited" properties
      self.inherited = inherited # read-only access to a set of keys
      self.keytype = keytype     # I enforce this: a key must be an instance of keytype
      self.overrides = 0         # used to speed up computing the size of the whole key set a bit

   def __len__(self):
      return len(self.own) + len(self.inherited) - self.overrides

   def __getitem__(self, key):
      self._vetkey(key)
      return self.own.__getitem__(key) if key in self.own else self.inherited.__getitem__(key)

   def __setitem__(self, key, value):
      self._vetkey(key)
      if key in self.inherited and not key in self.own:
         self.overrides += 1
      self.own.__setitem__(key, value)

   def __delitem__(self, key):
      self._vetkey(key)
      value = self.own[key]     # should throw a KeyError is key is NOT present 
      if key in self.inherited: # if the key is an override, make sure we keep that count correct
         self.overrides -= 1
      self.own.__delitem__(key)
      return value

   def __contains__(self, key):
      self._vetkey(key)
      if self.own.__contains__(key):
         return True
      else:
         for table in self.inherited:
            if table.__contains__(key):
               return True
         return False

   def __iter__(self): return self.keys()

   def __reversed__(self): DOES_NOT_IMPLEMENT_REVERSAL(self)

   def __repr__(self):
      return "{0} {1}".format(self.__class__.__name__, reprlib.repr(self.own))

   def __str__(self): return str(self.own)

   def _vetkey(self, key):
      if not isinstance(key, self.keytype):
         wanted = self.keytype
         got = type(key)
         raise TypeError(
            "Key of type {0} expected, but {1} has type {2}".format(wanted, key, got)
            )

   def clear(self):
      # remove all items from the local dictionary.  Inherited values are unaffected
      self.own.clear()

   def copy(self):
      # Return a shallow copy as a InheritanceDict.
      clone = InheritanceDict(self.inherited, self.keytype)
      clone.own = self.own.copy()
      clone.overrides = self.overrides
      return clone

   def get(self, key, default=None):
      try:
         return self[key]
      except:
         return default

   def isOwn(self, key):
      return key in self.own

   def items(self):
      ours = ((key, self.own[key]) for key in self.own)
      theirs = ((key, self.inherited[key]) for key in self.inherited if not key in self.own)
      return chain(ours, theirs)

   def keys(self):
      ours = iter(self.own)
      theirs = (key for key in self.inherited if not key in self.own)
      return chain(ours, theirs)

   def pop(self, key, default = None):
      if key not in self.own:
         return default
      else:
         return self.__delitem__(key)

   def popkey(self):
      msg = "random key removal is not supported by {0}".format(su.a_classname(self))
      raise NotImplementedError(msg)

   def setdefault(self, key, default=None): 
      if self.__contains__(key):
         return self[key]
      else:
         self.__setitem__(key, default)
         return default

   def update(self, dictLike={}, **kwargs):
      for key in dictLike:
         self.__setitem__(key, dictLike[key])
      for key in kwargs:
         self.__setitem__(key, kwargs[key])

   def values(self):
      ours = (self.own[key] for key in self.own)
      theirs = (self.inherited[key] for key in self.inherited if not key in self.own)
      return chain(ours, theirs)

