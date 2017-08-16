
import functools
from dictasset import DictAsSet 
import sysutils as su
from types import new_class


def _tidy_up_and_assign(delegator, name, the_method, setter=None, deferred=None):
   # sets some attributes of the delegated operator to aid introspection and debugging, 
   # and then assigns the operator to the appropriate attribute of the delegator.
   if hasattr(delegator, name):
      functools.update_wrapper(the_method, getattr(delegator, name))
   else:
      the_method.__name__ = name
      the_method.__qualname = delegator.__qualname__+"."+name
      if hasattr(delegator, "__module__"): 
         the_method.__module__ = getattr(delegator, "__module__")
      the_method.__doc__ = getattr(object, name, "")
   if setter and deferred:
      try:
         setter(delegator, the_method)
      except:
         deferred[name] = fcn
   if setter:
      setter(delegator, the_method)
   elif deferred:
      deferred[name] = fcn
   else:
      raise ValueError("No setter or deferred list supplied!")

def delegate_unop(delegator, delegate_name, op_name, *, setter=None, deferred=None):
   def unop(self):
      my_delegate = object.__getattribute__(self, delegate_name)
      my_op = my_delegate.__getattribute__(op_name)
      return my_op()
   _tidy_up_and_assign(delegator, op_name, unop, setter=setter, deferred=deferred)

def delegate_binop(
   delegator, delegate_name, op_name, *, setter=None, deferred=None, type_check=True):
   if type_check:
      def binop(self, other):
         if isinstance(other, delegator):
            other = object.__getattribute__(other, delegate_name)
         my_delegate = object.__getattribute__(self, delegate_name)
         my_op = my_delegate.__getattribute__(op_name)
         return my_op(other)
   else:
      def binop(self, other):
         my_delegate = object.__getattribute__(self, delegate_name)
         my_op = my_delegate.__getattribute__(op_name)
         return my_op(other)
   _tidy_up_and_assign(delegator, op_name, binop, setter=setter, deferred=deferred)

def delegate_inplace_binop(
   delegator, delegate_name, op_name, *, setter=None, deferred=None, type_check=True):
   if type_check:
      def ibinop(self, other):
         if isinstance(other, delegator):
            other = object.__getattribute__(other, delegate_name)
         my_delegate = object.__getattribute__(self, delegate_name)
         my_op = my_delegate.__getattribute__(op_name)
         my_op(other)
         return self
   else:
      def ibinop(self, other):
         my_delegate = object.__getattribute__(self, delegate_name)
         my_op = my_delegate.__getattribute__(op_name)
         my_op(other)
         return self
   _tidy_up_and_assign(delegator, op_name, ibinop, setter=setter, deferred=deferred)


def _set__cmp__(cls, fcn): cls.__cmp__ = fcn
def _set__lt__(cls, fcn): cls.__lt__ = fcn
def _set__le__(cls, fcn): cls.__le__ = fcn
def _set__eq__(cls, fcn): cls.__eq__ = fcn
def _set__ne__(cls, fcn): cls.__ne__ = fcn
def _set__gt__(cls, fcn): cls.__gt__ = fcn
def _set__ge__(cls, fcn): cls.__ge__ = fcn


