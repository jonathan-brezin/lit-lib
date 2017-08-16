
from blist import *
from idbg import DbgClient
import sys
import sysutils as su


class BufferSizeError(Exception):
   def __init__(self, victim):
      msg = "size limit {0} for this {1} exceeded"
      super().__init__(msg.format(victim.maxsize, victim.__class__.__name__))

class _sizeProperty(object):
   """ read-only access to the current vblist size """
   def __get__(self, obj, objtype):
      return len(obj)
   def __set__(self, obj, val):
      self.raise_error(AttributeError("The vblist's current size is a read-only attribute"))

class _sizelimitProperty(object):
   """  the maximum vblist size can be decreased, but not increased. """
   limits = {}
   def __get__(self, obj, objtype):
      theId = id(obj)
      return self.limits[theId] if theId in self.limits else sys.maxsize
   def __set__(self, obj, val):
      """ I only track those vblists whose length is constrained """
      theId = id(obj)
      val = int(val) if val != None else sys.maxsize
      if theId not in self.limits:
         if val < sys.maxsize:
            self.limits[theId] = val 
      else:
         if val <= self.limits[theId]:
            if val < obj.size:
               msg = "New size limit, {}, less than the current size, {}"
               self.raise_error(ValueError(msg.format(val, obj.size)))
            self.limits[theId] = val
         else:
            before = self.limits[theId]
            msg = "You cannot increase the size limit {} to {}"
            self.raise_error(ValueError(msg.format(before, val)))


class _sharedMethods:
   def __add__(self, other):
      return self.__class__(self, vet=self.vet).add_all(other)

   def __copy__(self):
       # do not vet the entries again: let vet be None initially
      newlist = self.__class__(self, maxsize=self.maxsize, vet=None)
      newlist.vet = self.vet
      return newlist
      
   def __eq__(self, other):
      return isinstance(other, self.__class__)  and \
      self.vet == other.vet and \
      self.maxsize == other.maxsize and\
      super().__eq__(other)

   def __iadd__(self, other):
      return self.add_all(other)

   def __imul__(self, k):
      original = self.__class__(self)
      for n in range(0,int(k)-1):
         self += original

   def __mul__(self, k):
      answer = self.__class__(self)
      for n in range(0,int(k)-1):
         answer += self
      answer.vet = self.vet

   def __ne__(self, other):
      return not self.__eq__(other)

   def __radd__(self, other):
      return other.__add__(self)

   def __rmul__(self, k):
      return self.__mul__(k)

   def __repr__(self):
      #print("Ur class: {}".format(self.__class__))
      inherited = super().__repr__()
      tail = inherited[inherited.find('('):]
      return self.__class__.__name__+tail

   def handle_overflow(self, dieOnFail):
      if dieOnFail:
         self.raise_error(BufferSizeError(self))
      else:
         msg = "attempt to add to {2} failed for size {0} and bound {1}"
         self.issue_warning(msg.format(self.size, self.maxsize, su.a_classname(self)))
         return False

   def add_all(self, an_iterable,  *, dieOnFail=True):
      if not _sharedMethods.isAVettedCollection(an_iterable) or (self.vet != an_iterable.vet):
         an_iterable = [self.vet(item) for item in an_iterable]
      if self.maxsize == sys.maxsize or self.size+len(an_iterable) <= self.maxsize:
         if hasattr(self, "extend"):
            super().extend(an_iterable) # for collections where "add" means "add at end"
         else:
            for item in an_iterable: self.add(item)
      else:
         for item in an_iterable:
            if not self.add(item, dieOnFail=dieOnFail): # fail on overflow?
               break
      return self

   def copy(self):
      return self.__copy__()

   def find(self, what):
      try:
         return self.index(what)
      except:
         return -1

   def head(self, howMany = None):
      if howMany is None: # return the entry, not a list!! 
         return self[0]
      if howMany > self.size:
         msg = "{} entries requested, but only {} available"
         self.raise_error(IndexError(msg.format(howMany, self.size)))
      else:
         return self[0: howMany]

   def isEmpty(self): return self.size is 0

   @staticmethod
   def isAVettedCollection(stuff):
      return isinstance(stuff, vblist) or isinstance(stuff, vbdeque) or \
            isinstance(stuff, vsortedlist) or isinstance(stuff, vsortedset)

   def peek(self, howMany = None, *, orElse = None, reverse=True):
      if howMany is None:
         return orElse if self.size == 0 else self[0]
      else:
         if howMany > 0: 
            available = self.size if self.size < howMany else howMany
            values = self[0 : available] 
         else:
            howMany = -howMany
            available = self.size if self.size < howMany else howMany
            values = self[-available:]
            if reverse: values.reverse()
         leftToAdd = howMany - available
         return values if leftToAdd is 0 else values + ([orElse]*leftToAdd)

   def tail(self, howMany = None):
      if howMany is None: # return the entry, not a list!! 
         return self[-1]
      if howMany > self.size:
         msg = "{} entries requested, but only {} available"
         self.raise_error(IndexError(msg.format(howMany, self.size)))
      else:
         return self[-howMany:]

