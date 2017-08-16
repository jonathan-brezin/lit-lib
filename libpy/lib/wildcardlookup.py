

from collections import defaultdict

class WildCardLookup():
   def __init__(self, *patterns):
      self.exactmatch = set()   # no wild cards
      self.pairs = defaultdict(set) # key == start of match; the value is the set of ends.
      self.cache = {}           # the results of previous match attempts
      self.matchall = False     # any key matches, if this is True
      if len(patterns) > 0:
         self.add(*patterns)

      
   def __contains__(self, key):
      if self.matchall:
         return True
      elif key in self.cache:
         return self.cache[key]
      elif key in self.exactmatch:
         self.cache[key] = True
         return True
      elif len(key) < 2: # wild card matches need at least one character beyond the pattern
         self.cache[key] = False
         return False
      else:
         for start in self.pairs:
            if key.startswith(start):
               restOfKey = key[len(start)+1:]
               for end in self.pairs[start]:
                  if restOfKey.endswith(end):
                     self.cache[key] = True
                     return True
         self.cache[key] = False
         return False

   def __len__(self):
      return len(self.exactmatch)+len(self.pairs)+(1 if self.matchall else 0)

   def add(self, *newPatterns):
      for newPattern in newPatterns:
         if type(newPattern) is not str:
            raise TypeError("Expected a key string, but got a {0}".format(type(newPattern)))
         added = [x.strip() for x in newPattern.split(',')]
         for pattern in added:
            if "*" not in pattern:
               self.exactmatch.add(pattern)
               if pattern in self.cache and not self.cache[pattern]:
                  self.cache[pattern] = True
            elif pattern == "*":
               self.matchall = True
            else:
               (start, end) = pattern.split('*')
               self.pairs[start].add(end)
               for cached in self.cache:
                  if not self.cache[cached]:
                     if cached.startswith(start) and cached[len(start)+1:].endswith(end):
                        self.cache[cached] = True

   def remove(self, *deadPatterns):
      resetTheCache = False
      for deadPattern in deadPatterns:
         parsed = [x.strip() for x in deadPattern.split(',')]
         for removed in parsed:
            #print("remove '{}'".format(removed))
            if removed is '*':
               self.matchall = False
            elif removed in self.exactmatch: 
               self.exactmatch.remove(removed)
               if removed in self.cache:
                  self.cache.pop(removed)
            else:
               (start, end) = removed.split('*')
               if start in self.pairs:
                  startSet = self.pairs[start]
                  if end in startSet:
                     startSet.remove(end)
                     if len(startSet) is 0:
                        self.pairs.pop(start)
                     resetTheCache = True
      if resetTheCache:
         # simplest guess: invalidate all positive entries in the cache.  It is no more
         # expensive to check the entries that would have survived if they are encountered
         # afterward as guards
         for key in self.cache:
            if self.cache[key]:
               self.cache.pop(key) 

   def patterns(self):
      all = set(self.exactmatch)
      if self.matchall: all.add("*")
      for start in self.pairs:
         for end in self.pairs[start]:
            all.add(start+"*"+end)
      return all

   def isdisjoint(self, other):
      return self.patterns().isdisjoint(other.patterns())

   def issubset(self, other):
      return self.patterns().issubset(other.patterns())

   def __eq__(self, other):
      return self.matchall==other.matchall and self.patterns() == other.patterns

   def __ne__(self, other):
      return self.matchall!=other.matchall or self.patterns() != other.patterns

   def __le__(self, other):
      return self.issubset(other)

   def __lt__(self, other):
      return self.issubset(other) and self.__ne__(other)

   def issuperset(self, other):
      return self.patterns().issuperset(other.patterns())

   def __ge__(self, other):
      return self.issuperset(other)

   def __gt__(self, other):
      return self.issuperset(other) and self.__ne__(other)

   def union(self, *others):
      asSet = self.patterns().union(*[other.patterns() for other in others])
      return WildCardLookup(*list(asSet))

   def __or__(self, other):
      return self.union(other)

   def intersection(self, *others):
      asSet = self.patterns().intersection(*[other.patterns() for other in others])
      return WildCardLookup(*list(asSet))

   def __and__(self, other):
      return self.intersection(other)

   def difference(self, *others):
      asSet = self.patterns().difference(*[other.patterns() for other in others])
      return WildCardLookup(*list(asSet))

   def __sub__(self, other):
      return self.difference(other)

   def symmetric_difference(self, other):
      asSet = self.patterns().symmetric_difference(other.patterns())
      return WildCardLookup(*list(asSet))

   def __xor__(self, other):
      return self.symmetric_difference(other)



   def strictestPatternFor(self, key):
      if key in self.exactmatch:
         # the exact match is definitely the strictest: look no further 
         return key
      allmatches = self.patternsMatching(key)
      if len(allmatches) is 0:
         return "*" if self.matchall else None
      else:
         sizes = [len(x) for x in allmatches]
         winner = sizes.index(max(sizes))
         return allmatches[winner]

   def weakestPatternFor(self, key):
      allmatches = self.patternsMatching(key)
      if len(allmatches) is 0:
         return "*" if self.matchall else None
      else:
         sizes = [len(x) for x in allmatches]
         winner = sizes.index(min(sizes))
         return allmatches[winner]
      return self._matchedBy(key, False)

   def patternsMatching(self, key):
      theList = []
      if key in self.exactmatch:
         theList.append(key)
      if len(key) < 2:
         return theList
      for start in self.pairs:
         if key.startswith(start):
            rest = key[len(start)+1:]
            for end in self.pairs[start]:
               if rest.endswith(end):
                  theList.append(start+"*"+end)
      theList.sort()
      return theList

   def anyMatched(self, *keys):
      if len(keys) is 0:
         raise ValueError("WildCardLookup.anyMatched requires at least one argument.")
      elif self.matchall:
         return True
      else:
         for entry in keys:
            tested = [x.strip() for x in entry.split(',')]
            for x in tested:
               if self.__contains__(x): # NB. uses my _contains_, not set's!!!
                  return True
         return False
         
   def allMatched(self, *keys):
      if len(keys) is 0:
         raise ValueError("WildCardLookup.allMatched requires at least one argument.")
      elif self.matchall:
         return True
      else:
         for entry in keys:
            tested = set(x.strip() for x in entry.split(','))
            for x in tested:
               if not self.__contains__(x):
                  return False
         return True



   def __iter__(self):
      sorted = list(self.patterns())
      sorted.sort()
      return sorted.__iter__()

