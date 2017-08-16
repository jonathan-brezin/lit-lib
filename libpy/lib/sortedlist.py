
from blist import blist
import sysutils as su


class _threshold_data:
   def __init__(self, fraction=0.5, absolute=64*1024):
      if 0.0 <= fraction <= 1.0:
         self.fraction = fraction
      else:
         msg = "Threshold fraction {} is illegal: it must be between 0 and 1"
         raise ValueError(msg.format(fraction))
      self.absolute = int(absolute)
   def __repr__(self):
      return "_threshold_data({:.3f},{})".format(self.fraction, self.absolute)
   def is_met_by(self, entries_in_sorted_part,  new_entries):
      # there must be more new entries than some fraction of the old size
      if new_entries >= entries_in_sorted_part * self.fraction:
         # and there must be at least some minimum number, independent of the old size
         return new_entries >= self.absolute
      else:
         return False

class _threshold:
   def __get__(self, obj, type=None):
      return obj._threshold
   def __set__(self, obj, new_value):
      if isinstance(new_value, _threshold_data):
         obj._threshold = new_value 
      else:
         msg = "The new value, {}, is not a _threshold_data instance, as required."
         raise ValueError(msg.format(su.a_classname(new_value)))
   def __delete__(self, obj):
      raise AttributeError("The threshold attribute cannot be deleted.")