class vblist(_sharedMethods, blist, DbgClient):
   size   = _sizeProperty()
   maxsize = _sizelimitProperty()
   # buffered debugging available, but left off for the moment:
   def __init__(self, iterable=[], maxsize = sys.maxsize, vet=None):
      blist.__init__(self, [])
      # local public attributes:
      self.maxsize = maxsize
      if vet is None: # don't waste time vetting the initial entries
         blist.extend(self, iterable)
         self.vet = lambda data: data
      else:
         self.vet = vet
         for entry in iterable:
            self.add(entry)


   def __setitem__(self, which_indices, data):
      if isinstance(which_indices, int):
         added = self.vet(data)
         if which_indices >= 0:
            if which_indices < self.size:
               blist.__setitem__(self, which_indices, added)
               return
         elif which_indices >= -self.size:
               blist.__setitem__(self, which_indices, added)
               return
         else:
            msg = "index {0} is not in range(-{1},{1}), as required."
            self.raise_error(IndexError(msg.format(which_indices, self.size)))
      elif isinstance(which_indices, slice):
         self.dbg_write("get [{0}] slice".format(which_indices))
         the_range = su.slice2range(which_indices, max=self.size)
      elif isinstance(which_indices, range):
         the_range = which_indices
      else:
         template = "{0} cannot be used to index {1}"
         msg = template.format(su.a_classname(which_indices), su.a_classname(self))
         self.raise_error(TypeError(msg))
      if the_range.start < 0 or the_range.stop > self.size:
         msg = "{} is not a subrange of range(0,{}), as required"
         self.raise_error(IndexError(msg.format(the_range, self.size)))
      if len(range) >= len(entries):
         # possibly shrink the list, but first overwrite what is there
         next_in = range.start
         for entry in entries:
            self[next_in] = entry
            next_in += 1
         if next_in < range.stop:
            del self[next_in:range.stop]
      else: 
         # need to expand the list, so just blow away self[slice] and insert data
         # in its place
         del self[the_range]
         next_in = the_range.start
         for entry in entries:
            self.insert(next_in, entry)
            next_in += 1

   def add(self, what, *, dieOnFail=True):
      what = self.vet(what)
      if self.size < self.maxsize:
         super().append(what)
         return True
      else:
         return self.handle_overflow(dieOnFail)

   def add_all(self, an_iterable,  *, dieOnFail=True):
      if not _sharedMethods.isAVettedCollection(an_iterable) or (self.vet != an_iterable.vet):
         an_iterable = [self.vet(item) for item in an_iterable]
      if self.size+len(an_iterable) <= self.maxsize:
         super().extend(an_iterable) 
      else:
         self.handle_overflow(dieOnFail)
      return self

   def add_first(self, what, *, dieOnFail=True):
      if self.size < self.maxsize:
         super().insert(0, what)
         return True
      else:
         self.handle_overflow(dieOnFail)
      return False

   def append(self, what):
      return self.add(what)

   def extend(self, iterable, dieOnFail=True):
      return self.add_all(iterable, dieOnFail=dieOnFail)

   def insert(self, where, what, dieOnFail=True):
      what = self.vet(what)
      if self.size < self.maxsize:
         blist.insert(self, where, what)
         return True
      else:
         template = "Attempt to insert into a full {}, size {}"
         msg = template.format(self.__class__.__name, self.size)
         if dieOnFail:
            self.raise_error(BufferSizeError(msg))
         else:
            self.dbg_write(msg)
            return False

   def next(self, howMany=None):
      if howMany is None:
         if self.size > 0:
            answer = self[0]
            del self[0]
            return answer
         else:
            msg = "Request for next from an empty "+self.__class__.__name__
            self.raise_error(IndexError(msg))
      elif howMany > 0 and howMany <= self.size:
         answer = self[0:howMany]
         del self[0:howMany]
         return answer
      elif howMany < 0 and (-howMany) <= self.size:
         answer = self[-howMany:]
         del self[-howMany:]
         return answer
      else:
         msg = "{0} entries requested, only {1} available"
         self.raise_error(IndexError(msg.format(abs(howMany), self._count_)))

   def next_or_else(self, howMany=None, orElse=None):
      if howMany is None:
         try:
            return self.next()
         except IndexError:
            return orElse
      elif abs(howMany) <= self.size:
         return self.next(howMany)
      else:
         fromList = self.next(howMany=self.size)
         need = abs(howMany) - self.size
         return fromList + ([orElse]*need)

   def prepend(self, iterable):
      added = list(iterable)
      added.reverse()
      for x in added:
         self.add_first(x)

   def push(self, what):
      return self.add(what, dieOnFail=False)

   def replace(self, indexOrRange, iterable, dieOnFail=True):
      if isinstance(indexOrRange, int):
         insertionpoint = indexOrRange
         del self[insertionpoint]
      else:
         if indexOrRange.step != 1:
            self.raise_error(ValueError("expected a range with step 1, not {}", indexOrRange.step))
         insertionpoint = indexOrRange.start
         del self[insertionpoint: indexOrRange.stop]
      for v in iterable:
         self.insert(v, insertionpoint)
         insertionpoint += 1

