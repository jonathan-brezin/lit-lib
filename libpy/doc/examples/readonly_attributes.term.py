# from a terminal, invoke python and Ctrl-c Ctrl-v this file into the terminal session

# This is an example of introducing one's own __setattr__ to prohibit setting an
# attribute.  The solution here does not stop you from adding readable attributes later,
# and as this code shows, adding the read-write attribute does not change the type of the
# object.

class Rect: 
   def __init__(self, x, y):
      self.x = x
      self.y = y      
   def area(self): return self.x * self.y
   def perimeter(self): return 2*(self.x + self.y)

r = Rect(4,5)
[r.x, r.y, r.area(), r.perimeter()] # should print [4, 5, 20, 18]

class RORect(Rect):           # delegates to a Rect that is otherwise hidden
   def __init__(self, x, y):  # use the usual __setattr__ to initialize self._r
      object.__setattr__(self, "x", x)
      object.__setattr__(self, "y", y)
   def __setattr__(self, name, value): # assigns to an RORect attribute
      if name in set(("area", "perimeter", "x", "y")):
         raise AttributeError("RORect.{0} is read-only".format(name))
      else: # all other cases are attributes added at runtime
         object.__setattr__(self, name, value)

ro = RORect(7,8)
[ro.x, ro.y, ro.area(), ro.perimeter()] # [7, 8, 56, 30]
try:
   ro.x = 21  # this had better throw an AttributeError!
except AttributeError as ae:
   print("I told you so: {}".format(ae))

ro.z = 3   # I have done nothing to stop you from adding read-write attributes
ro.z       #  ... the value should be 3

rp = RORect(9,10)               # here is a pure, untouched RORect
sametype = type(ro) is type(rp) # True, even though rp has no 'z' attribute
print("ro and rp have the same type? {}".format(sametype))

# __getattribute__ was not overwritten for RORect, so object.__setattr__ can hurt you!
object.__setattr__(ro, "area", "Yes!")
print("ro.area got zapped: {}".format(ro.area))

