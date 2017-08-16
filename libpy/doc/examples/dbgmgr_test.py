#!/usr/bin/env python3.53.5

""" test the dbg module """

import dbg

with dbg.openDbgMgr("a, a_*, *b, a*b") as dbgmgr:
   dbgmgr.dbg("a", "Initializing the manager with a, a_*, *b, and a*b")
   print("Output to " + dbgmgr.path)
   buffered_messages = ''
   for buffered_message in dbgmgr: 
      buffered_messages += str(buffered_message)+" "
   dbgmgr.dbg("a", "dbgmgr buffered messages are '"+buffered_messages+"'")
   dbgmgr.dbg("a", "'a' in dbgmgr? {0}?  'c'? {1} 'acb'? {2}".format(
      'a' in dbgmgr, 'c' in dbgmgr, 'acb' in dbgmgr))

   def dbgcaller(dbgmgr):
      dbgmgr.err("I did something wrong\n   and here it is!", bail_out=False)
      dbgmgr.warn("You did something risky,\n   which is not a good idea")
      dbgmgr.dbg("first_b", "first b is in the live set: matched by {0}".format(
         dbgmgr.keypatterns.strictestPatternFor("first_b")))
      dbgmgr.dbg("ac", "ac is not in the live set")

   dbgcaller(dbgmgr)

   dbgmgr.raise_priority("HI!")
   dbgmgr.dbg("a", "the strict match for a_b is {0}, and weak is {1}".format(
      dbgmgr.keypatterns.strictestPatternFor("a_b"),
      dbgmgr.keypatterns.weakestPatternFor("a_b")
      ))

   def dbggohi(dbgmgr):
      dbgmgr.dbg("HI!", "Man, this is important!")

   dbggohi(dbgmgr)

   dbgmgr.flush(before="This should come first", after="This should come last")
   dbgmgr.pre("aandthenb", "This is a formatted message:\n   Bye!\nIt sits inside a &lt;pre&gt;")
   dbgmgr.flush(
      before="This starts a new list, but the indexing is not restarted",
      after="This ends the list"
   )
   dbgmgr.dbg("HI!", "That's all, folks!")