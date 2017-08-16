

from argparse import ArgumentParser
from argparse import HelpFormatter
from collections import defaultdict, namedtuple
from frozendict import FrozenDict
import re
import sys
import sysutils as su
import types


def parse_args(*classes, args=None, usage=None, harden=True):
   clp = CmdLineParser() if usage == None else CmdLineParser(usage=usage)
   for aClass in classes:
      clp.setCaller(aClass)
      aClass.setCmdLineArgs(clp)
   return clp.parse_all_args(args=args, harden=harden)



def args_dict(parsed_args, freeze=False):
  if hasattr(parsed_args, "__dict__"):
    return parsed_args.__dict__.copy() if not freeze else FrozenDict(parsed_args.__dict__)
  elif hasattr(parsed_args, "_asdict"):
    asdict = parsed_args._asdict()
    return asdict if not freeze else FrozenDict(asdict)
  else:
    raise TypeError(
      "Unexpected return type, {}, from the argument parser".format(type(parsed_args))
    )

class CmdLineParser(ArgumentParser):

   def __init__(self, 
                 prog=None,             usage=None,
                 description=None,      epilog=None,
                 parents=[],            formatter_class=HelpFormatter,
                 prefix_chars='-',      fromfile_prefix_chars=None,
                 argument_default=None, conflict_handler='error',
                 add_help=True,         caller=None):
      self.synonyms = defaultdict(list)  # maps each key to its synonyms
      self.misfits = set()               # keys that are not valid Python ids
      self.setCaller(caller)
      ArgumentParser.__init__(self,
                 prog=prog, usage=usage, description=description,
                 epilog=epilog, parents=parents, formatter_class=formatter_class,
                 prefix_chars=prefix_chars, fromfile_prefix_chars=fromfile_prefix_chars,
                 argument_default=argument_default, conflict_handler=conflict_handler,
                 add_help=add_help)

   def setCaller(self, caller):
      if caller is None:
         self.caller = None
      elif isinstance(caller, str):
         self.caller = caller
      else:
         theClass = caller if isinstance(caller, type) else caller.__class__
         self.caller = theClass.__name__


   def _addSynonyms(self, namespace, strict=True, harden=False):
      kvpairs = vars(namespace)
      updates = {}
      errors = []
      for key, value in kvpairs.items():
         if key in self.synonyms:
            try:
               for other in self.synonyms[key]:
                  updates[other] = value
            except Exception as e:
               errors.add(str(e))
      if len(errors) > 0:
         if strict:
            raise ValueError("Parse failed:\n\t{}".format(errors))
         else:
            for msg in errors:
               print(msg, file=sys.stderr)
      for key in updates:
         value = updates[key]
         namespace.__dict__.update(((key, value),))
      return su.harden(namespace) if harden else namespace

   def parse_all_args(self, args=None, strict=True, harden=False):
      namespace = types.SimpleNamespace()
      self.parse_args(args, namespace)
      return self._addSynonyms(namespace, strict, harden)
      
   def parse_only_known_args(self, args=None, strict=True, harden=False):
      namespace = types.SimpleNamespace()
      namespace, the_rest = self.parse_known_args(args, namespace)
      return (self._addSynonyms(namespace, strict, harden), the_rest)

   
   def add_argument(self, *args, **kwargs):
      for n in range(0, len(args)):
         argN = args[n]
         mall = re.fullmatch("(-*)(.+)", argN)
         #print(mall.groups())
         if not mall.group(2):
            continue 
         leader = mall.group(1)
         keyN = mall.group(2)
         mkey = re.fullmatch("\w+", keyN)
         if not mkey:
            clean = keyN.replace('-', '_')
            self.synonyms[clean].append(keyN)
            self.synonyms[keyN].append(clean)
            keyN = clean # make sure we have what argparse might use as a key
            self.misfits.add(keyN)
         for m in range(0, len(args)):
            if n != m:
               mall = re.fullmatch("(-+)(.+)", args[m])
               keyM = mall.group(2)
               #print("{} {} <--> {} {}".format(n, keyN, m, keyM))
               self.synonyms[keyN].append(keyM)
      return ArgumentParser.add_argument(self, *args, **kwargs)

   def _print_add_error(self, key, message):
      tail = " option '{}': {}".format(key, message)
      if self.caller:
         tail = " caller '{}', {}".format(self.caller, tail)
      print("Error:"+tail, file=sys.stderr)

   def add_pair(self, *keys,           # the short and optional long form for the key 
                     const=None,       # value to use if the key appears without a value
                     default=None,     # value to use if the key does NOT appear at all
                     type=str,         # a valid Python type, typically str or int
                     choices=None,     # if a collection, the only valid values for the key
                     required=False,   # normally a key need not appear
                     action='store',   # normal action: just save the value
                     help='(no help)', # help message
                     metavar=None      # documentation only
                     ):
      try:
         if len(keys) == 1:
            if keys[0][0] == '-':
               self.add_argument(keys[0],
                  const=const, default=default, type=type,  choices=choices,
                  required=required, help=help, metavar=metavar)
            else:
               self.add_argument(keys[0],
                  const=const, default=default, type=type,  choices=choices,
                  help=help, metavar=metavar)
         else:
            self.add_argument(keys[0], keys[1],
               const=const, default=default, type=type,  choices=choices,
               required=required, help=help, metavar=metavar)
            self.synonyms[keys[1]] = keys[0]
      except Exception as e: 
         self._print_add_error(keys[0], str(e))

   def add_repeatable(self, *keys,     # the short and optional long form for the key 
                     const=None,       # value to use if the key appears without a value
                     default=None,     # value to use if the key does NOT appear at all
                     type=str,         # a valid Python type, typically str or int
                     choices=None,     # if a collection, the only valid values for the key
                     required=False,   # normally a key need not appear
                     help='(no help)', # help message
                     metavar=None      # documentation only)
                     ):
      if keys[0][0] != '-':
         raise ValueError("Positional argument '{}' cannot be repeatable".format(keys[0]))
      self.add_pair(*keys, source=source, const=const, default=default,
                    type=type, choices=choices, required=required, action="append",
                    help=help, metavar=metavar)

   def add_flag(self, *keys,            # the short and optional long form for the key 
                     help='(no help)'): # help message
      try:
         if  len(keys) == 1: 
            self.add_argument(keys[0], action='store_true', help=help)
         else: 
            self.add_argument(keys[0], keys[1], action='store_true', help=help)
            self.synonyms[keys[1]] = keys[0]
      except Exception as e:
         self._print_add_error(keys[0], str(e))

   def add_positional(self, key,      # the key for accessing the value
                     type=str,        # a valid Python type, typically str or a numeric type
                     nargs=1,         # normally 1, can be a number, '?', '+', or  '*' 
                     choices=None,    # if a collection, the only valid values for the key
                     help='(no help)' # help message
                     ):
      try:
         self.add_argument(key, type=type, choices=choices, help=help, nargs=nargs)
      except Exception as e:
         self._print_add_error(key, str(e))

   def add_a_flag(self, key, help_msg):
      self.add_flag(key, help=help_msg)

   def add_an_int(self, key, default_value, help_msg):
      self.add_pair(key, default=default_value, help=help_msg, type=int)

   def add_a_float(self, key, default_value, help_msg):
      self.add_pair(key, default=default_value, help=help_msg, type=float)

   def add_a_str(self, key, default_value, help_msg):
      self.add_pair(key, default=default_value, help=help_msg, type=str)

   def add_a_list(self, key, help, type=str): 
      self.add_positional(key, help=help, nargs='+', type=type)

   def add_an_optional_list(self, key, help, type=str):
      self.add_positional(key, help=help, nargs='*', type=type)
   