def _set__add__(cls, fcn): cls.__add__ = fcn
def _set__and__(cls, fcn): cls.__and__ = fcn
def _set__divmod__(cls, fcn): cls.__divmod__ = fcn
def _set__floordiv__(cls, fcn): cls.__floordiv__ = fcn
def _set__lshift__(cls, fcn): cls.__lshift__ = fcn
def _set__mod__(cls, fcn): cls.__mod__ = fcn
def _set__mul__(cls, fcn): cls.__mul__ = fcn
def _set__or__(cls, fcn): cls.__or__ = fcn
def _set__pow__(cls, fcn): cls.__pow__ = fcn
def _set__radd__(cls, fcn): cls.__radd__ = fcn
def _set__rand__(cls, fcn): cls.__rand__ = fcn
def _set__rdivmod__(cls, fcn): cls.__rdivmod__ = fcn
def _set__rfloordiv__(cls, fcn): cls.__rfloordiv__ = fcn
def _set__rlshift__(cls, fcn): cls.__rlshift__ = fcn
def _set__rmod__(cls, fcn): cls.__rmod__ = fcn
def _set__rmul__(cls, fcn): cls.__rmul__ = fcn
def _set__ror__(cls, fcn): cls.__ror__ = fcn
def _set__rpow__(cls, fcn): cls.__rpow__ = fcn
def _set__rrshift__(cls, fcn): cls.__rrshift__ = fcn
def _set__rshift__(cls, fcn): cls.__rshift__ = fcn
def _set__rsub__(cls, fcn): cls.__rsub__ = fcn
def _set__rtruediv__(cls, fcn): cls.__rtruediv__ = fcn
def _set__rxor__(cls, fcn): cls.__rxor__ = fcn
def _set__sub__(cls, fcn): cls.__sub__ = fcn
def _set__truediv__(cls, fcn): cls.__truediv__ = fcn
def _set__xor__(cls, fcn): cls.__xor__ = fcn


def _set__iadd__(cls, fcn): cls.__iadd__ = fcn
def _set__iand__(cls, fcn): cls.__iand__ = fcn
def _set__iconcat__(cls, fcn): cls.__iconcat__ = fcn
def _set__ifloordiv__(cls, fcn): cls.__ifloordiv__ = fcn
def _set__ilshift__(cls, fcn): cls.__ilshift__ = fcn
def _set__imod__(cls, fcn): cls.__imod__ = fcn
def _set__imul__(cls, fcn): cls.__imul__ = fcn
def _set__ior__(cls, fcn): cls.__ior__ = fcn
def _set__ipow__(cls, fcn): cls.__ipow__ = fcn
def _set__irshift__(cls, fcn): cls.__irshift__ = fcn
def _set__isub__(cls, fcn): cls.__isub__ = fcn
def _set__itruediv__(cls, fcn): cls.__itruediv__ = fcn
def _set__ixor__(cls, fcn): cls.__ixor__ = fcn


def _set__pos__(cls, fcn): cls.__pos__ = fcn
def _set__neg__(cls, fcn): cls.__neg__ = fcn
def _set__abs__(cls, fcn): cls.__abs__ = fcn
def _set__invert__(cls, fcn): cls.__invert__ = fcn
def _set__round__(cls, fcn): cls.__round__ = fcn
def _set__floor__(cls, fcn): cls.__floor__ = fcn
def _set__ceil__(cls, fcn): cls.__ceil__ = fcn
def _set__trunc__(cls, fcn): cls.__trunc__ = fcn


def _set__getitem__(cls, fcn):  cls.__getitem__ = fcn
def _set__setitem__(cls, fcn):  cls.__setitem__ = fcn
def _set__delitem__(cls, fcn):  cls.__delitem__ = fcn
def _set__contains__(cls, fcn): cls.__contains__ = fcn
def _set__iter__(cls, fcn):     cls.__iter__ = fcn
def _set__len__(cls, fcn):      cls.__len__ = fcn
def _set__missing__(cls, fcn):  cls.__missing__ = fcn
def _set__reversed__(cls, fcn): cls.__reversed__ = fcn


def _set__call__(cls, fcn):  cls.__call__ = fcn
def _set__enter__(cls, fcn): cls.__enter__ = fcn
def _set__exit__(cls, fcn):  cls.__exit__ = fcn


def _set__getattr__(cls, fcn): cls.__getattr__ = fcn
def _set__setattr__(cls, fcn): cls.__setattr__ = fcn
def _set__delattr__(cls, fcn): cls.__delattr__ = fcn
def _set__getattribute__(cls, fcn): cls.__getattribute__ = fcn


def _set__repr__(cls, fcn): cls.__repr__ = fcn
def _set__str__(cls, fcn): cls.__str__ = fcn


def _set__hash__(cls, fcn): cls.__hash__ = fcn
def _set__sizeof__(cls, fcn): cls.__sizeof__ = fcn



COMPARISONS = DictAsSet({  # all except __cmp__, which, if available, overrides the others.
    "__lt__": _set__lt__, "__le__": _set__le__, "__eq__": _set__eq__, "__ne__": _set__ne__,
    "__gt__": _set__gt__, "__ge__": _set__ge__
})