class SortedList(blist):
   threshold = _threshold()
   def __init__(self, iterable=(), key=None):
      blist.__init__(self, iterable)
      blist.sort(self, key=key)

      # The following attributes are used to implement the lazy sorting.  I track the
      # two extreme key values so that when an item is added that at either extreme
      # (or beyond), it can be immediately inserted without worrying about locating
      # the appropriate insertion index. Items that belong in the interior of the list
      # are initially added at the end of the list and put into their correct positions
      # only when an attempt to access the list items is made.
      object.__setattr__(self, "_key", key if key is not None else lambda x: x)
      self._threshold = _threshold_data() # criterion for when to restore sorted order
      self._pending = 0 # how many items at the end of the list need to be relocated
      self._set_firstkey()
      self._set_lastkey()

      # turn on and off debugging aids--see __str__
      self._noRestore = False # allow slicing without restoring the sorted order?
      self._debug = False     # should __str__ special show debugging output?

   def _set_firstkey(self, byIndex=True, value=None):
      if byIndex:
         try:
            value = self._key(blist.__getitem__(self,0))
         except:
            pass
      object.__setattr__(self, "_firstkey", value)

   def _set_lastkey(self, byIndex=True, value=None):
      if byIndex:
         try:
            value = self._key(blist.__getitem__(self,-1))
         except:
            pass
      object.__setattr__(self, "_lastkey", value)



   def __setattr__(self, name, value):
      if name in ["_firstkey", "_key", "_lastkey"]:
         raise AttributeError(name+" is a read-only attribute")
      else:
         object.__setattr__(self, name, value) # use SortedList.__... to avoid recursion

   def __delattr__(self, name):
      if name in ["_firstkey", "_key", "_lastkey", "_pending"]:
         raise AttributeError("the "+name+" attribute may not be deleted.")
      else:
         object.__delattr__(self, name)

   def __repr__(self):
      self.restore_sorted_order()
      old = blist.__repr__(self)
      tail = old[old.index("("):]
      return self.__class__.__name__+ tail

   def __str__(self):
      if not self._debug:
         return self.__repr__()
      else:
         try:
            # I want to use blist's lazy slicing, but only on the list as it is RIGHT NOW, not
            # after it has the sort restored.  Therefore, I need a Boolean to forestall the
            # restore that would occur when the slice is computed.
            self._noRestore = True
            unsortedLength = len(self)-self._pending
            old = blist.__repr__(self[0:unsortedLength]) # this part is in order (or should be!)
            tail = old[old.index("("):]
            pending = str(list(self[unsortedLength:]))   # these are the pending insertions
            self._noRestore = False
            return self.__class__.__name__+"("+str(self.threshold)+")"+tail+pending
         except Exception as e:
            self._noRestore = False
            raise e

   def set_threshold(self, *, fraction=None, absolute=None):
      old = self.threshold
      if fraction is None:
         fraction = old.fraction
      if absolute is None:
         absolute = old.absolute
      self.threshold = _threshold_data(fraction, absolute)

   def sort(self):
      self.restore_sorted_order()

   def restore_sorted_order(self):
      numberPending = self._pending
      if numberPending > 0:
         blist.sort(self, key = self._key)
         self._pending = 0
         self._set_lastkey()
         self._set_firstkey()
      return numberPending

   def merge(self, iterable):
      for item in iterable:
         self.add(item)

   def extend(self, iterable):
      self.merge(iterable)
 
   def add(self, item):  
      newkey = self._key(item)
      if len(self) is 0:
         self._set_lastkey(byIndex=False, value=newkey)
         self._set_firstkey(byIndex=False, value=newkey)
         blist.append(self,item)
      elif newkey >= self._lastkey:
         self._set_lastkey(byIndex=False, value=newkey) 
         blist.append(self,item)   
      elif newkey <= self._firstkey:
         self._set_firstkey(byIndex=False, value=newkey)
         blist.insert(self, 0, item)
      else:
         blist.append(self,item)   
         self._pending += 1
         if self.threshold.is_met_by(len(self), self._pending):
            self.restore_sorted_order()

   def append(self, item):
      self.add(item)
 
   def insert(self, item): 
      newkey = self._key(item)
      if len(self) is 0 or newkey>=self._lastkey or newkey<=self._firstkey:
         self.add(item) # add() takes care of the extreme cases without finding a range
      else:             # I need to find where to put the new item in the interior
         r = self._find_key_range(newkey, False) # False means "don't restore first"
         n = r.stop     # n is the first index of an item having key > newkey
         blist.insert(self, n, item) # shifts self[n:] to the right one slot and inserts the item
                                     # into the now empty n-th slot

   def pop(self, index=-1):
      if len(self) is 0:
         raise IndexError("Attempt to pop from an empty list")
      self.restore_sorted_order()
      answer = blist.pop(self, index)
      if len(self) is 0:
         self._set_lastkey(None)
         self._set_firstkey(value = None)
      else:
         last = self._key(self[-1])
         if last < self._lastkey:
            self._set_lastkey(value = last)
      return answer

   def pop_orelse(self, index=-1, orelse=None):
      try:
         return self.pop(index)
      except IndexError:
         return orelse

   def remove(self, item, sameIdOnly=False, failHard=True):
      r = self.find_item_key_range(item) 
      for n in r:
         item_n = blist.__getitem__(self, n)
         if item_n == item:
            if not sameIdOnly or item_n is item:
               blist.__delitem__(self, n)
               remaining = len(self)
               if remaining is 0:
                  self._set_lastkey(value = None)
                  self._set_firstkey(value = None)
               elif n == remaining: # the last item was deleted, the first is unchanged
                  self._set_lastkey()
               elif n == 0:         # the first item was deleted, the last is unchanged
                  self._set_firstkey()
               return
      if failHard:  # we only get here if nothing was removed
         raise ValueError("{} could not be found to remove".format(item))

   def discard(self, item, sameIdOnly=False):
      self.remove(item, sameIdOnly)

   def replace(self, olditem, newitem, sameIdOnly=False):
      r = self.find_item_key_range(olditem)
      count = self.remove_all(olditem, sameIdOnly=sameIdOnly)
      if count > 0:
         self.merge([newitem]*count)
      return count

   def remove_all(self, item, sameIdOnly = False):
      itemkey = self._key(item)
      r = self.find_key_range(itemkey)
      rreversed = range(r.stop-1, r.start-1, -1)
      count = 0
      for n in rreversed:
         item_n = blist.__getitem__(self, n)
         if item_n == item:
            if not sameIdOnly or (blist.__getitem__(self, n) is item):
               blist.__delitem__(self, n)
               count += 1
      if count > 0: # we could have changed the low and high keys
         if len(self) is 0:
            self._set_lastkey(byIndex=False, value = None)
            self._set_firstkey(byIndex=False, value = None)
         else:
            if itemkey == self._lastkey:
               self._set_lastkey()
            if itemkey == self._firstkey:
               self._set_firstkey()
      return count

   def remove_key(self, key):
      r = self.find_key_range(key) 
      rreversed = range(r.stop-1, r.start-1, -1)
      for n in rreversed:
         blist.__delitem__(self, n)
      if r.stop > r.start: # at least one item was removed
         if len(self) is 0:
            self._set_lastkey(byIndex=False, value = None)
            self._set_firstkey(byIndex=False, value = None)
         else:
            # since at least one item remains and "key" is gone, "key" could not have equalled both
            # the smallest AND the largest key in the list before it was deleted.  It could have
            # been either one of them, though.
            if key == self._lastkey:
               self._set_lastkey()
            elif key == self._firstkey:
               self._set_firstkey()
      return r.stop - r.start

   def __copy__(self):
      self.restore_sorted_order()
      answer = SortedList(self, self._key)
      answer._debug = self._debug
      answer.threshold = self.threshold

   def copy(self):
      return self.__copy__()

   def union(self, other):
      target = self.copy()
      target.merge(other)
      return target

   def __add__(self, other):
      return self.union(other)

   def __iadd__(self, other):
      self.merge(other)
      return self

   def intersection(self, other, *, clone=True):
      self.restore_sorted_order()
      if isinstance(other, SortedList): other.restore_sorted_order()
      common = set(self).intersection(set(other))
      target = self.copy() if clone else self
      for item in common:
         ours = self.count(item)
         theirs = other.count(item)
         both = min(ours, theirs)
         toss = ours - both
         while toss > 0:
            target.remove(item)
            toss -= 1
      return target

   def __and__(self, other):
      return self.intersection(other)

   def __iand__(self, other):
      return self.intersection(other, clone=False)

   def diff(self, other, *, clone=True):
      target = self.copy() if clone else self
      common = self.intersection(other)
      for item in common:
         toss = common.count(item)
         while toss > 0:
            target.remove(item)
            toss -= 1
      return target

   def __sub__(self, other):
      return self.diff(other)

   def __isub__(self, other):
      return self.diff(other, clone=False)

   def xor(self, other, *, clone=True):
      in_one = self.union(other, clone)
      in_both = self.intersection(other)
      return in_one.diff(in_both, clone=False)

   def __xor_(self, other):
      return self.xor(other)

   def __ixor__(self, other):
      return self.xor(other, clone=False)

   def clear(self):
      sizenow = len(self)
      del self[0 : ]
      self._set_firstkey(byIndex=False, value = None)
      self._set_lastkey(byIndex=False, value = None)
      self._pending = 0 # should have been cleared when the slice was taken... but just in case...
      return sizenow


   def __getitem__(self, n):
      # Fetching is by integer index here, not by key or item, so we must drive home all additions
      self.restore_sorted_order()
      if isinstance(n, int):
         return blist.__getitem__(self, n)
      else:
         return SortedList(blist.__getitem__(self, n))

   def __setitem__(self, n, newvalue):
      # You should not be setting the "n-th" item in a sorted list unless you KNOW that the list 
      # will remain sorted after you modify the entry? 
      msg = """Assigning an item to a given position is not supported in sorted lists.
      Use replace(olditem, newitem) to update an item"""
      raise su.IllegalOpError(msg)

   def __delitem__(self, n):
      self.restore_sorted_order()
      blist.__delitem__(self, n)

   def __contains__(self, item):
      self.restore_sorted_order()
      return blist.__contains__(self, item) 

   def __iter__(self):
      self.restore_sorted_order()
      return blist.__iter__(self)

   def __reversed__(self):
      raise su.IllegalOpError("SortedList uses the key's native '<', so reversing one makes no sense.")

   def index(self, item):
      self.restore_sorted_order()
      return blist.index(self, item)

   def bisect_left(self, item):
      r = self.find_key_range(self._key(item))
      return r.start

   def bisect_right(self, item):
      r = self.find_key_range(self._key(item))
      return r.stop

   def last_lt(self, item, orelse = None):
      n = self.bisect_left(self, item) # index of first item with key >= argument's key
      return self[n-1] if n > 0 else (
         None if orelse is None else orelse(self, item))

   def last_le(self, item, orelse = None):
      n = self.bisect_right(self, item) # index of first item with key > argument's key
      return self[n-1] if n > 0 else (
         None if orelse is None else orelse(self, item))

   def first_ge(self, item, orelse = None):
      n = self.bisect_left(self, item) 
      return blist.__getitem__(self, n) if n < len(self) else (
         None if orelse is None else orelse(self, item))
      
   def first_gt(self, item, orelse = None):
      n = self.bisect_right(self, item)
      return blist.__getitem__(self, n) if n < len(self) else (
         None if orelse is None else orelse(self, item))

   def find_slice_range(self, start=None, stop=None, *, inclusive = True, reversed=False):
      self.restore_sorted_order()
      startx = 0  if start is None else self.bisect_left(start)
      stopx  = len(self) if stop is None else (
         self.bisect_right(stop) if inclusive else self.bisect_left(stop))
      if not reversed:
         return range(startx, stopx, 1)
      else:
         startr = stopx - 1 if stopx > 0 else 0
         stopr  = startx - 1 if startx > 0 else 0
         return range(startr, stopr, -1)

   def _find_key_range(self, key, restore):
      if restore:
         self.restore_sorted_order()
      start = None
      stop = None
      high = self.__len__() - 1
      if high < 0:
         return range(0, 0)
      highkey = self._key(blist.__getitem__(self, high))
      if highkey < key:
         return range(self.__len__(), self.__len__()) # everything comes before `key`
      low = 0
      lowkey = self._key(blist.__getitem__(self, low))
      if key < lowkey:
         return range(0, 0) # everything comes after `key`
      # From this point on, we know that key will lie in the interval
      #    self._key(self[low]) <= key <= self._key(self[high])
      mid = (low + high) // 2
      # inside the loop, low < mid < high will hold
      midkey = self._key(blist.__getitem__(self, mid))
      while low < mid and key != midkey:  # let the binary search begin
         if midkey > key:
            high = mid
         else: # must have midkey > key because midkey != key
            low = mid
         mid = (low + high)//2
         midkey = self._key(blist.__getitem__(self, mid))
      for m in range(mid, -1, -1): # find the leftmost item with key < key
         key_m = self._key(blist.__getitem__(self, m))
         if key_m < key: 
            break
      for n in range(mid, high+1, 1): # find the rightmost item with key > key
         key_n = self._key(blist.__getitem__(self, n))
         if key_n > key: 
            break
         start = m if key == key_m else m+1
         stop = n+1 if key == key_n else n
      return range(start, stop) if start is not None else None

   def find_key_range(self, key):
      return self._find_key_range(key, True)

   def find_key(self, key):
      r = self.find_key_range(key)
      if r.start < r.stop and self._key(blist.__getitem__(self, r.start)) == key:
         return r.start
      else:
         return -1

   def find_item_key_range(self, item):
      return self.find_key_range(self._key(item))

   def slice(start=None, stop=None, inclusive = True):
      if self.__len__() == 0:
         return self.SortedList(key=self._key)
      sg = self.slice_generator(start, stop, inclusive)
      return SortedList(iterable=sg, key=self._key)

   def slice_generator(start=None, stop=None, *, inclusive = True, reversed = False):
      # get the starting item index and eliminate some more boundary cases
      r = self.find_slice_range(start, stop, inclusive=inclusive, reversed=reversed)
      return (blist.__getitem__(self, n) for n in r)

   def count(self, item):
      self.restore_sorted_order()
      return blist.count(self, item)

   def reverse(self):
      raise su.IllegalOpError("You cannot reverse a SortedList in place")

   class _CountIter:
      def __init__(self, sl, start=None, stop=None, *, inclusive = True, reversed = False, both=True):
         r = sl.find_slice_range(start, stop, inclusive=inclusive,reversed=reversed)
         self.source = sl
         self.startx = r.start
         self.stopx  = r.stop
         self.step   = r.step
         self.both   = both
      def __next__(self):
         if self.startx >= self.stopx:
            raise StopIteration()
         item = blist.__getitem__(self.source,self.startx)
         stop = self.startx + self.step
         while stop < self.stopx and self._key(item) == self._key(blist.__getitem__(sl, stop)):
            stop += 1
         count = stop - self.startx
         self.startx = stop
         return (self._key(item), count) if both else self._key(item)

   def key_counts(self, start=None, stop=None, *, inclusive = True, reversed = False):
      return self._CountIter(self, start, stop, inclusive=inclusive, reversed=reversed)

   def keys(self, start=None, stop=None, *, inclusive = True, reversed = False):
      return self._CountIter(self, start, stop, inclusive=inclusive, reversed=reversed, both=False)

   class _ItemIter:
      def __init__(self, sl, start=None, stop=None, *, inclusive = True, reversed = False):
         r = sl.find_slice_range(start, stop, inclusive=inclusive,reversed=reversed)
         self.itemset = set()
         self.currentkey = None
         self.source = sl
         self.startx = r.start
         self.stopx  = r.stop
      def __next__(self):
         if self.startx >= self.stopx:
            raise StopIteration()
         item = blist.__getitem__(self, self.startx)
         self.startx += self.step
         key = self._key(item)
         if key == self.currentkey:
            if item in self.itemset:
               return self.__next__()
            else:
               set.itemset.add(item)
               return item
         else:
            self.currentkey = key
            self.itemset.clear()
            self.itemset.add(item)
            return item

   def items(self, start=None, stop=None, *, inclusive = True, reversed = False):
      return self._ItemIter(self, start, stop, inclusive=inclusive, reversed=reversed)


