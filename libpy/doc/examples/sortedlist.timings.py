#!/usr/bin/env python3.5

###
#
# This code exercises my SortedList, and compares it against blists, sortedlist (from blist), and
# plain vanilla Python lists.

from bisect import bisect_left
from blist import blist, sortedlist
from collections import defaultdict
from random import randint, seed
from sortedlist import SortedList
import sys
import sysutils as su
from time import time

m = int(sys.argv[1]) if len(sys.argv) > 1 else 512*1024
n = int(sys.argv[2]) if len(sys.argv) > 2 else 1024*1024
toShow = int(sys.argv[3]) if len(sys.argv) > 3 else 20
toAdd = int(sys.argv[4]) if len(sys.argv) > 4 else 16*1024
toDel = int(sys.argv[5]) if len(sys.argv) > 5 else 128
ourseed = 31416
generator = ((randint(0, m), randint(0,m)) for x in range(0, n))

##
#  The raw construction times
##

print("Initializing 4 lists with {} entries: this could take a while!".format(n))
print("The SortedList's threshold is the default: {}".format(SortedList().threshold))
seed(ourseed)
input = list(generator)
starta= time()
a = list(input)
a.sort(key = lambda x: x[0])
timea = time() - starta
seed(ourseed)
startb = time()
bl = blist((x for x in input))
bl.sort(key=lambda x: x[0])
timeb = time() - startb
startc = time()
c = SortedList((x for x in input), lambda x: x[0])
timec = time() - startc
startd = time()
sl = sortedlist(input, key=lambda x: x[0])
timed = time() - startd
print("Time for building a list and sorting {} random pairs ints in the range 0-{}:".format(n, m))
print("   {:6.3f} for a list,\n   {:6.3f} for a blist,\n   {:6.3f} for a SortedList and\n   {:6.3f} for a sortedlist.".format(timea, timeb, timec, timed))
#print(str(c[0:10])+"..."+str(c[-10:]))

##
#  Insertion times
##

ourseed = 271828
generator = ((randint(0, m), randint(0,m)) for x in range(0, toAdd))
input = list(generator)
seed(ourseed)
starta= time()
for pair in input: a.append(pair)
a.sort(key = lambda x: x[0])
timea = time() - starta
startb = time()
for pair in input: bl.append(pair)
bl.sort()
timeb = time() - startb
starts = time()
for pair in input: sl.add(pair)
times = time() - starts
startc = time()
for pair in input: c.append(pair)
c.restore_sorted_order()
timec = time() - startc
print("Time  to add {} items\n   {:6.3f} to the list,\n   {:6.3f} to the blist,\n   {:6.3f} to the sortedlist,\n   {:6.3f} to the SortedList.".format(toAdd, timea, timeb, times, timec))
c.set_threshold(fraction = 2/3, absolute=128*1024)
startc = time()
for k in range(0, toAdd): c.append((randint(0, m), randint(0,m)))
c.restore_sorted_order()
timec = time() - startc
print("Time {:6.3f} to add {} items to the SortedList with {} threshold.".format(timec, toAdd, c.threshold))
c.set_threshold(fraction = 3/4, absolute=128*1024)
startc = time()
for k in range(0, toAdd): c.append((randint(0, m), randint(0,m)))
c.restore_sorted_order()
timec = time() - startc
print("Time {:6.3f} to add {} items to the SortedList with {} threshold.".format(timec, toAdd, c.threshold))

##
#  Deletion times
##

len_a = len(a)
dead_list = (a[randint(0, len_a-toDel)] for x in range(0, toDel))
dead_set = set(dead_list)
starta= time()
for dead in dead_set: a.remove(dead)
timea = time() - starta
startb = time()
for dead in dead_set: bl.remove(dead)
timeb = time() - startb
starts = time()
for dead in dead_set: sl.remove(dead)
times = time() - starts
startc = time()
for dead in dead_set: c.remove(dead)
timec = time() - startc
print("Time to remove {} items\n  {:6.3f} from the list,\n  {:6.3f} from the blist,\n  {:6.3f} from the sortedlist,\n  {:6.3f} from the SortedList.".format(toDel, timea, timeb, times, timec))

##
#  Access times
##

dummy = 0
seed(ourseed)
startr = time()
lasta = len(a)-1
for n in range(0, len(a)):
   dummy |= randint(0, lasta)
timer = time() - startr
seed(ourseed)
starta = time() + timer
for n in range(0, len(a)):
   dummy |= a[randint(0, lasta)][0]
timea = time() - starta
seed(ourseed)
startb = time() + timer
for n in range(0, len(a)):
   dummy |= bl[randint(0, lasta)][0]
timeb = time() - startb
seed(ourseed)
starts = time() + timer
for n in range(0, len(a)):
   dummy |= sl[randint(0, lasta)][0]
times = time() - starts
seed(ourseed)
startc = time() + timer
for n in range(0, len(a)):
   dummy |= c[randint(0, lasta)][0]
timec = time() - startc
print("Time to read {} items by index: \n   {:6.3f} from the list,\n   {:6.3f} from the blist,\n   {:6.3f} from the sortedlist,\n   {:6.3f} from the SortedList.".format(len(a), timea, timeb, times, timec))

##
# Iteration times
##

starta = time()
for item in a:
   dummy |= item[0]
timea = time() - starta
startb = time()
for item in bl:
   dummy |= item[0]
timeb = time() - startb
starts = time()
for item in sl:
   dummy |= item[0]
times = time() - startb
startc = time()
for item in c:
   dummy |= item[0]
timec = time() - startc
print("Time to iterate over {} items\n   {:6.3f} from the list,\n   {:6.3f} from the blist,\n   {:6.3f} from the sortedlist,\n   {:6.3f} from the SortedList.".format(len(a), timea, timeb, times, timec))
startd = time()
for k in range(0, len(c)):
   dummy |= c[k][0]
timed = time() - startd
print("Time {:6.3f} for iterating over a sortedlist by index k for k in a range of size {}".format(timed, len(c)))

##
#  Build times for SortedLists by adding to an empty list
##

d = SortedList(key=lambda x: x[0])
input = list(((randint(0, m), randint(0,m)) for x in range(0, n)))
starta = time()
for pair in input:
   d.add(pair)
timea = time() - starta
input.sort()
d = SortedList(key=lambda x: x[0])
startb = time()
for pair in input:
   d.add(pair)
timeb = time() - startb
d = SortedList(key=lambda x: x[0])
input.reverse()
startc = time()
for pair in input:
   d.add(pair)
timeb = time() - startc
print("Time for raw build of {} items that are initially\n    unsorted:{:6.3f},\n    sorted: {:6.3f},\n    reversed: {:6.3f}".format(len(d), timea, timeb, timec))