MATH_BINOPS = DictAsSet({
   "__add__": _set__add__, "__and__": _set__and__, "__divmod__": _set__divmod__, 
   "__floordiv__": _set__floordiv__, "__lshift__": _set__lshift__, 
   "__mod__": _set__mod__, "__mul__": _set__mul__, "__or__": _set__or__,
   "__pow__": _set__pow__, "__radd__": _set__radd__, "__rand__": _set__rand__,
   "__rdivmod__": _set__rdivmod__, "__rfloordiv__": _set__rfloordiv__,
   "__rlshift__": _set__rlshift__, "__rmod__": _set__rmod__, "__rmul__": _set__rmul__,
   "__ror__": _set__ror__, "__rpow__": _set__rpow__, "__rrshift__": _set__rrshift__,
   "__rshift__": _set__rshift__, "__rsub__": _set__rsub__, 
   "__rtruediv__": _set__rtruediv__, "__rxor__": _set__rxor__,
   "__sub__": _set__sub__, "__truediv__": _set__truediv__, "__xor__": _set__xor__ 
   })
MATH_IBINOPS = DictAsSet({
   "__iadd__": _set__iadd__, "__iand__": _set__iand__, "__iconcat__": _set__iconcat__,
   "__ifloordiv__": _set__ifloordiv__, "__ilshift__": _set__ilshift__,
   "__imod__": _set__imod__, "__imul__": _set__imul__,  "__ior__": _set__ior__,
   "__ipow__": _set__ipow__, "__irshift__": _set__irshift__, "__isub__": _set__isub__,
   "__itruediv__": _set__itruediv__, "__ixor__": _set__ixor__, 
})
MATH_UNOPS = DictAsSet({
   "__pos__": _set__pos__, "__neg__": _set__neg__, "__abs__": _set__abs__,
   "__invert__": _set__invert__, "__round__": _set__round__, "__floor__": _set__floor__,
   "__ceil__": _set__ceil__, "__trunc__": _set__trunc__,
})
MATH_OPS = MATH_BINOPS + MATH_IBINOPS + MATH_UNOPS

INDEXING_OPS = DictAsSet({
   "__getitem__": _set__getitem__, 
   "__setitem__": _set__setitem__, 
   "__delitem__": _set__delitem__, 
   "__contains__": _set__contains__, 
   "__iter__": _set__iter__,
   "__len__": _set__len__, 
   "__missing__": _set__missing__, 
   "__reversed__": _set__reversed__
})

NAMED_OPS = COMPARISONS + MATH_OPS + INDEXING_OPS


def delegate_cmps(delegator, delegate_name, include=COMPARISONS):
   for opname in include:
      delegate_binop(delegator, delegate_name, opname, setter=COMPARISONS[opname], type_check=True)

def delegate_math(delegator, delegate_name, include=MATH_OPS):
   for opname in include:
      setter = MATH_OPS[opname]
      if opname in MATH_BINOPS:
         delegate_binop(delegator, delegate_name, opname, setter=setter, type_check=True)
      elif opname in MATH_IBINOPS:
         delegate_inplace_binop(delegator, delegate_name, opname, setter=setter, type_check=True)
      elif opname in MATH_UNOPS:
         delegate_unop(delegator, delegate_name, opname, setter=setter)
      else:
         raise ValueError("'{}' is not a known numeric method name".format(setter))



