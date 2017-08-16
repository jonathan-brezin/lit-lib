# The statement "class C:" creates a variable named C and a class object named C
class C:
   def __init__(self, x):
      self.x = x

d = C # d is now the class object
C = 2 # C, the variable, now has value 2
print("C is", C, ", d(5).x is", d(5).x)
print("d(5)'s class's name is", d(5).__class__.__name__)

# Functions work the same way: "def fcn(...):" creates both a function object and variable to hold
# that object.
def fcn(x,y):
   return x*y - x - y

g = fcn
fcn = 4
print("fcn is {}, {}(2,3) is {}".format( fcn, g.__name__, g(2,3)))