class CheckedSortedList(SortedList):

   def __init__(self, iterable=[], key=None, vetter=lambda x: x):
      self.itemtype = aType
      object.__setattr__(self, "vetter", vetter)
      SortedList.__init__(self, (vetter(item) for item in iterable), key=key)

   def __setattr__(self, name, value):
      if name is "vetter":
         raise AttributeError(name+" is a read-only attribute")
      else:
         SortedList.__setattr__(self, name, value) # use SortedList.__... to avoid recursion

   def __delattr__(self, name):
      if name is "vetter":
         raise AttributeError(name+" may not be deleted.")
      else:
         SortedList.__delattr__(self, name)

   def add(self, item):
      SortedList.add(self, self.vetter(item))

   def insert(self, item):
      SortedList.insert(self, self.vetter(item))
      

class TypedSortedList(CheckedSortedList):

   def __init__(self, iterable=[], key=None, aType=str, asAType=str):
      self.itemtype = aType
      def vetter(data):
         if isinstance(data, aType):
            return data
         elif asAType is not None:
            try:
               return asAType(data)
            except:
               pass
         msg = "{0} was pushed, but {1} is expected."
         raise TypeError(msg.format(su.A_classname(data), su.a_classname(aType)))
      CheckedSortedList.__init__(self, (vetter(item) for item in iterable), key=key, vetter=vetter)

   def __setattr__(self, name, value):
      if name is "itemtype":
         raise AttributeError(name+" is a read-only attribute")
      else:
         CheckedSortedList.__setattr__(self, name, value) # use CheckedSortedList to avoid recursion

   def __delattr__(self, name):
      if name is "itemtype":
         raise AttributeError(name+" may not be deleted.")
      else:
         CheckedSortedList.__delattr__(self, name)