def delegate_indexing(delegator, delegate_name, *, excluded=set()):
   if "__setitem__" in excluded:
      def setter(self, key, value):
         raise su.IllegalOpError(
            "{0}[{1}] is readonly; cannot set entry for key {1}".format(delegator.__name__, su.quote_if_str(key))
         )
   else:
      def setter(self, key, value):
         my_delegate = object.__getattribute__(self, delegate_name)
         return my_delegate.__setitem__(key, value)
   if "__delitem__" in excluded:
      def deleter(self, key):
         raise su.IllegalOpError(
            "{}[{}] is readonly and may not be removed".format(delegator.__name__, su.quote_if_str(key))
         )
   else:
      def deleter(self, key):
         my_delegate = object.__getattribute__(self, delegate_name)
         return my_delegate.__delitem__(key)
   _tidy_up_and_assign(delegator, "__setitem__", setter, _set__setitem__)
   _tidy_up_and_assign(delegator, "__delitem__", deleter, _set__delitem__)
   excluded = excluded.union(set(("__setitem__", "__delitem__")))
   for name, setter in INDEXING_OPS.items():
      if name not in excluded:
         if name is "__iter__" or name is "__len__":
            delegate_unop(delegator, delegate_name, name, setter=setter)
         else:
            delegate_binop(delegator, delegate_name, name, setter=setter, type_check=False)


def _prepare_a_field(delegator, delegate_name, deferred, field_name, readonly=False):
   if not readonly:
      class Field:
         def __get__(self, obj, type=None):
            dlgtobj = object.__getattribute__(obj, delegate_name)
            return dlgtobj.__getattribute__(field_name)

         def __set__(self, obj, value):
            dlgtobj = object.__getattribute__(obj, delegate_name)
            return dlgtobj.__setattr__(field_name)

         def __delete__(self, obj):
            dlgtobj = object.__getattribute__(obj, delegate_name)
            return dlgtobj.__delattr__(field_name)
   else:
      class Field:
         def _raise_error(field_name):
            class_name = su.a_classname(delegator)
            raise su.IllegalOpError(
               "'{}' is a read-only attribute of {}".format(field_name, class_name))
         def __get__(self, obj, type=None):
            dlgtobj = object.__getattribute__(obj, delegate_name)
            return dlgtobj.__getattribute__(field_name)

         def __set__(self, obj, value):
            _raise_error(field_name)

         def __delete__(self, obj):
            _raise_error(field_name)
   cls = new_class("_{}_{}_delegator".format(delegator.__name__,field_name), (Field,))
   deferred[field_name] = cls()
   return deferred

def delegate_fields(delegator, delegate_name, *, rw_names=(), ro_names=()):
   deferred = {}
   for name in rw_names:
      _prepare_a_field(delegator, delegate_name, deferred, name, readonly=False)
   for name in ro_names:
      _prepare_a_field(delegator, delegate_name, deferred, name, readonly=True)
   if len(deferred) is 0:
      return delegator
   else:
      def populate(ns):
         for name in deferred:
            ns[name] = deferred[name]
      newcls = new_class(delegator.__name__, (delegator,), exec_body=populate)
      return newcls



def delegate_ops_from_source(delegator, delegate_name, source, excluded=set()):
   if not isinstance(excluded, set): 
      excluded = set(excluded)
   included = set()
   for name in NAMED_OPS:
      if hasattr(source, name) and name not in excluded:
         included.add(name)
   return delegate_ops(delegator, delegate_name, included=included, excluded=excluded)

def delegate_ops(delegator, delegate_name, *, included=set(), excluded=set()):
   if not isinstance(excluded, set): 
      excluded = set(excluded)
   comparisons = set()
   mathops = set()
   indexing = set()
   for name in included:
      if name not in excluded:
         if name in COMPARISONS: comparisons.add(name)
         elif name in MATH_OPS: mathops.add(name)
         elif name in INDEXING_OPS: indexing.add(name)
   if len(comparisons) > 0:
      delegate_cmps(delegator, delegate_name, include=comparisons)
   if len(mathops) > 0:
      delegate_math(delegator, delegate_name, include=mathops)
   if len(indexing) > 0:
      delegate_indexing(delegator, delegate_name, excluded=excluded)
   return comparisons.union(mathops.union(indexing))

def delegate_from_source(delegator, delegate_name, source, included= set(), readonly=set(), excluded=None):
   if not isinstance(included, set): included = set(included)
   if excluded is None:
      excluded = set(su.owndir(delegator))
   elif not isinstance(excluded, set): excluded = set(excluded)
   done = delegate_ops_from_source(delegator, delegate_name, source, excluded=excluded)
   excluded.update(done)
   remaining = included.union(set(su.pubdir(source))) - excluded
   return delegate_fields(delegator, delegate_name, rw_names=remaining-readonly, ro_names=readonly)

