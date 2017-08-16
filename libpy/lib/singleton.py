import sysutils as su


def _copy(self): 
   msg = "'{}' is a singleton class: no copy allowed!"
   raise AssertionError(msg.format(self.__class__.__name__))

def _deepcopy(self, memo):
      msg = "'{}' is a singleton class: no deep copy allowed!"
      raise AssertionError(msg.format(self.__class__.__name__))

def _inhibit_copy(cls):
   # If cls implements __copy__ or __deepcopy__, well so be it! I will leave it alone.
   # If not, I will provide an implementation that raises an appropriate exception.
   try:
      cls.__copy__
   except AttributeError:
      cls.__copy__ = _copy
   try:
      cls.__deepcopy__
   except AttributeError:
      cls.__deepcopy__ = _deepcopy

class OnlyOne(type):
   instances = dict()
   def __call__(cls, *args, **kwargs):
      if cls.__name__ not in OnlyOne.instances:
         OnlyOne.instances[cls.__name__] = type.__call__(cls, *args, **kwargs)
         _inhibit_copy(cls)
      return OnlyOne.instances[cls.__name__]


class OneAndOnly(object):
   def __init__(self, cls):
      self.__dict__['cls'] = cls # make cls's dict available
      _inhibit_copy(cls)
   instances = {}
   def __call__(self):
      if self.cls not in self.instances:
         self.instances[self.cls] = self.cls()
         _inhibit_copy(self.cls)
      return self.instances[self.cls]
   def __getattr__(self, attr):
      return getattr(self.__dict__['cls'], attr)
   def __setattr__(self, attr, value):
      return setattr(self.__dict__['cls'], attr, value)


class OneOnly(object):
   def __init__(self, cls):
      self._cls = cls
      self._instance = cls()
      _inhibit_copy(cls)
   def get(self):
      return self._instance 
   def __call__(self): # make sure the constructor for the singleton class fails
      raise AssertionError("'{}' is a singleton class".format(self._cls.__name__))

