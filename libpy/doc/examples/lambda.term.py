x = 5

# assignment in a lambda raises a syntax error:

l = lambda y: (x = y)

# the cause really is the assignment, not the presence of "x"

l = lambda y: x*y
print("l(3) should be 15: ", l(3))