def delegate(delegator, delegate_name, *, readonly=set(), included=set(), excluded=set()):
   if not isinstance(readonly, set): readonly = set(readonly)
   if not isinstance(included, set): included = set(included)
   excluded = set(excluded)
   excluded.update(delegate_ops(delegator, delegate_name, included=included, excluded=excluded))
   readwrite = (included - excluded) - readonly
   if len(readwrite)+len(readonly) > 0:
      return delegate_fields(delegator, delegate_name, rw_names=readwrite, ro_names=readonly)
   else:
      return delegator


def _set__getattribute__(cls, fcn): cls.__getattribute__ = fcn
def _set__setattr__(cls, fcn): cls.__setattr__ = fcn
def _set__delattr__(cls, fcn): cls.__delattr__ = fcn


def _onerror(msg, value=None):
   raise su.IllegalOpError(msg)

def protect_the_delegate(delegator, delegate_name, *, 
   readable=False, writable=False, removeable=False, onerror=_onerror):
   if not readable:
      ur_get = object.__getattribute__(delegator, "__getattribute__")
      @functools.wraps(ur_get)
      def getter(self, key):
         if delegate_name != key:
            return object.__getattribute__(self, key) 
         else:
            onerror("get '{}' failed: the attribute is private".format(key))
      _tidy_up_and_assign(delegator, "__getattribute__", getter, _set__getattribute__)
   if not writable:
      ur_set = object.__getattribute__(delegator, "__setattr__")  
      @functools.wraps(ur_set)
      def setter(self, key, value):
         if delegate_name != key:
            object.__setattr__(self, key, value)
         else:
            onerror("set '{}' failed: the attribute is private".format(key,value), value)
      _tidy_up_and_assign(delegator, "__setattr__", setter, _set__setattr__)
   if not removeable:
      ur_del = object.__getattribute__(delegator, "__delattr__")  
      @functools.wraps(ur_del)
      def deleter(self, key):
         if delegate_name != key:
            object.__delattr__(self, key)
         else:
            onerror("del '{}' failed: the attribute is private".format(key))
      _tidy_up_and_assign(delegator, "__delattr__", deleter, _set__delattr__)



class Static_Delegator:
   def __init__(self, delegate_name="", *, source=None, included=set(), excluded=set(), readonly=set()):
      self.delegate_name = delegate_name
      self.included = set(included)
      self.readonly = set(readonly)
      self.excluded = set(excluded)
      self.source = source

   def apply(self, delegator, delegate_name=None):
      if not delegate_name:
         if self.delegate_name:
            delegate_name = self.delegate_name
         else:
            raise ValueError("No value was supplied for the delegate attribute's name.")
      if self.source:
         return delegate_from_source(delegator, delegate_name,
            self.source, included=self.included, readonly=self.readonly, excluded=self.excluded)
      else:
         return delegate(delegator, delegate_name,
            included=self.included, readonly=self.readonly, excluded=self.excluded)

   def __call__(self, delegator):
      return self.apply(delegator)

class Indexing_Delegator(Static_Delegator):
   def __init__(self, delegate_name="", *, excluded=set()):
      Static_Delegator.__init__(self, delegate_name, included=INDEXING_OPS, excluded=excluded)

class List_Delegator(Static_Delegator):
   def __init__(self, delegate_name="", *, excluded=set()):
      Static_Delegator.__init__(self, delegate_name, source=list, excluded=excluded)

class Tuple_Delegator(Static_Delegator):
   def __init__(self, delegate_name="", *, excluded=set(("__setitem__", "__delitem__"))):
      Static_Delegator.__init__(self, delegate_name, source=tuple, excluded=excluded)

class Dict_Delegator(Static_Delegator):
   def __init__(self, delegate_name="", *, excluded=set()):
      Static_Delegator.__init__(self, delegate_name, source=dict, excluded=excluded)

class RO_Dict_Delegator(Static_Delegator):
   def __init__(self, delegate_name="", *, excluded=set(
         ("__delitem__", "__setitem__", "clear", "copy", "pop", "popitem", "setdefault", "update")
      )):
      Static_Delegator.__init__(self, delegate_name, source=dict, excluded=excluded)

