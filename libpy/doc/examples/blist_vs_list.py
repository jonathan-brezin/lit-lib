#!/usr/bin/env python3.53.5

from blist import blist
from collections import deque
import time

a = [x for x in range(0, 1000000)]
b = blist(a)
d = deque(a)
print("Comparing a list of length {:8.3f} with a blist and a deque of the same length".format(len(a)))
print("This could take a while... be patient.\n")

sum = 0
h = [x for x in range(0,1000000)]
starta = time.time()
for n in h:
   sum |= a[n]
stopa = time.time()
startb = time.time()
for n in h:
   sum |= b[n]
stopb = time.time()
startc = time.time()
for n in h:
   sum |= d[n]
stopc = time.time()

print("Random read access")
print("list accesses time:  {:8.3f}".format(stopa - starta))
print("blist accesses time: {:8.3f}".format(stopb - startb))
print("deque accesses time: {:8.3f}".format(stopc - startc))

sum = 0
starta = time.time()
for n in h:
   sum |= a[0]
stopa = time.time()
startb = time.time()
for n in h:
   sum |= b[0]
stopb = time.time()
startc = time.time()
for n in h:
   sum |= d[0]
stopc = time.time()
headTimes = [stopa - starta, stopb - startb, stopc - startc]

print("\nRead the queue head")
print("list accesses time:  {:8.3f}".format(stopa - starta))
print("blist accesses time: {:8.3f}".format(stopb - startb))
print("deque accesses time: {:8.3f}".format(stopc - startc))

starta = time.time()
a = []
for n in range(0, 1000000):
   a.append(n)
stopa = time.time()
startb = time.time()
b = blist()
for n in range(0, 1000000):
   b.append(n)
stopb = time.time()
startc = time.time()
d = deque(maxlen=1000000)
for n in h:
   d.append(n)
stopc = time.time()
appendTimes = [stopa - starta, stopb - startb, stopc - startc]

print("\nAppending to the collection")
print("list appending time:  {:8.3f}".format(stopa - starta))
print("blist appending time: {:8.3f}".format(stopb - startb))
print("deque appending time: {:8.3f}".format(stopc - startc))

starta = time.time()
for n in range(0, 1000000):
   a[n] = n
stopa = time.time()
startd = time.time()
for n in range(0, len(d)):
    b[n] = n
stopd = time.time()
starte = time.time()
for n in range(0, len(d)):
   d[n] = n
stope = time.time()

print("\n{} updates times".format(len(d)))
print("list update  time: {:8.3f}".format(stopa - starta))
print("blist update time: {:8.3f}".format(stopd - startd))
print("deque update time: {:8.3f}".format(stope - starte))

k = [x for x in range(0,100000, 10)]
starta = time.time()
for n in k:
   del a[0]
stopa = time.time()

startb = time.time()
for n in k:
   del b[0]
stopb = time.time()

startc = time.time()
for n in h:
   del d[0]
stopc = time.time()
deleteTimes = [stopa - starta, stopb - startb, stopc - startc]


print("\nRemoving the first element the collection")
print("list deletion time:  {:8.3f}".format(stopa - starta))
print("blist deletion time: {:8.3f}".format(stopb - startb))
print("deque deletion time: {:8.3f}".format(stopc - startc))

print("\nTotal peek plus append plus delete times:")
print("list time:  {:8.3f}".format(headTimes[0]+appendTimes[0]+deleteTimes[0]))
print("blist time: {:8.3f}".format(headTimes[1]+appendTimes[1]+deleteTimes[1]))
print("deque time: {:8.3f}".format(headTimes[2]+deleteTimes[2]+appendTimes[2]))

