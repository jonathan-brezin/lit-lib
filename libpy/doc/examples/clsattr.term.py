class C:
   pass

try:
   C.__setattr__(C, "bycall", "xxx") # same as C.bycall = "xxx"
except Exception as e:
   print("Whoops!", e)

C.bydot = "yyy"
print("C.bydot is", C.bydot)

c = C()
print("c.bydot is", c.bydot)