
import sysutils as su


class DictAsSet(dict):

   def __init__(self, initialdata=[], onconflicts="die", **kwargs):
      dict.__init__(self, initialdata, **kwargs)
      self.onconflicts = onconflicts

   def __copy__(self):
      clone = DictAsSet(self)
      clone.onconflicts = self.onconflicts
      return clone

   def copy(self):
      return self.__copy__()

   def discard(self, key):
      if key in self: del self[key]

   def remove(self, key):
      if key not in self:
         return None
      else:
         self_key = self[key]
         del self[key]
         return self_key


   def isdisjointfrom(self, other):
      if not isinstance(other, dict):
         raise ValueError("Argument is {}, but a dict is expected".format(su.a_classname(other)))
      if len(other) < len(self):
         for key in other:
            if key in self: return False
         return True
      else:
         for key in self:
            if key in other: return False
         return True

   def __le__(self, other):
      if not isinstance(other, dict):
         raise ValueError("Cannot compare a DictAsSet with {}".format(su.a_classname(other)))
      for key in self:
         if key not in other or self[key] != other[key]:
            return False
      return True

   def __lt__(self, other):
      return self.__le__(other) and len(self) < len(other)

   def __ge__(self, other):
      if not isinstance(other, dict):
         raise ValueError("Cannot compare a DictAsSet with {}".format(su.a_classname(other)))
      for key in other:
         if key not in self or self[key] != other[key]:
            return False
      return True

   def __gt__(self, other):
      return self.__ge__(other) and len(self) < len(other)

      
   def handle_conflicts(self, msg, result, conflicts, others):
      all_sources = [result]+list(others)
      if self.onconflicts == "die":
         raise DictConflictError(msg, result, conflicts, all_sources)
      elif callable(self.onconflicts):
         return self.onconflicts(msg, result, conflicts, all_sources)
      else: # this should never happen
         err = "Unexpected value, '{}', for self.onconflicts."
         raise ValueError(err.format(self.onconflicts))


   def _validate_other(other, op):
      if not isinstance(other, dict):
         msg = "{} right operand is a {}, not a dict."
         raise ValueError(msg.format(op), su.a_classname(other))

   def __add__(self, other):
      answer = self.copy()
      answer.__iadd__(other)
      return answer

   def __iadd__(self, other):
      DictAsSet._validate_other(other, "+")
      conflicts = set()
      if self.onconflicts == "first":
         for key in other:
            if key not in self: 
               self[key] = other[key]
      elif self.onconflicts == "last":
         for key in other: 
            self[key] = other[key]
      else:
         for key in other:
            if key in self:
               if self[key] != other[key]:
                  conflicts.add(key)
            else:
               self[key] = other[key]
      if len(conflicts) > 0:
         msg = "add in place failed"
         return self.handle_conflicts(msg, answer, conflicts, [other])
      else:
         return self

   def __and__(self, other):
      answer = self.copy()
      answer.__iand__(other)
      return answer

   def __iand__(self, other):
      # we have to be careful NOT to delete from self while iterating over self
      # so we iterate over the dead bodies.
      DictAsSet._validate_other(other, "&")
      dead = set(self.keys()) - set(other.keys()) 
      for key in dead:
         del self[key]
      if self.onconflicts == "first":
         return self
      elif self.onconflicts == "last":
         for key in self:
            self[key] = other[key]
         return self
      else:
         conflicts = set()
         for key in  self:
            if self[key] != other[key]:
               conflicts.add(key)
               print("iand conflict: '{}'".format(key))
         if len(conflicts) == 0:
            return self
         else:
            for key in conflicts:
               self.discard(key)
            msg = "'and 'in place failed"
            return self.handle_conflicts(msg, self, conflicts, [other])

   def __sub__(self, other):
      answer = self.copy()
      answer -= other
      return answer

   def __isub__(self, other):
      DictAsSet._validate_other(other, "-")
      common_keys = set(self.keys()).intersection(set(other.keys()))
      for key in common_keys:
         if self[key] == other[key]:
            del self[key]
      return self

   def __xor__(self, other):
      DictAsSet._validate_other(other, "^")
      answer = DictAsSet(self-other, onconflicts="die")
      answer += (other - self) # will crash and burn on duplicate keys
      answer.onconflicts = self.onconflicts
      return answer

   def __ixor__(self, other):
      DictAsSet._validate_other(other, "^")
      saved = self.onconflicts
      self.onconflicts = "die"
      try:
         self -= other
         self += (other - self) # will crash and burn on duplicate keys
      except:
         self.onconflicts = saved
         raise
      else:
         self.onconflicts = saved
         return self


   def intersect(self, *others):
      answer = self.copy()
      answer.update_intersect(*others)
      return answer

   def update_intersect(self, *others):
      if (self.onconflicts in ("first", "last")) or (len(others) <= 1):
         self &= others[0]
         return self
      common_keys = set(self.keys())
      #print("keys in self: {}".format(common_keys))
      for other in others:
         DictAsSet._validate_other(other, "intersect")
         common_keys &= set(other.keys())
         self -= (self - other)
      if len(self) ==  len(common_keys):
         return self
      else:
         conflicts = common_keys - set(self.keys())
         msg = "intersection failed."
         return self.handle_conflicts(msg, self, conflicts, others)

   def union(self, *others):
      answer = self.copy()
      answer.update_union(*others)
      return answer

   def update_union(self, *others):
      if self.onconflicts in ("first", "last") or len(others)<=1:
         for other in others:
            self.__iadd__(other)
         return self
      conflicts = set()
      for other in others:
         DictAsSet._validate_other(other, "union")
         new_conflicts = set()
         for key in other:
            if key in self:
               if self[key] != other[key]:
                  conflicts.add(key)
            else:
               self[key] = other[key]
         conflicts.update(new_conflicts)
      if len(conflicts) == 0:
         return self
      else:
         msg = "union failed"
         return self.handle_conflicts(msg, self, conflicts, others)


class DictConflictError(Exception):
   def __init__(self, msg, result, conflicts, sources):
      Exception.__init__(self, msg)
      self.result = result
      self.conflicts = conflicts
      self.sources = sources
