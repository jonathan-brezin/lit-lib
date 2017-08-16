## the magic __eq__ method is only respected when it is a class method
## Copy all and execute in a terminal session.

class Foo:
   def __eq__(self, other):
      return "who cares"
   def __init__(self, x, y):
      self.x = x
      self.y = y
      self.__eq__ = lambda b: "the instance cares"

foo1 = Foo(1, 2)
foo2 = Foo(1, 2)
foo1 == foo2
foo1.__eq__(foo2)
