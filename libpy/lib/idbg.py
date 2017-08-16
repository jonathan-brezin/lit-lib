

import dbg
import inspect
import sys
from sysutils import asboolean

class DbgClient:

   @staticmethod
   def mycallersname(): 
      return inspect.currentframe().f_back.f_back.f_code.co_name

   @classmethod
   def configure_debugging(self, key, pattern=None, active=False):
      self._dbgmgr = dbg.getDbgMgr()
      if (getattr(self, "_dbg_default_key", None) is not None) and ('dbgmgr' in self._dbgmgr):
         if key != self._dbg_default_key or pattern != self._dbg_default_pattern:
            fmt = "Debugging {} reconfigured {}=>{} and {}=>{}"
            msg = fmt.format(
               self, self._dbg_default_key, key, self._dbg_default_pattern, pattern
            )
            self._dbgmgr.warn(msg)
      active = asboolean(active)
      self._dbg_class_active = active     # the class is ready to stream
      self._dbg_default_active = active   # by default, so are all new instances
      self._dbg_default_key = key         # use this key by default in requests
      self._dbg_default_pattern = key if pattern is None else key # match against this 

   @classmethod
   def start_debugging(self, *patterns, styles={}):
      self._dbg_default_active = True
      self._dbg_class_active = True
      if len(patterns) is 0:
         self._dbgmgr.add_patterns(self._dbg_default_pattern)
      else:
         self._dbgmgr.add_patterns(patterns)
      for name in styles:
         self._dbgmgr.addstyleclass(name, styles[name])

   @classmethod
   def pause_debugging(self, *patterns):
      self._dbg_default_active = False
      self._dbg_class_active = False
      if len(patterns) is 0:
         self._dbgmgr.remove_patterns(self._dbg_default_pattern)
      else:
         self._dbgmgr_.remove_patterns(patterns)

   @classmethod
   def stop_debugging(self, final_msg=""):
      self._dbgmgr.close(after=final_msg)
      self._dbg_default_active  = False

   @classmethod
   def dbg_class_is_active(self):
      return self._dbg_class_active

   @classmethod
   def dbg_activate_class(self):
      self._dbg_class_active = True
   
   @classmethod
   def dbg_deactivate_class(self):
      self._dbg_class_active = False
   
   @classmethod
   def dbg_default_is_active(self):
      return self._dbg_default_active

   @classmethod
   def dbg_set_default_active_state(self, active = True):
      self._dbg_default_active = asboolean(active)
      return self._dbg_default_active

   @classmethod
   def raise_an_error(self, anError, *, bail_out=True, esc=False):
      if self._dbg_class_active:
         self._dbgmgr.err(anError, src=DbgClient.mycallersname())
      elif isinstance(anError, Exception):
         raise anError
      else:
         raise RuntimeError(anError)

   @classmethod
   def issue_a_warning(self, aWarning, *, bail_out=True, esc=False):
      if self._dbg_class_active:
         self._dbgmgr.warn(aWarning, src=DbgClient.mycallersname())
      elif bail_out:
         if isinstance(aWarning, Exception):
            raise aWarning
         else:
            raise RuntimeError(aWarning)
      else:
         print(aWarning, file=sys.stderr)

   @classmethod
   def dbg_write_msg(self, msg, *, 
      key=None, src=None, pre=False, style=None, now=False, esc=False
   ):
      if self._dbg_class_active:
         key = key or self._dbg_default_key
         caller = src or self.mycallersname()
         if pre:
            self._dbgmgr.pre(key, msg, src=caller, style=style, now=now)
         else:
            self._dbgmgr.dbg(key, msg, src=caller, style=style, now=now)

   ####### Instance Methods #######

   def dbg_activate(self, *patterns, default_also=False):
      if len(patterns) > 0:
         self._dbgmgr.add_patterns(*patterns)
      self._dbg_instance_active = True
      if default_also:
         self.__class__._dbg_default_active = True

   def dbg_deactivate(self, default_also=False):
      self._dbg_instance_active = False
      if default_also:
         self.__class__._dbg_default_active = False

   def dbg_is_active(self):
      return getattr(self, "_dbg_instance_active", self._dbg_default_active)

   def raise_error(self, anError, *, bail_out=True, esc=False):
      if self.dbg_is_active():
         self._dbgmgr.err(anError, src=DbgClient.mycallersname(), bail_out=bail_out)
      elif isinstance(anError, Exception):
         raise anError
      else:
         raise RuntimeError(anError)
  
   def issue_warning(self, aWarning, *, bail_out=False, esc=False):
      if self.dbg_is_active():
         self._dbgmgr.warn(aWarning, src=DbgClient.mycallersname())
      elif bail_out:
         if isinstance(aWarning, Exception):
            raise aWarning
         else:
            raise RuntimeError(aWarning)
      else:
         print(aWarning, file=sys.stderr)

   def dbg_write(self, msg, *, 
         key=None, src=None, pre=False, style=None, now=False, esc=False
   ):
      if not self.dbg_is_active():
         return False
      caller = src or self.mycallersname()
      self.__class__.dbg_write_msg(msg,key=key,src=caller,pre=pre,style=style,now=now,esc=esc)
      return True