class SortedSet(SortedList):
   def __init__(self, iterable = (), failondup = False):
      SortedList.__init__(self)
      self.failondup = failondup
      for x in iterable:
         self.add(x)

   def __copy__(self):
      return SortedSet(iterable=self, failondup=self.failondup)

   def add(self, item):  
      if failondup and item in self:
         raise ValueError("duplicate item {} not added.".format(item))
      sortedlist.add(self, item)

   def insert(self, item):  
      if failondup and item in self:
         raise ValueError("duplicate item {} not added.".format(item))
      sortedlist.insert(self, item)

   def slice(start=None, stop=None, inclusive = True):
      if self.__len__() == 0:
         return self.SortedSet(failondup=self.failondup)
      sg = self.slice_generator(start, stop, inclusive)
      return SortedSet(iterable=sg, failondup=self.failondup)


class _ondup_value:
   tags = set(("fail", "old", "new", "same", "value"))
   value2tag = {"e": "error", "f": "fail", "o": "old", "n": "new", "s": "same", "v": "value"}
   def __init__(self):
       "e"
   def __get__(self, obj, type=None):      
      return self.ondup
   def __set__(self, obj, value):
      lowered = value.lower()
      initial = lowered[0]
      full_name = self.value2tag[initial]
      if full_name.startswith(lowered):
         self.ondup = initial
      else:
         self.ondup = "e" # as in "error"
         raise ValueError("Unexpected dup handler: '{0}'. Expected one of {1}".format(value,tags))
   def __delete__(self, obj):
      raise AttributeError("The dup handler's strategy tag may not be deleted")
   def __repr__(self):
      return "ondup('{}')".format(self.value2tag[self.ondup])
   def __str__(self):
      return "'{}'".format(self.value2tag[self.ondup])