vblist.configure_debugging("vblist") 


class vbdeque(vblist):
   def __init__(self, iterable=[], maxsize = sys.maxsize, vet = None):
      super().__init__(iterable, maxsize, vet)


   def _forbid(self, msg):
      self.raise_error(su.IllegalOpError(msg.format(self.__class__.__name__)))

   def insert(self, index, object):
      self._forbid("Random insertion into a {} is not supported")
      
   def remove(self, value):
      self._forbid("Random removal from a {} is not supported.")

   def reverse(self):
      self._forbid("Reversing a {} is not supported")

   def sort(self):
      self.forbid("Sorting a {} is not supported")

   def __setitem__(self, index, value):
      self._forbid("{} indexing is only for read access")

   def __delitem__(self, index):
      if isinstance(index, int):
         if index in (0, -1, self.size-1):
            super().__delitem__(index)
            return
         else:
            self._forbid("Deletion from the middle of a {} is not supported")
      elif isinstance(index, slice):
         self.dbg_write("get [{0}] slice".format(index))
         the_range = su.slice2range(index, max=self.size)
      elif isinstance(index, range):
         the_range = index
      else:
         self.raise_error(TypeError("Illegal type for 'index': {}".format(type(index))))
      if the_range.start == 0 or the_range.stop == self.size:
         for n in range(0, len(the_range)): blist.__delitem__(self, the_range.start)
      else:
         self.forbid("Deletion from the middle of a {} is not supported")


class vbqueue(vbdeque):
   def __init__(self, iterable=[], maxsize = sys.maxsize, vet=None):
      super().__init__(iterable, maxsize, vet)

   def add_first(self, what):
      self._forbid("A {} only grows from at its end")

   def prepend(self, iterable, *, dieOnFail=True):
      self._forbid("A {} only grows from at its end")


   def __delitem__(self, index):
      if isinstance(index, int):
         if index == 0:
            super().__delitem__(index)
            return
         else:
            self._forbid("Only deletion at the start of a {} is supported")
      elif isinstance(index, slice):
         self.dbg_write("get [{0}] slice".format(index))
         the_range = su.slice2range(index, max=self.size)
      elif isinstance(index, range):
         the_range = index
      else:
         self.raise_error(TypeError("Illegal type for 'index': {}".format(type(index))))
      if the_range.start == 0:
         for n in range(0, len(the_range)): blist.__delitem__(self, the_range.start)
      else:
         msg = "Deletion from the middle of {} is not supported"
         self.forbid(msg.format(su.a_classname(self)))

   def next_or_else(self, howMany=None, orElse=None):
      if howMany is None or howMany >= 0:
         return super().next_or_else(howMany=howMany, orElse=orElse)
      else:
         self.raise_error(ValueError("Illegal 'next' count, {}".format(howMany)))

   def next(self, howMany=None):
      if howMany is None or howMany >= 0:
         return super().next(howMany)
      else:
         self.raise_error(ValueError("Illegal 'next' count, {}".format(howMany)))



class vbstack(vbdeque):

   def __init__(self, iterable=[], maxsize = None, vet=None):
      super().__init__(iterable, maxsize, vet)

   def add_first(self, what):
      self._forbid("A {} only grows from at its end")

   def prepend(self, iterable, *, dieOnFail=True):
      self._forbid("A {} only grows from at its end")


   def __delitem__(self, index):
      if isinstance(index, int):
         if index == -1 or index == self.size - 1:
            super().__delitem__(index)
            return
         else:
            self._forbid("Only deletion at the end of a {} is supported")
      elif isinstance(index, slice):
         self.dbg_write("get [{0}] slice".format(index))
         the_range = su.slice2range(index, max=self.size)
      elif isinstance(index, range):
         the_range = index
      else:
         self.raise_error(TypeError("Illegal type for 'index': {}".format(type(index))))
      if the_range.stop == self.size:
         for n in range(0, len(the_range)): blist.__delitem__(self, the_range.start)
      else:
         msg = "Only deletion from the top of {} is supported"
         self.forbid(msg.format(su.a_classname(self)))

   def next_or_else(self, howMany=None, orElse=None):
      if howMany is None:
         return super().next_or_else(orElse=orElse, howMany=None)
      if howMany >= 0:
         return vblist.next_or_else(self, orElse=orElse, howMany=-howMany)
      else:
         self.raise_error(ValueError("Illegal 'next' count, {}".format(howMany)))

   def next(self, howMany=None):
      if howMany is None:
         return vblist.next(self, howMany=-1)
      elif howMany >= 0:
         return vblist.next(self, howMany=-howMany)
      else:
         self.raise_error(ValueError("Illegal 'next' count, {}".format(howMany)))

   def pop(self, howMany=None):
      return self.next(howMany)


