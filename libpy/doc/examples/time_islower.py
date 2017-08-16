#!/usr/bin/env python3.5

"""

This code compares checking strings for "is lowercase" by using lower() on the whole string and
then comparing against the original, versus a per-character check in a loop and Python's own
builtin islower() (which presumably does a per char loop, too).

Console output for running this code, time in seconds on an otherwise idle iMac (21.5-inch, Late
2013, 2.7 GHz Intel Core i5, with 8G memory running Macos 10.12 (Sierra)):

$time_islower.py 10 10000 10
For 10000 strings of length 10, check repeated 10 times:
Per char time 55.122 ms, whole string time 32.779 ms.
Python time 20.658 ms.

"""

from random import randint as rnd, seed 
import sys
from time import time

def perChar(s):
   for c in s:
      if c.lower() != c: return False
   return True

def wholeStr(s):
   return s.lower() == s

stringLength = 10
stringCount  = 10000
repeatCount  = 10
if __name__ == '__main__':
   if len(sys.argv) >= 2:
      if sys.argv[1] in ["-?", "--help"]:
         print("Usage: time_islower.py [string length, string count [ repeat count]") 
         print("    Time the difference between per character and per string costs")
         print("    for checking whether a string is all lower case or not.\nDefaults:")
         print("        string length = 10, string count = 10000, repeat count = 10" )
         sys.exit(1)
      stringLength = int(sys.argv[1])
   if len(sys.argv) >= 3:
      stringCount = int(sys.argv[2])
   if len(sys.argv) >= 4:
      repeatCount = int(sys.argv[3])

the_range = range(0, stringLength)
alphabet = "abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ "
print("For {} strings of length {}, check repeated {} times:".format(stringCount, stringLength, repeatCount))
def newString():
   return "".join(alphabet[rnd(0, 53)] for n in the_range)
the_list = [newString() for n in range(0, stringCount)]

start_pc = time()
for m in range(0, repeatCount):
   for n in range(0, stringCount):
      perChar(the_list[n])
time_pc  = (time() - start_pc)*1000

start_ws = time()
for m in range(0, repeatCount):
   for n in range(0, stringCount):
      wholeStr(the_list[n])
time_ws  = (time() - start_ws)*1000

print("Per char time {:6.3f} ms, whole string time {:6.3f} ms.".format(time_pc, time_ws))

start_py = time()
for m in range(0, repeatCount):
   for n in range(0, stringCount):
      the_list[n].islower()
time_py  = (time() - start_py)*1000
print("Python time {:6.3f} ms.".format(time_py))

