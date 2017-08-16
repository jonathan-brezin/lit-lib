#! /usr/bin/env python

# it will run, but it is better to select all, and then copy into python terminal session

from dictasset import * 
import sysutils as su 

das1 = DictAsSet(((1,2), (3,4), (5,6)))
das2 = DictAsSet(((5,6), (7,8), (9,10)))
das1 + das2
das3 = das1.copy()
das3 += das2
das3

das4 = das1 - das2
das4
das8 = das1.copy()
das8 -= das2
das8

das5 = das4 ^ das2
das5
das6 = das4.copy()
das6 ^= das2
das6

das1 & das2
das7 = das1.copy()
das7 &= das2
das7

das9 = DictAsSet(((3,5), (12,13)))
try:
   das10 = das9 & das1
except Exception as e:
   print("Conflicts: ", e.conflicts)
   print(e.__class__.__name__+":", e)

das5.isdisjointfrom(das1&das2)

das4 < das1
das4 > das1
das1 <= das1
das1 == das1
das1 != das1
das9 < das1

das1.union(das2,das3,das4)
das2.intersect(das3, das4, das5)
das2.update_intersect(das3, das4, das5)
das2
try:
   das3
   das4
   das9
   das3.update_intersect(das4, das9)
except DictConflictError as e:
   print("Conflicts: ", e.conflicts)
   print(e.__class__.__name__+":", e)
except Exception as e:
   print(e.__class__.__name__+":", e)
   raise

try:
   das9
   das1
   das9 &= das1
except Exception as e:
   print("Conflicts: ", e.conflicts)
   print(e.__class__.__name__+":", e)

