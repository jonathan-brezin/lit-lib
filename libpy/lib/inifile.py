
from collections import namedtuple, defaultdict
import idbg
import math
from fileutils import expandPathList, fopen
import os
import re
import sys
import sysutils as su


class SectionDict(dict):
   LIST_SEPARATOR = re.compile(",\s*")
   def __init__(self, mapping = {}):
      dict.__init__(self)
      for key in mapping: self[key.lower()] = mapping[key]
   def __setitem__(self, key, value):
      dict.__setitem__(self, key.lower(), str(value))
   def get(self, key, default = None):
      if key in self:
         return self[key]
      else:
         return default
   def getint(self, key, default=None):
      if key in self:
         return su.str2int(self[key])
      else:
         return default
   def getfloat(self, key, default=None):
      if key in self:
         return float(self[key])
      else:
         return default
   def getboolean(self, key, default=None):
      if key in self:
         return su.asboolean(self[key])
      else:
         return default
   def getlist(key, separator=LIST_SEPARATOR, default=[]):
      if key in self:
         return separator.split(self[key])
      else:
         return default
   def getstr(self, key, default = None):
      if key in self:
         return self[key]
      else:
         return default


class Inifile(defaultdict, idbg.DbgClient):
   comment_start = "^[#;]"
   key_end = "\s*[:=]\s*"
   no_trailing_whitespace = True
   idbg.DbgClient.start_debugging()

   def firstWins(section, key, source, target):
      # do nothing, so the target remains as it was
      pass

   def lastWins(section, key, source, target):
      # the source being merged into the target overwrites the target's value
      target[key] = source[key]

   def keepBoth(section, key, source, target, separator=", "):
      # the values are always strings, so we can just concatenate with a separator 
      target[key] += separator+source[key]

   def raiseError(section, key, source, target):
      msg = "Conflicting duplicate entries for key [{0}]{1} in {2}."
      raise ValueError(msg.format(section, key, source.path))

   @classmethod
   def readOne(self, baseName, *paths):
      if len(paths) is 0:
         (abspath, baseName) = os.path.split(os.path.abspath(baseName))
         paths = [abspath]
      for path in expandPathList(paths):
         inipath = os.path.join(path, baseName)
         self.dbg_write("ini_read", "Try {0}.".format(inipath))
         if os.path.exists(inipath):
            self.dbg_write("ini_read", "Use {0}.".format(inipath))
            return Inifile(inipath)
      raise IOError("File not found, {0} in any of {1}", baseName, paths)

   @classmethod
   def readAll(self, baseName, *paths, ondup=raiseError):
      if len(paths) is 0:
         (abspath, baseName) = os.path.split(os.path.abspath(baseName))
         paths = [abspath]
      inifiles = []
      for path in expandPathList(paths):
         inipath = os.path.join(path, baseName)
         if os.path.exists(inipath):
            self.dbg_write("ini_read", "Use {0}.".format(inipath))
            inifiles.append(Inifile(inipath))
         else:
            self.dbg_write("ini_read", "No {0}.".format(inipath))
      if len(inifiles) is 0:
         return Inifile()
      else:
         answer = inifiles[0]
         for ini in inifiles[1:]:
            answer.merge(ini, ondup)
         return answer

   @classmethod
   def readOptional(self, baseName, *paths, defaults=None):
      if defaults is None:
         defaults = Inifile()
      if len(paths) is 0:
         (abspath, baseName) = os.path.split(os.path.abspath(baseName))
         paths = [abspath]
      for path in expandPathList(paths):
         inipath = os.path.join(path, baseName)
         self.dbg_write("ini_read", "Try {0}.".format(inipath))
         if os.path.exists(inipath):
            self.dbg_write("ini_read", "Use {0}.".format(inipath))
            return Inifile(inipath)
      self.dbg_write("ini_read", "Use {0}.".format(defaults))
      return defaults

   @classmethod
   def read(self, all=[], one=[], optional=[], ondup=raiseError, defaults=None):
      if defaults is None:
         defaults = Inifile()
      final = Inifile()
      for args in all:
         final.merge(self.readAll(*args, ondup=ondup), ondup)
      for args in one:
         final.merge(self.readOne(*args), ondup)
      for args in optional:
         final.merge(self.readOptional(*args), ondup)
      final.mergeTargetWins(defaults)
      return final


   def _debug_key(self, msg, section, key, lineno):
      if self.dbg_is_active("ini_key"):
         leader = "Line {}: [{}]".format(lineno, section)
         if key:
            leader += "[{}]".format(key)
         self.debug_output("ini_key", "{} {}".format(leader, msg))

   def __init__(self, path=None, 
         cmnt_re=comment_start, keyend_re=key_end, no_tws=no_trailing_whitespace
   ):
      defaultdict.__init__(self, SectionDict) # that is: super.__init__(...)
      idbg.DbgClient.__init__(self)
      self.path = path
      if path is None:
         return
      commentRe = re.compile(cmnt_re)
      keyendRe = re.compile(keyend_re)
      # a section name is a square-bracket-free string in square brackets:
      sectionNameRe = re.compile("^\[([^[\]]*)\]$") 
      # capture leading whitespace and "the rest", except for the trailing newline:
      lws_re = re.compile("^(\s*)([^\n]*)")
      # we begin in the "anonymous" section
      sectionName = ""
       # a dict for the current section's key/data pairs
      currentDictionary = self[sectionName] 
      with open(path, 'r') as f:
         linenowidth = 3
         justify = lambda x: repr(x).rjust(linenowidth)
         lineno = 0
         line = ''
         def nextLine():
            nonlocal f, line, lineno, commentRe, no_tws, lws_re
            line = f.readline()
            if len(line) == 0:
               return (-1, None)
            lineno += 1
            self.debug_output("ini_all", "Line {0}: {1}".format(justify(lineno), line))
            if commentRe.match(line):
               return nextLine()
            (whitespace, rest) = lws_re.match(line).groups()
            if rest == '':  # it is a blank line
               return nextLine()
            if no_tws:
               rest = rest.rstrip() # the initial match left trailing spaces and tabs on the right
            return((len(whitespace) > 0), rest)
         (indented, rest) = nextLine()
         while rest is not None:
            # this is either a section name line or the start of a key/data pair: no indent!
            if indented: 
               raise SyntaxError("Line {0} should not be indented!".format(lineno)) 
            if rest[0] == '[': # the line names a section and must end with  a ']'
               if rest[-1] != "]": 
                  msg = "Line {0}: missing ']' in section start, \"{1}\""
                  raise SyntaxError(msg.format(justify(lineno), rest))
               match = sectionNameRe.match(rest)
               if match is None:
                  msg = "Line {0}: illegal character, '[' or ']', in the section name '{1}'"
                  raise SyntaxError(msg.format(justify(lineno), rest[1 : -1]))
               sectionName = rest[1 : -1]
               self._debug_key("change section.", sectionName, None, lineno)
               currentDictionary = self[sectionName]
               (indented, rest) = nextLine()
            else: # the line begins a key/data pair 
               match = keyendRe.search(rest)
               if match is None:
                  raise SyntaxError("line {0}: missing key terminator".format(lineno))
               key  = rest[0:match.start()] 
               data = rest[match.end():] 
               key_start = lineno
               (indented, rest) = nextLine()
               while indented and rest is not None:
                  data += "\n" + rest # 'rest' has no leading whitespace!            
                  (indented, rest) = nextLine()
               if len(data) is 0:
                  msg = "line {0}: no data after the key terminator"
                  raise SyntaxError(msg.format(lineno))
               if key in currentDictionary:
                  oldValue = currentDictionary[key]
                  # both data and oldValue are strings.  If they are unequal as strings,
                  # they may still imply the same Boolean value: e.g. "yes" and "on", or
                  # 'no' and 'off'. I assume that if both name Booleans and have the
                  # same value as Booleans, then there is no conflict.
                  if data != oldValue and not su.sameboolean(data, oldValue):
                     msg = "line {0}: duplicate key '{1}' with differing values"
                     raise ValueError(msg.format(key_start, key))
                  else:
                     msg = "== {} dup'd".format(oldValue)
                     self._debug_key(msg, sectionName, key, key_start)
               else:
                  currentDictionary[key] = data
                  self._debug_key("== {}.".format(data), sectionName, key, key_start)


   def _get_args(self, args, default=None):
      arg0 = args[0]
      if arg0.startswith('['):
         sectionend = arg0.index(']')
         s = arg0[1:sectionend-1]
         k = arg0[sectionend+1:]
      else:
         s = arg0
         k = None
      argcount = len(args)
      if argcount is 1:
         if k is None:
            raise ValueError("No key specified in the argument, '{0}'".format(s))
      elif argcount is 2:
         if k is None:
            k = args[1]
         else:
            default = args[1]
      elif argcount > 3 or k is not None:
         raise Exception("Too many arguments: {0}".format(args))
      else: # argcount is 3 and all we need is k and default
         k = args[1]
         default = args[2]
      return (s, k, default)

   def get(self, *args):
      (s, k, default) = self._get_args(args)
      return self[s][k] if s in self and k in self[s] else default

   def getboolean(self, *args):
      return su.asboolean(self.get(*args))

   def getfloat(self, *args):
      raw = self.get(*args)
      if raw is None:
         return math.nan
      else:
         return float(raw)
    
   def getint(self, *args):
      raw = self.get(*args).lower()
      if raw is None:
         return None
      else:
         return su.str2int(raw)

   def getlist(self, *args, separator=SectionDict.LIST_SEPARATOR):
      (s, k, default) = self._get_args(args, default=[])
      return separator.split(self[s][k]) if s in self and k in self[s] else default

   def getstr(self, *args):
      return self.get(*args)
   
   def hassection(self, aString):
      return s in self

   def haskey(self, s, k=''):
      if s.startswith('['):
         (s, k) = s[1:].split(']')
      return s in self and k in self[s]

   def sectionswithkey(key):
      answer = []
      for s in self:
         if key in self[s]:
            answer.append(s)
      return answer
    
   def getsection(self, s, default = SectionDict()): 
      return dict(self[s]) if s in self else default

   def getsectionkeys(self):
      if s in self:
         asList = list(self[s].keys())
         asList.sort()
         return asList

   def getsections(self):
      asList = list(self.keys())
      asList.sort()
      return asList

   def addsection(self, name):
      if not name in self:
         self[name] = {}

   def badType(name, theType):
      msg = "Expected a string for the {0}, but was passed a {1}"
      raise TypeError(msg.format(name, su.aOrAn(str(theType))))

   def addentry(self, section="", key="", value=""):
      if type(section) is not str:
         badType("section", type(section))
      elif section not in self:
         raise ValueError("Section {0} not found.".format(section))
      elif type(key) is not str:
         badType("key", type(key))
      elif type(value) != str:
         badType("value", type(value))
      else:
         self[section][key] = value

   def merge(self, anInifile, ondup=raiseError):
      for section in anInifile:
         if section not in self:
            self[section] = anInifile.getsection(section)
         else:
            source = anInifile[section]
            target = self[section]
            for key in source:
               if key not in target: target[key] = source[key]
               elif target[key] != source[key]:
                  ondup(section, key, source, target)

   def mergeTargetWins(self, anInifile):
      self.merge(self, anInifile, firstWins) 

   def mergeSourceWins(self, anInifile): 
      self.merge(self, anInifile, lastWins)

   def mergeKeepBoth(self, anInifile, separator=','): 
      self.merge(self, anInifile, keepBoth) 

   def write_to_f_out(self, f_out, keyend=": ", indent="   "):
      section_names = list(self)
      section_names.sort()
      for name in section_names:
         if len(name) > 0:
            f_out.write("[{0}]\n".format(name))
         sectionDict = self[name]
         keys = list(sectionDict)
         keys.sort()
         line_end = "\n"+indent
         for key in keys:
            value = sectionDict[key].replace("\n",line_end)
            f_out.write("{0}{2}{1}\n".format(key, value, keyend))

   def write(self, path=None, keyend=": ", indent="   ", backups=0):
      if path is None:
         path = self.path if self.path else sys.stdout
      if type(path) is str: # it is a real path: use "with" to guaranty closure
         with fopen(path, mode="w", encoding="utf-8", where="bak", toKeep=backups) as f_out:
            self.write_to_f_out(f_out, keyend, indent)
      else: # "path" must be a stream: do NOT close it, as a "with" would
         self.write_to_f_out(path, keyend, indent)
