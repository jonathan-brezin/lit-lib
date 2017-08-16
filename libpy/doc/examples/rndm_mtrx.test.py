#!/usr/bin/env python3.5

# Exercise the randomdist and nputils code
import math
import numpy as np
import nputils as npu
import randomdist as rndm 
import sysutils as su
#1) Create an matrix with uniform distribution; save it to "disc" and read it back in
#   Uses a uniform distribution and NumPy binary format

rd = rndm.RandomDist({'float': True, 'min':0, 'max': 100})

print("Create a random 3x3 matrix with uniform random integer entries and save as npy:")
path = 'testdata/array_3x3_int.npy'
matrix = rd.matrix(shape = (3,3), path=path, ext="npy")
print(npu.format_array(matrix, displaylimit=9, perline=3, formatter="{1:e}"))
print("Read it back in:")
(array, ignore, toss) = npu.readarray(path)
if npu.sameentries(matrix, array):
   print("   successful.")
else:
   relnorm = npu.supnorm(matrix-array)/npu.supnorm(matrix)
   print("   failed: relative sup norm of difference is  {:e}".format(relnorm))
   print("   The difference:")
   print(npu.format_array(abs(matrix-array), displaylimit=9, perline=3, formatter="{1:e}"))

#2) Create another matrix with uniform distribution; saveit to "disc" and read it back in
#   Uses a uniform distribution and my .tbl format: some loss of precision!

print("Create another 3x3 integer matrix and save it as a .tbl")
path = 'testdata/array_3x3_int.tbl'
matrix = rd.matrix(shape = (3,3), path=None, ext="npy")
rowheaders = np.array(["x", "y", "a", "b", "c"])
colheaders = np.array(["d", "e", "f", "g", "h", "i"]).reshape((3,2))
npu.writearray(path, matrix, rowheaders = rowheaders, colheaders = colheaders)
print("New array is:")
print(npu.format_array(matrix, displaylimit=9, perline=3, formatter="{1:e}"))
print("Read it back in:")
array, rhdrs, chdrs = npu.readarray(path)
if npu.sameentries(matrix, array):
   print("   successful.")
else:
   supnorm = npu.supnorm(matrix-array)/npu.supnorm(matrix)
   print("   failed: relative sup norm of difference is {:g}".format(supnorm))
   print("   The difference:")
   print(npu.format_array(abs(matrix-array), displaylimit=9, perline=3, formatter="{1:e}"))
print("   row headers: {}, column headers: {}".format(rhdrs, chdrs))

#3) Create another matrix with uniform distribution; saveit to "disc" and read it back in
#   Uses a uniform distribution and my .csv format: some loss of precision, but should
#   give the same read-back as the .tbl!

print("Now save the previous matrix as a .csv")
path = 'testdata/array_3x3_int.csv'
headers = "I am a table header"
footers = "I am a table footer\nI am the last footer"
npu.writearray(path, matrix, headers = headers, footers = footers, perline=3)
print("Read it back in and compare with the .tbl version:")
array2, hdrs, ftrs = npu.readarray(path)
if npu.sameentries(array, array2):
   print("   successful.")
else:
   supnorm = npu.supnorm(array-array2)/npu.supnorm(array)
   print("   failed: relative sup norm of difference is {:g}".format(supnorm))
   print("   The difference:")
   print(npu.format_array(abs(array-array2), displaylimit=9, perline=3, formatter="{1:e}"))
print("   headers: {}, footers: {}".format(hdrs, ftrs))
