# Illustrates some ways of providing attributes to an object that are not directly declared as such
# (whence "derived attributes").  Two examples: one using a "descriptor", and the other using 
# overrides for __getattribute__ and __setattr__.


class _area(object):                  # define a virtual attribute descriptor
   def __get__(self, obj, objtype):   # this will do the fetch of obj.area
      return obj.x*obj.y              # x and y are the rectangle's dimensions
   def __set__(self, obj, val):       # this handles assignment: obj.area = val
      raise AttributeError("Silly you... nothing here to set!")

class Rectangle(object):
   area = _area()                     # access to value is via the descriptor
   def __init__(self, x=1, y=1):
      self.x = x
      self.y = y

r = Rectangle(3,4)
print("r.area should be 12: it is {0}".format(r.area))
try:
   r.area = 15                        # should raise the exception
except AttributeError as ae:
   print("I tried to set r.area = 15: {0}".format(ae))

try:
   object.__setattr__(r, "area", "area")
except AttributeError as ae:
   print("Even object cannot change the area")

new_area = object.__getattribute__(r,'area')
print("r.area is {}".format(r.area))
print("object.__getattribute__(r,'area') is also {}".format(new_area))

class Rectangle2(object):
   def __init__(self, x=1, y=1):
      self.x = x
      self.y = y
   def __getattribute__(self, key):
      if key == "area":
         return self.x * self.y
      else:
         return object.__getattribute__(self, key)
   def __setattr__(self, key, value):
      if key == "area":
         raise AttributeError("Silly you... nothing here to set!")
      else:
         return object.__setattr__(self, key, value)

r2 = Rectangle2(5,6)
print("r2.area should be 30: it is {0}".format(r2.area))
try:
   r2.area = 25                       # should raise the exception
except AttributeError as ae:
   print("I tried to set r2.area = 25: {0}".format(ae))


object.__setattr__(r2, "area", "area") # creates a local attribute in r2
new_area2 = object.__getattribute__(r2,'area')
print("r2.area is {}".format(r2.area)) # calls the class's __getattribute__
print("but object.__getattribute__(r2,'area') is: {}".format(repr(new_area2)))
