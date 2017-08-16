#! /usr/bin/env python
"""
Some simple exercises for inifile parsing: uses the file testdata/stuff.ini as the source for 
reading a single file, and testdata/attic/stuff.ini and testdata/cellar/stuff.ini as add-ons.
The debug keys for verbose output are "ini_key" and "ini_read".

A normal execution has rc=0 and produces no HTML output in the log other than that salient fact.
Any errors will be logged and left in a file in the `log` directory whose name has the format 
`dbg`_`date`_`.`_`gmt`_`.html`.  E.g.: `dbg20160819.182107.html`.

"""
from fileutils import *
from inifile import Inifile
from cmdlineparser import CmdLineParser
from dbg import openDbgMgr
import sys

def do_the_test(options):
   rc = 0
   with openDbgMgr(options.dbg) as dbgmgr:
      start_debug_fileutils()
      inifile = Inifile('testdata/stuff.ini')
      sectionNames = inifile.getsections()
      dbgmgr.dbg("ini_key", "Its sections are {0}".format(sectionNames))
      firstSectionName = "stuff fred"
      firstSection = inifile[firstSectionName]
      firstSectionPairs = [(key, firstSection[key]) for key in firstSection]
      firstSectionPairs.sort()
      dbgmgr.dbg("ini_key", "The key/value pairs in {0} are\n   {1}".format(firstSectionName, firstSectionPairs))
      if firstSection['first'] != "3\n5":
         dbgmgr.warn("'first' has the wrong value: \n{0}!".format(firstSection['first']), file=sys.stderr)
         rc = 1
      if not inifile.haskey(firstSectionName, "second"):
         dbgmgr.warn("Key `second` missing from {0}".format(firstSectionName), file=sys.stderr)
         rc |= 2
      data = inifile[firstSectionName]["second"]
      data_got = inifile.get(firstSectionName, "second", "huh?")
      if data != data_got:
         dbgmgr.warn("ini[stuff fred][second] != ini.get('stuff fred', 'second')", file=sys.stderr)
      if "secondx" in inifile["stuff fred"]:
         dbgmgr.warn("secondx found in `stuff fred`!", file=sys.stderr)
         rc |= 4
      if "more in default" not in inifile[""]:
         dbgmgr.warn("'more in default' not found in default key set!", file=sys.stderr)
         dbgmgr.dbg("ini_read", "The whole default key set is {0}".format([key for key in inifile[""]]))
         rc |= 8
      inifile.write(backups=10)
      ini = Inifile.readOne("stuff.ini", "'.:testdata/attic:testdata/cellar:testdata'") 
      ini = Inifile.readOptional("stuffed.ini", "'.:testdata/attic:testdata/cellar:testdata'",defaults="Missing!") 
      if ini != "Missing!":
         dbgmgr.warn("read optional got {0}, not None".format(ini))
         rc |= 16
      ini = Inifile.readAll("stuff.ini", ".:testdata/cellar:testdata/attic")
      if "third occupied" not in ini["stuff jane"]:
         dbgmgr.err("Did not file 'third occupied in 'self jane!")
         jane = ini["stuff jane"]
         pairs = [(key, jane[key]) for key in jane]
         pairs.sort()
         dbgmgr.dbg("ini_read", "stuff jane is\n   {0}".format(pairs))
   print("exit rc={0}".format(rc))
   sys.exit(rc)

if __name__ != '__main__': # we are testing this code from the command line
   print("This code is meant to be executed from the command line.")
   exit(127)

clp = CmdLineParser(prog='testini.py')
clp.add_a_str("-dbg", "", "turn on debug output")
options = clp.parse_args()
print("Infile test: {0}".format(options.dbg))
do_the_test(options)