class Delegate_Protector:
   def __init__(self, delegate_name="", *,
         readable=False, writable=False, removeable=False, onerror=None):
      self.delegate_name = delegate_name
      self.readable = readable
      self.writable = writable and readable
      self.removeable = removeable
      self.onerror = onerror if onerror is not None else _onerror
   
   def apply(self, delegator, delegate_name=None):
      if not delegate_name:
         if self.delegate_name:
            delegate_name = self.delegate_name
         else:
            raise ValueError("No value was supplied for the delegate attribute's name.")
      protect_the_delegate(delegator, delegate_name, 
         readable = self.readable, writable = self.writable, 
         removeable = self.removeable, onerror = self.onerror)
      return delegator

   def __call__(self, delegator):
      return self.apply(delegator)


class RO_Delegate_Protector(Delegate_Protector):
   def __init__(self, delegate_name="", *, onerror=None):
      Delegate_Protector.__init__(self, delegate_name,
         readable=True, writable=False, removeable=False, onerror=onerror)



def delegate__attr__from_source(delegator, delegate_name, source, *,
   protect=True, runtime=set(), included=set(), readonly=set(), excluded=set()):
   excluded = set(excluded)
   original = set(dir(delegator))
   delegator = delegate_from_source(delegator,delegate_name,
      source=source, included=included, excluded=runtime.union(excluded), readonly=readonly)
   added = set(dir(delegator)) - original
   excluded = excluded.union(added)
   for name in added:
      if name in included:
         included.remove(name)
   return _delegate__attr__common(delegator, delegate_name,
      protect=protect, included=included, excluded=excluded, readonly=readonly)

def delegate__attr__(delegator, delegate_name, *, 
   protect=True, runtime=set(), included=set(), readonly=set(), excluded=set()):
   excluded = set(excluded)
   original = set(dir(delegator))
   delegator = delegate(delegator,delegate_name,
      included=included, excluded=runtime.union(excluded), readonly=readonly)
   added = set(dir(delegator)) - original
   excluded = excluded.union(added)
   for name in added:
      if name in included:
         included.remove(name)
   return _delegate__attr__common(delegator, delegate_name,
      protect=protect, included=included, excluded=excluded, readonly=readonly)

def _choose_protector(protect):
   if protect is True: 
      # n.b. really, really True, not Trueish. 
      def nosuch(msg, value=None): 
         raise su.IllegalOpError(msg)            
   elif type(protect)==type(Exception) and issubclass(protect, Exception): 
      # you may wish to some work before surrendering to the "raise"
      def nosuch(msg, value=None):
         raise protect(msg) 
   elif protect:
      # you are on your own here
      def nosuch(msg, value=None):
         return protect(msg, value)
   else:
      nosuch = False
   return nosuch

def _delegate__attr__common(delegator, delegate_name, *, protect=True, included=set(), readonly=set(), excluded=set()):
   if not isinstance(included, set):
      included = set(included)
   nosuch = _choose_protector(protect)
   ur_get = object.__getattribute__(delegator, "__getattribute__")
   @functools.wraps(ur_get )
   def getter(self, key):
      if key in included: 
         # only look in the delegate, not in the delegator
         return object.__getattribute__(self, delegate_name).__getattribute__(key)
      elif delegate_name == key and nosuch is not False:
         msg = "get '{}' failed: attribute is private".format(key)
         return nosuch(msg)
      elif key in excluded:
         # the key is excluded and excluded keys are NEVER delegated! 
         return object.__getattribute__(self, key)
      else:
         # try delegator first, but if that fails, try the delegate 
         try:
            return object.__getattribute__(self, key) 
         except:
            return object.__getattribute__(self, delegate_name).__getattribute__(key) 
   ur_set = object.__getattribute__(delegator, "__setattr__")  
   @functools.wraps(ur_set)
   def setter(self, key, value):
      if key in included and key not in readonly:
         object.__getattribute__(self, delegate_name).__setattr__(key, value)
      elif delegate_name == key and nosuch is not False:
         msg = "set '{}' failed: attribute is private".format(key)
         nosuch(msg,value)
      elif key not in excluded:
         try:
            object.__setattr__(self, key, value)
         except:
            object.__getattribute__(self, delegate_name).__setattr__(key, value)
      else:
         return object.__setattr__(self, key, value)

   ur_del = object.__getattribute__(delegator, "__delattr__")  
   @functools.wraps(ur_del)
   def deleter(self, key):
      if key in included:
         object.__getattribute__(self, delegate_name).__delattr__(key)
      elif delegate_name == key and nosuch is not False:
         msg = "del '{}' failed: attribute is private".format(key)
         nosuch(msg)
      elif key not in excluded:
         try:
            object.__delattr__(self, key)
         except:
            object.__getattribute__(self, delegate_name).__delattr__(key)
      else:
         object.__delattr__(self, key)
   _tidy_up_and_assign(delegator, "__getattribute__", getter, _set__getattribute__)
   _tidy_up_and_assign(delegator, "__setattr__", setter, _set__setattr__)
   _tidy_up_and_assign(delegator, "__delattr__", deleter, _set__delattr__)
   return delegator

