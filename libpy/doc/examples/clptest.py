#!/usr/bin/env python3.5

import cmdlineparser as clpmod
if __name__ != '__main__': 
   raise Exception("Command line needed")

# We are testing this code from the command line: add a flag and a key-value pair, etc
# Try python clptest.py -rh 31 to see that you can abbreviate long forms.

class CLPTest1:
   def __init__(self):
      pass
   def setCmdLineArgs(clp):
      clp.add_positional("first", help="first argument, required", type=int, choices=[1,2,3])
      clp.add_pair("second", help="i am two", type=int, default=54)
      clp.add_flag("-dbg", help="turn on debug output")
      clp.add_flag("-dbg", help="turn on debug output") # Error message!
      clp.add_pair("-rhdrs", "--r", help="number of header rows", type=int, default=31)
      clp.add_an_int("-s", 29, "number of sunny days")
      clp.add_a_float("--t", 2.7, "eeeeek!")
      clp.add_a_str("-u", "you", "who is here")
      # uncomment the next two lines to see these two attributes get overwritten
      #clp.add_an_int("-count", 77, "number of days")
      #clp.add_flag("-index", help="create an index") # Error message!
      clp.add_an_optional_list("others",  help="optional last argument")

options = clpmod.parse_args(CLPTest1, usage="Example of cmdlineparser usage: try clptest --help")

print("\noption tuple = {0}".format(options))
print("as a 'dict'  = {0}\n".format(clpmod.args_dict(options)))
#print("You cannot use the built-in function vars() on a namedtuple, though:")
#try:
#   print("   vars(options) = {0}".format(vars(options)))
#except Exception as e:
#   print("   vars(options) failed and raised: \"{0}\"".format(e))

print("The trailing list, options.others: {0}.\n".format(options.others))
msg = """Check options.index and options.count against the default values for -r and -dbg.
   options.index(31) is {0} and options.count(False) is {1}.
"""
if callable(options.index) and callable(options.count):
   print(msg.format(options.index(31),options.count(False)))
else:
   print("options.index is {0} and options.count is {1}\n".format(options.index, options.count))
print("This is the value for --rhdrs: {0}".format(options.rhdrs) )
try:
   print("   ... and this is the value for -r: {0}".format(options.r) )
   print("   Are they the same: {0}!".format( "Yes" if options.rhdrs==options.r else "No"))
except Exception as e:
   print("Getting the value for -r failed: {0}".format(e))
print("\nOne week longer than sunny days: -s value + 7 is {0}".format(options.s+7))
print("Bump -t by 0.715 to get pi: {0}".format(0.715 + options.t))

class CLPTest2:
   def __init__(self):
      pass
   def setCmdLineArgs(clp):
      clp.add_pair("--r+hdrs", help="number of header rows", type=int, default=31)
      clp.add_a_float("--t", 2.7, "eeeeek!")

try:
   options = clpmod.parse_args(CLPTest2, args="--t 5.9".split(), usage="bad attribute")
   print("Whew! Thought I'd die!")
except ValueError as ve:
   print(ve)
   options = clpmod.parse_args(CLPTest2, args="--t 5.9".split(), harden=False, usage="bad attribute")

print("\noption tuple = {0}".format(options))
print("as a 'dict'  = {0}\n".format(clpmod.args_dict(options)))
