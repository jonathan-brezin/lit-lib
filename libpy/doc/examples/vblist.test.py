#!/usr/bin/env python3.5

from vblist import *
from dbg import openDbgMgr
from delegator import *
from sysutils import owndir

with openDbgMgr("vblist") as dbgmgr:
   q = vbqueue(maxsize = 4)
   q.start_debugging()
   q.add(1)
   print("A single entry queue: {}".format(q))
   print("Here are its attributes: {}".format(owndir(q)))
   q.extend([2,3,4])
   print("Now with 1 through 4: {}".format(q))
   print("In loop should have 4 lines printed:")
   for n in q:
      print("   {}".format(n))
   print("q[3] = {}. It should be 4.".format(q[3]))
   if q.add(5, dieOnFail=False):
      print("Add to full queue succeeded: {}".format(q))
   else:
      print("Add to full queue failed gracefully")
   try:
      q.add(6)
      print("Added 6: {}".format(q))
   except BufferSizeError as e:
      print("add to a full queue failed: {}".format(e))
   print("Removing {} from the queue, leaving {}".format(q.next(), q))
   print("Trying next_or_else(howMany=3): get {}, leaving {}".format(q.next_or_else(howMany=3), q))
   try:
      q.next()
   except Exception as e:
      print("Empty queue: {}".format(e))
   try:
      print("next_or_else says hello: {}".format(q.next_or_else(orElse="Hi!")))
   except Exception as e:
      print("next_or_else failed. {}".format(e))
   print("------------------------------------------------")

   vbdeque.start_debugging()
   dq = vbdeque(maxsize = 4)
   dq.add(1)
   print("A single entry deque: {}".format(dq))
   dq.extend([2,3,4])
   print("Now with 1 through 4: {}".format(dq))
   print("In loop should have 4 lines printed:")
   for n in dq:
      print("   {}".format(n))
   print("dq[3] = {}. It should be 4.".format(dq[3]))
   if dq.add(5, dieOnFail=False):
      print("Add to full deque succeeded: {}".format(dq))
   else:
      print("Add to full deque failed gracefully")
   try:
      dq.add(6)
      print("Added 6: {}".format(dq))
   except BufferSizeError as e:
      print("add to a full deque failed: {}".format(e))
   print("Removing {} from the deque, leaving {}".format(dq.next(), dq))
   print("Trying next_or_else(howMany=3): get {}, leaving {}".format(dq.next_or_else(howMany=3), dq))
   try:
      dq.next()
   except Exception as e:
      print("Empty deque: {}".format(e))
   try:
      print("next_or_else says hello: {}".format(dq.next_or_else(orElse="Hi!")))
   except Exception as e:
      print("next_or_else failed. {}".format(e))
   dq.add(5.6)
   dq.prepend([1.2,3.4])
   print("After prepending [1.2,3.4]: {}".format(dq))
   print("------------------------------------------------")
   
   vbstack.start_debugging()
   stk = vbstack(maxsize = 4)
   stk.add(1)
   print("A single entry stack: {}".format(stk))
   stk.extend([2,3,4])
   print("Now with 1 through 4: {}".format(stk))
   print("In loop should have 4 lines printed:")
   for n in stk:
      print("   {}".format(n))
   print("stk[3] = {}. It should be 4.".format(stk[3]))
   if stk.push(5):
      print("Add to full stack succeeded: {}".format(stk))
   else:
      print("Add to full stack failed gracefully")
   try:
      stk.push(6)
      print("Added 6: {}".format(stk))
   except BufferSizeError as e:
      print("add to a full stack failed: {}".format(e))
   print("Removing {} from the stack, leaving {}".format(stk.next(), stk))
   print("Trying next_or_else(howMany=3): get {}, leaving {}".format(stk.next_or_else(howMany=3), stk))
   try:
      stk.next()
   except Exception as e:
      print("Empty stack: {}".format(e))
   try:
      print("next_or_else says hello: {}".format(stk.next_or_else(orElse="Hi!")))
   except Exception as e:
      print("next_or_else failed. {}".format(e))
   try: 
      stk.extend([1.2,3.4])
      print("After appending [1.2,3.4]: {}".format(stk))
   except Exception as e:
      print("extend failed: {}".format(e))
   print("------------------------------------------------")

   ## An example: the <code>typed_vblist</code> class

   ## Instances use the vetting function to assure that every entry has the correct type.

   class typed_vblist(vblist):
      def __init__(self, aType, iterable=[], maxsize = sys.maxsize, allowConversion=False):
         def vetter(data):
            print("Vet {}".format(data))
            if not isinstance(data, aType):
               if allowConversion:
                  return aType(data)
               else:
                  msg = "Data {2} of type {0} offered, but type {1} is expected."
                  DbgMgr().err(ValueError(msg.format(type(data), aType, data)))
            else: 
               return data
         super().__init__(iterable, maxsize = maxsize, vet = vetter)

   typed_vblist.start_debugging()
   tvbl = typed_vblist(int, allowConversion=True)

   tvbl = typed_vblist(int, maxsize = 4, allowConversion=True)
   tvbl.add(1)
   print("A single entry typed list: {}".format(tvbl))
   tvbl.extend([2,3,4])
   print("Now with 1 through 4: {}".format(tvbl))
   print("In loop should have 4 lines printed:")
   for n in tvbl:
      print("   {}".format(n))
   print("tvbl[3] = {}. It should be 4.".format(tvbl[3]))
   if tvbl.push(5):
      print("Add to full typed list succeeded: {}".format(tvbl))
   else:
      print("Add to full typed list failed gracefully")
   try:
      tvbl.push(6)
      print("Added 6: {}".format(tvbl))
   except BufferSizeError as e:
      print("add to a full typed list failed: {}".format(e))
   print("Removing {} from the typed list, leaving {}".format(tvbl.next(), tvbl))
   print("Trying next_or_else(howMany=3): get {}, leaving {}".format(tvbl.next_or_else(howMany=3), tvbl))
   try:
      tvbl.next()
   except Exception as e:
      print("Empty typed list: {}".format(e))
   try:
      print("next_or_else says hello: {}".format(tvbl.next_or_else(orElse="Hi!")))
   except Exception as e:
      print("next_or_else failed. {}".format(e))
   try: 
      tvbl.extend([1.2,3.4])
      print("After appending [1.2,3.4]: {}".format(tvbl))
   except Exception as e:
      print("extend failed: {}".format(e))
   try:
      tvbl.add("abc")
      print("Did not know 'abc' is an int literal! {}".format(tvbl))
   except Exception as e:
      print("adding 'abc' failed:\n\t{}".format(e))

   print("------------------------------------------------")

   @Static_Delegator("_vbq", source=vbqueue, excluded=set(
      ("add", "append", "extend", "insert", "push")
   ))
   class queue_that_grows:
      def __init__(self, iterator=[], maxsize = sys.maxsize, vet = None):
         object.__setattr__(self, "_vbq", vbqueue(iterator, maxsize, vet))
         self._vbq.start_debugging()


      def _handle_overflow(self, new_data, one_only):
         new_size = round(self._vbq.maxsize * 1.5)
         print("Enlarging queue limit from {} to {}".format(self._vbq.maxsize, new_size))
         object.__setattr__(self, "_vbq", vbqueue(self._vbq, new_size, self._vbq.vet))
         return self.add(new_data) if one_only else self.extend(new_data)

      def add(self, what):
         try:
             return self._vbq.add(what)
         except BufferSizeError as err:
            return self._handle_overflow(what, True)

      def append(self, what): return self.add(what)

      def extend(self, iterable):
         try:
            self._vbq.extend(iterable)
         except BufferSizeError as err:
            return self._handle_overflow(iterable, False)

      def push(self, what): return self.push(what)

      def __str__(self):
         inherited = self._vbq.__str__()
         tail = inherited[inherited.find('('):]
         return self.__class__.__name__+tail

   qtg = queue_that_grows([1,2,3,4], maxsize=5)
   print("qtg._vbq is {}".format(qtg))
   qtg.add(5)
   print("add 5 to qtg, getting: {}".format(qtg))
   qtg.add(6)
   print("add 6 to qtg, getting: {}".format(qtg))
   qtg.extend([7,8,9])
   print("add [7,8,9] to qtg, getting: {}".format(qtg))