class vsortedlist(_sharedMethods, sortedlist, DbgClient):
   size   = _sizeProperty()
   maxsize = _sizelimitProperty()
   def __init__(self, an_iterable=[], maxsize = sys.maxsize, vet=None):
      sortedlist.__init__(self, [])
      DbgClient.__init__(self)
      # local public attributes:
      self.maxsize = maxsize
      self.vet = (lambda data: data) if vet is None else vet
      for entry in an_iterable:
         self.add(entry)

   def _forbid(self, msg):
      self.raise_error(su.IllegalOpError(msg.format(self.__class__.__name__)))

   def __setitem__(self, index, value):
      self._forbid("{} indexing is only for read access")

   def add(self, what, *, dieOnFail=True):
      what = self.vet(what)
      if self.size < self.maxsize:
         super().add(what)
         return True
      else:
         return self.handle_overflow(dieOnFail)

   def add_all(self, an_iterable,  *, dieOnFail=True):
      return self.update(an_iterable, dieOnFail=dieOnFail) 

   def update(self, an_iterable, *, dieOnFail=True):
      if not _sharedMethods.isAVettedCollection(an_iterable) or (self.vet != an_iterable.vet):
         an_iterable = [self.vet(item) for item in an_iterable]
      if self.maxsize == sys.maxsize or self.size+len(an_iterable) <= self.maxsize:
         for item in an_iterable:
            if not self.add(item, dieOnFail=dieOnFail):
               break
      else:
         self.handle_overflow(dieOnFail)
      return self


class vsortedset(_sharedMethods, sortedset, DbgClient):
   size   = _sizeProperty()
   maxsize = _sizelimitProperty()
   def __init__(self, an_iterable=[], maxsize = sys.maxsize, vet=None):
      sortedset.__init__(self, [])
      DbgClient.__init__(self)
      # local public attributes:
      self.maxsize = maxsize
      self.vet = (lambda data: data) if vet is None else vet
      for entry in an_iterable:
         self.add(entry)

   def _forbid(self, msg):
      self.raise_error(su.IllegalOpError(msg.format(self.__class__.__name__)))

   def __setitem__(self, index, value):
      self._forbid("{} indexing is only for read access")

   def __and__(other):
      return self.intersection(other)

   def __iand__(other):
      return self.intersection_update(other)

   def __or__(self, other):
      return self.__class__(self, vet=self.vet).add_all(other)

   def __ior__(self, other):
      return self.add_all(other)

   def __xor__(self, other):
      return self.symmetric_difference(other)

   def __ixor__(self, other):
      return self.symmetric_difference_update(other)

   def add(self, what, *, dieOnFail=True):
      what = self.vet(what)
      if self.size < self.maxsize:
         super().add(what)
         return True
      else:
         return self.handle_overflow(dieOnFail)

   def add_all(self, an_iterable,  *, dieOnFail=True):
      for item in an_iterable:
         if not self.add(item, dieOnFail=dieOnFail): # fail on overflow?
            break
      return self

   def intersection(self, *others, maxsize=None):
      if maxsize == None:
         maxsize = self.maxsize
      a_copy = self.__class__(self, vet=self.vet, maxsize=maxsize)
      return a_copy.intersection_update(other)

   def intersection_update(self, *others):
      left = self.size
      for other in others:
         for item in other:
            if item not in self:
               self.discard(item)
               left -= 1
               if left <= 0:
                  break
      return self

   def symmetric_difference(self, other, maxsize=None):
      if maxsize == None:
         maxsize = self.maxsize
      a_copy = self.__class__(self, vet=self.vet, maxsize=maxsize)
      return a_copy.symmetric_difference_update(other)

   def symmetric_difference_update(self, other):
      in_both  = self & other
      from_other = other - in_both
      self &= in_both
      self += from_other
      return self

   def union(self, *others, dieOnFail=True):
      for other in others:
         self.add_all(other, dieOnFail=dieOnFail)
      return self

   def update(self, an_iterable):
      return self.add_all(an_iterable, dieOnFail=True) 