def basic_delegate_attr(delegator, delegate_name, *, protect=True):
   nosuch = _choose_protector(protect)
   ur_get = object.__getattribute__(delegator, "__getattribute__")
   ur_set = object.__getattribute__(delegator, "__setattr__")  
   ur_del = object.__getattribute__(delegator, "__delattr__")  
   if nosuch:
      @functools.wraps(ur_get )
      def getter(self, key):
         if delegate_name == key:
            msg = "get '{}' failed: attribute is private".format(key)
            return nosuch(msg)
         else:
            try:
               return object.__getattribute__(self, key) 
            except:
               return object.__getattribute__(self, delegate_name).__getattribute__(key)
      @functools.wraps(ur_set)
      def setter(self, key, value):
         if delegate_name == key:
            msg = "set '{}' failed: attribute is private".format(key)
            nosuch(msg, value)
         else:
            try:
               object.__setattr__(self, key, value)
            except:
               object.__getattribute__(self, delegate_name).__setattr__(key, value)
      @functools.wraps(ur_del)
      def deleter(self, key):
         if delegate_name == key and nosuch is not False:
            msg = "del '{}' failed: attribute is private".format(key)
            nosuch(msg)
         else:
            try:
               object.__delattr__(self, key)
            except:
               object.__getattribute__(self, delegate_name).__delattr__(key)
   else: 
      @functools.wraps(ur_get )
      def getter(self, key):
         try:
            return object.__getattribute__(self, key) 
         except:
            return object.__getattribute__(self, delegate_name).__getattribute__(key) 
      @functools.wraps(ur_set)
      def setter(self, key, value):
         try:
            object.__setattr__(self, key, value)
         except:
            object.__getattribute__(self, delegate_name).__setattr__(key, value)
      @functools.wraps(ur_del)
      def deleter(self, key):
         try:
            object.__delattr__(self, key)
         except:
            object.__getattribute__(self, delegate_name).__delattr__(key)
   _tidy_up_and_assign(delegator, "__getattribute__", getter, _set__getattribute__)
   _tidy_up_and_assign(delegator, "__setattr__", setter, _set__setattr__)
   _tidy_up_and_assign(delegator, "__delattr__", deleter, _set__delattr__)
   return delegator



class Dynamic_Delegator():
   def __init__(self, delegate_name="", *, protect=True, included=set(), readonly= set(), excluded=set()):
      self.delegate_name = delegate_name
      self.included = set(included)
      self.readonly = set(readonly)
      self.excluded = set(excluded)
      self.protect = protect

   def apply(self, delegator, delegate_name=None):
      if not delegate_name:
         if self.delegate_name:
            delegate_name = self.delegate_name
         else:
            raise ValueError("No value was supplied for the delegate attribute's name.")
      return delegate__attr__(delegator, delegate_name, 
         protect=self.protect, included=self.included, readonly=self.readonly, excluded=self.excluded
      )

   def __call__(self, delegator):
      return self.apply(delegator)
