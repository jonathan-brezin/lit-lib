#!/usr/bin/env python3.5

class A:
   a = "A"
   @classmethod
   def myname(self): print(self.__name__)
   @classmethod
   def set_a(self, value): self.a = value
   def set_x(self, value):
      self.__class__.x = value
   def __init__(self):
      self.a = "something different"

class B(A):
   @classmethod
   def parent(self): A.myname()

# Subclassing is a little clumsy...

A.myname() # A
B.parent() # A
B.myname() # B

# But instances setting class variables works as you would guess

a = A()
a.set_x("i am 'a'")
print("A.x is '{}'".format(A.x)) # 'a'
b = B()
b.set_x("i am 'b'")
print("A.x is '{}'".format(A.x)) # still 'a'
print("B.x is '{}'".format(B.x)) # 'b'

# And class attributes are copy on write:

print("A.a is '{}'".format(A.a))
A.set_a("set by A")
print("after reset: A.a is '{}'".format(A.a))
print("meanwhile a.a is '{}'".format(a.a))
B.set_a("set by B")
print("after set by B: A.a is '{}'".format(A.a))
print("and B.a is '{}'".format(B.a))
print("You can use b.a as well: '{}'".format(b.a))

