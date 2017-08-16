#!/usr/bin/env python3.5

from dbg import openDbgMgr
from idbg import DbgClient

class ShoppingCart(DbgClient):
   @classmethod
   def prepare_for_debugging(self):
      self.configure_debugging("sc", "sc")
      CART_STYLE = """{color: #000000; background-color: #00FF00; font-weight: bold;
         border: 2px solid green; margin-left: 1em;}
         """
      self._dbgmgr.addstyleclass("cart", CART_STYLE) 

   def cart_output(self, guard_key, msg, *, pre=False, src=None):
      if not src: src = self.mycallersname()
      self.dbg_write(msg, key=guard_key, pre=pre, src=src, style="cart")

   def try_before_you_buy(self):
      self.cart_output("sc", "I'm a cart talking")
      self.dbg_write("I'm debug output" )
      self.stop_debugging("Good buy now!")

###                                                                         ###
#                                                                             # 
# Try commenting out the first two lines below and executing the command as   #
#        dbgmsg.py 2>stuff.html                                               #
# You should get the same output as before, but now in the file "stuff.html". #
#                                                                             #
###                                                                         ###
dbgmgr = openDbgMgr()
print("Output to {}".format(dbgmgr.get_path()))
ShoppingCart.prepare_for_debugging()
sc = ShoppingCart()

sc.dbg_write("You should not see this") # no keys yet

sc.start_debugging() # turn on the key and the default is now "active"
print("ShoppingCart class is active? {}".format(ShoppingCart.dbg_class_is_active()))
ShoppingCart.dbg_write_msg("You should see this")
try:
   ShoppingCart.raise_an_error(ValueError("Bad class value"))
except:
   pass
try:
   sc.raise_error(ValueError("Bad instance value"))
except:
   pass
print("sc instance is active is {}".format(sc.dbg_is_active()))
sc.dbg_write("This you should see")
sc.dbg_deactivate()
print("'I am an inactive instance' should not get logged, but following class message should")
sc.dbg_write('I am an inactive instance')
ShoppingCart.dbg_write_msg("I am an active class")
sc.dbg_activate()
sc.try_before_you_buy()
print("done")