class SortedKeyedSet(SortedList):
   ondup = _ondup_value()
   def __init__(self, iterable = (), key=None, ondup="new"):
      SortedList.__init__(self, key)
      self.ondup = ondup
      for x in iterable:
         self.add(x)

   def __copy__(self):
      return SortedKeyedSet(self.failondup, self)

   def _fail(self, item, prior, key):
      msg = "duplicate item, {}, with key '{}' cannot replace {}."
      raise ValueError(msg.format(item, key, prior))

   def add(self, item):
      itemkey = self._key(item) 
      prior = self.last_le(item)
      priorkey = self._key(prior)
      if priorkey != itemkey: # new key, new item, no problems
         sortedlist.add(self, item)
      elif self.ondup == 'f': # same key, must fail
         self._fail(item, prior, priorkey)
      elif self.ondup == 's': # fail only if new object id
         if item is not prior:
            self._fail(item, prior, priorkey)
      elif self.ondup == 'v': # fail only if new value
         if item != prior:
            self._fail(item, prior, priorkey)
      elif self.ondup == 'n': # new item wins: out with the old, in with the new
         if item != prior:
            self.remove(prior)
            sortedlist.add(self, item)

   def slice(start=None, stop=None, inclusive = True):
      if self.__len__() == 0:
         return self.SortedKeyedSet(key=self._key, ondup=self.ondup)
      sg = self.slice_generator(start, stop, inclusive)
      return SortedKeyedSet(iterable=sg, key=self._key, ondup=self.ondup)
