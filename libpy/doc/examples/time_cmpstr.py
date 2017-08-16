#!/usr/bin/env python3.5
""" 

This code compares indexing into a string versus using the builtin __lt__ method for computing the
C/Unix style "cmp()". 

Console output for running this code, time in seconds on an otherwise idle iMac (21.5-inch, Late
2013, 2.7 GHz Intel Core i5, with 8G memory running Macos 10.12 (Sierra)):

$time_cmpstr.py 16000
For 16000 comparisons, 3 <= length <= 20:
   Lists computed, comparisons about to start.
Total time in seconds: mine =  0.016, Python =  0.005
Microseconds per call: mine:  0.978, python:  0.320
The ratio mine/python is 305%

$time_cmpstr.py 160000 10 100
For 160000 comparisons, 10 <= length <= 100:
   Lists computed, comparisons about to start.
Total time in seconds: mine =  0.169, Python =  0.055
Microseconds per call: mine:  1.054, python:  0.346
The ratio mine/python is 304%

$time_cmpstr.py 2500 1000 1500
For 2500 comparisons, 1000 <= length <= 1500:
   Lists computed, comparisons about to start.
Total time in seconds: mine =  0.003, Python =  0.001
Microseconds per call: mine:  1.215, python:  0.468
The ratio mine/python is 259%

Seems like C is three times as fast here as pure Python, a little less so for long strings, as one
would expect (since the indexing approach only does one comparison on average for every 1.5
comparisons using the built-in operators).

"""

def usemy(left, right):
   lenOfLeft  = len(left)
   lenOfRight =  len(right)
   for n in range(0, lenOfLeft if lenOfLeft <= lenOfRight else lenOfRight):
      if left[n] < right[n]:
         return -1
      elif left[n] > right[n]:
         return 1
   return 0 if lenOfRight == lenOfLeft else (-1 if lenOfRight > lenOfLeft else 1)

def usepy(left,right):
   return -1 if left < right else (1 if left > right else 0)

alphabet = "abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ "

from random import randint as rnd, seed 
import sys
from time import time

smallest = 3
largest  = 20
repeats  = 10000
if __name__ == '__main__':
   if len(sys.argv) >= 2:
      if sys.argv[1] in ["-?", "--help"]:
         print("Usage: time_cmpstr.py [repeats [ smallest [ largest]]]") 
         print("    This runs 'repeats' different comparisons of strings of")
         print("    length between 'smallest' and 'largest'.  Defaults:")
         print("        repeats=10,000,  smallest=3, and largest=20" )
         sys.exit(1)
      repeats = int(sys.argv[1])
   if len(sys.argv) >= 3:
      smallest = int(sys.argv[2])
   if len(sys.argv) >= 4:
      largest = int(sys.argv[3])

def rnd_size():
   return rnd(smallest, largest)

the_range = range(0, repeats)
print("For {} comparisons, {} <= length <= {}:".format(repeats, smallest, largest))

left_list = [''.join(alphabet[rnd(0, 53)] for n in range(0, rnd_size())) for n in the_range]
right_list =  [''.join(alphabet[rnd(0, 53)] for n in range(0, rnd_size())) for n in the_range]

print("   Lists computed, comparisons about to start.")
start_me = time()
for n in range(0, repeats):
   usemy(left_list[n], right_list[n])
my_time = time() - start_me

start_py = time()
for n in the_range:
   usepy(left_list[n], right_list[n])
py_time = time() - start_py

my_msec = (my_time * 1000000)/repeats
py_msec = (py_time * 1000000)/repeats

print("Total time in seconds: mine = {:6.3f}, Python = {:6.3f}".format(my_time, py_time))
print("Microseconds per call: mine: {:6.3f}, python: {:6.3f}".format(my_msec, py_msec))
print("The ratio mine/python is {}%".format(int(100*my_time/py_time)))
sys.exit(0)

