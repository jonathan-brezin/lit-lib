
from blist import blist
import html
import inspect
import io
import os
from singleton import OneOnly
from sys import stdout, stderr
import sysutils as su
import time
import traceback
from wildcardlookup import WildCardLookup

def getDbgMgr(*patterns):
   mgr = DbgMgr.get()
   mgr.add_patterns(*patterns)
   return mgr
        

def openDbgMgr(*patterns, **kwargs): 
   mgr = DbgMgr.get()
   mgr.add_patterns(patterns)
   if mgr.path is None:
      path = su.getitem(kwargs, "path", None)
      mgr._open(path)
      mgr.sortby = su.getitem(kwargs, "sortby", "time")
   return mgr
   

class DbgMessage:
   DEFAULTS = {
      "key": "",              # not used by errors and warnings
      "weakest_match": None,  # weakest pattern that matches the key (if key is non-empty)
      "display_priority": 3,  # the priority assigned to ordinary debugging output
      "caller": '??',         # should always be supplied by the caller
      "body": "",             # should always be supplied by the caller
      "index": -1,            # should always be supplied by the caller
      "style_class": "ordinary_msg" # ordinary, non-priority debugging output
   }
   def __init__(self, parms_in):
      parms = su.mergepairs(parms_in, self.DEFAULTS, clone=True)
      self.key = parms['key']
      self.match = parms['weakest_match'] if parms['weakest_match'] else parms['key']
      self.display_priority = parms['display_priority']
      self.caller = parms['caller']
      self.body = parms['body']
      self.index = parms['index']
      self.style_class = parms['style_class']

   def __eq__(self, other):
      self.index is other.index

   def __ne__(self, other):
      not (self.index is other.index)

   def __lt__(self, other):
      # the display priority always rules:
      if self.display_priority < other.display_priority:
         return True
      elif self.display_priority is other.display_priority:
         if self.key is None: 
            # both are either an error or a warning, so the index rules
            return self.index < other.index
         else:
             # Both must be debugging messages, since they have the same priority and
             # are not errors or warnings. They should both, therefore, have keys,
             # weakest matches, and sources.
            pivot = DbgMgr.get().sortby
            if pivot == "key":
               if self.key < other.key:
                  return True
               elif self.key == other.key:
                  if self.index < other.index:
                     return True
            elif pivot == "match":
               if self.match < other.match: 
                  return True
               elif self.match == other.match:
                  if self.index < other.index:
                     return True
            elif pivot == "source":
               if self.source < other.source:
                  return True
               elif self.source == other.source:
                  if self.index < other.index:
                     return True
      return False

   def __le__(self, other):
      return self.__lt__(other) or self.__eq__(other)

   def __gt__(self, other):
      return not (self.__lt__(other) or self.__eq__(other))

   def __ge__(self, other):
      return not self.__lt__(other)

   def __str__(self):
      from_key = "[{}]".format(self.key) if self.key else ""
      clean_caller =  html.escape(self.caller)
      about = "<span class=\"msg_source\">{0}: {1}{2}</span>".format(
         self.index, clean_caller, from_key
      )
      table = "<table class=\"{0}\"><tr><td>{1}</td></tr></table>".format(
         self.style_class, self.body
      )
      return about+table


@OneOnly
class DbgMgr:
   def __init__(self):
      self.buffer = []
      self.count = 0
      self.highpriority = WildCardLookup()
      self.keypatterns = WildCardLookup()
      self.message_styles = {
         "error_msg": """{color: #ff0000; font-weight: bold; background-color: #F0D0D0; 
                   border: 1px solid red; margin-left: 1em;}""",
         "priority_msg": """{color: #007020; font-weight: bold; background-color: #E1FDC8;
                   border: 1px solid #007020; margin-left: 1em;}""", 
         "ordinary_msg": """{color: #000000; background-color: #DDDDDD; 
                   border: 1px solid black; margin-left: 1em;}""", 
         "warning_msg": """{color: #0000ff; font-weight: bold; background-color: #C8E5F8;
                   border: 1px solid blue; margin-left: 1em;}""", 
         "flush_before_after":  "{color: #000000;}", 
         "msg_source": "{color: #000000; font-style: oblique}"
      }
      self._path = None
      self._sortby = None
      self._stream = None
      self._head = None
      self._head_started = False
      self._head_is_open = False
      self._something_written = False
      self._bail_on_warning = False

   def get_path(self):
      return self._path

   def set_path(self, logdirpath):
      if self._path is None:
         abspath = self._normalizeThePath(logdirpath)
         if not os.path.exists(abspath):
            os.makedirs(abspath)
         elif not os.path.isdir(abspath):
            msg = "'{0}' exists, but is not a directory".format(abspath)
            raise NotADirectoryError(msg)
         self._path = os.path.join(abspath, "dbg"+su.now4FileName()+".html")
      elif logdirpath is None:
         self.stream = None # flushes and closes the stream
         self._path = None
      else:
         raise RuntimeError("DbgMgr already opened '{}'".format(self._path))

   def _normalizeThePath(self, path):
      rootpath = os.getcwd()
      if path:
         if os.path.isabs(path):         
            raw = path
         elif path.startswith("./") or path.startswith("../") or path.startswith("~/"):
            raw = path # implied absolute paths: "here" and "home"                 
         else:
            raw =  os.path.join(rootpath, path)
      else:
         raw = os.path.join(rootpath, "log")
      return os.path.abspath(raw) # gets rid of pesky dots, double dots and tildes

   def del_path(self):
      raise RuntimeError("Cannot remove the path attribute")

   def get_sortby(self):
      return self._sortby

   def set_sortby(self, new_value):
      new_value = new_value.lower()
      if new_value in ["key", "match", "source", "time"]:
         self._sortby = new_value
      elif new_value is None:
         self._sortby = "time"
      else:
         raise ValueError("Unrecognized sort type: '{}'".format(new_value))

   def del_sortby(self):
      raise RuntimeError("Cannot remove the sortby attribute")

   def get_stream(self):
      return stderr if self._stream is None else self._stream

   def set_stream(self, astream):
      if self._stream is None:
         self.dbg("dbg", "initializing stream: {}".format(astream))
         self._stream = astream
      else:
         self.dbg("dbg", "resetting stream to None")
         if astream in [stdout, stderr, None]:
            if self._stream in [stdout, stderr]:
               if astream != self._stream:
                  self.flush()
                  self._stream = astream
               # else: no change: output is already going to "astream"
            else:
               # closing the current output file flushes the buffer
               self.close()
               self._stream = astream
         else:
            raise RuntimeError("Output stream is already opened")

   def del_stream(self):
      raise RuntimeError("Cannot remove the stream attribute")

   path   = property(get_path, set_path, del_path)
   sortby = property(get_sortby, set_sortby, del_sortby)
   stream = property(get_stream, set_stream, del_stream)

   def mycallersname(self): 
      return inspect.currentframe().f_back.f_back.f_code.co_name

   def prepare_patterns(self, patterns):
      as_blist = blist(patterns)
      su.flatten(as_blist)
      extras = []
      for n in range(0, len(as_blist)):
         entry_n = as_blist[n]
         if ',' in entry_n:            
            actual_entries = [s.strip() for s in entry_n.split(',')]
            as_blist[n] = actual_entries[0] # replace the comma list with its first entry
            extras += actual_entries[1:]    # do NOT change the size of as_blist
         else:
            as_blist[n] = entry_n.strip()
      as_blist += extras
      as_blist.sort()
      return as_blist

   def addstyleclass(self, name, spec):
      # I try to keep all the style classes together in the head of the document, so I buffer them
      # until the first flush.  Once they are written, I write a new <style> element for each new
      # class.  I do insist that a class be declared only once or with the same spec each time. 
      #
      # The reason for having this call is to allow one to create new message types easily, not to
      # encourage your artistic genius.  Simple classes only, please!
      if name.startswith("."): name = name[1:]
      if name in self.message_styles:
         if spec != self.message_styles[name]:
            raise ValueError("Debugging style class '"+name+"' mulitply declared.")
      else:
         self.message_styles[name] = spec
         if self._head_started:
            as_html = "<style type=\"text/css\">.{0} {1}</style>\n".format(name, spec)
            if self._head_is_open:
               self._head += as_html
            else:
               self.stream.write(as_html)

   def __enter__(self):
      return self

   def __exit__(self, exc_type, exc_value, exc_tb):
      if exc_type:
         tb = io.StringIO()
         traceback.print_tb(exc_tb, limit=10, file=tb)
         self.err("{0}: {1}\n{2}".format(exc_type, exc_value, tb.getvalue()))
      self.close()
   
   def __contains__(self, name):
      return name in self.keypatterns

   def __getitem__(self, what):
      if type(what) is int:
         return self.buffer[what]
      elif type(what) is str:
         whatMatcher = WildCardLookup(what)
         return [self.buffer[x] for x in self.buffer if self.buffer[x].key in whatMatcher]
      if type(what) is slice:
         what = su.slice2range(what, max=len(self.buffer))
      if type(what) is range:
         return [self.buffer[x] for x in what]
      else:
         msg = "{0} cannot be used to index {1}"
         raise TypeError(msg.format(su.a_classname(what), su.a_classname(self)))

   def __iter__(self): return self.keypatterns.__iter__()

   def pattern_iterator(self): return self.keypatterns.__iter__()
   def buffer_iterator(self): return self.buffer.__iter__()

   def pattern_count(self): return len(self.keypatterns)
   def msg_count(self): return self.count - 1 # message numbering starts at 1
   def buffer_count(self): return len(self.buffer)

   def _open(self, logdirpath):
      if self.path:
         return self
      if self.stream in [stdout, stderr]: 
         self.stream = None
      elif self.stream:
         self.stream.close()
         self.stream = None
      self.path = logdirpath 
      return self._start_the_head()

   def _start_the_head(self):
      headlines = [
         '<!DOCTYPE html>'
         '<html>'
         '<head>'
         '<meta charset="utf-8">',
         '<style type="text/css">'
         ]
      self._head_started = True
      self._head_is_open = True
      lines = [
      "."+name+" "+self.message_styles[name] for name in self.message_styles
      ]
      lines.sort() # NB. sort does NOT return "self"
      headlines += lines
      headlines.append('</style>\n')
      self._head = "\n".join(headlines)
      return self

   def add_patterns(self, *new_patterns):
      for pattern in self.prepare_patterns(new_patterns):
         if len(pattern) > 0:
            if pattern[0] == '+':
               pattern = pattern[1:]
               self.highpriority.add(pattern)
            self.keypatterns.add(pattern)

   def remove_patterns(self, *dead_patterns):
      for pattern in self.prepare_patterns(dead_patterns):
         self.keypatterns.remove(pattern)
         self.highpriority.remove(pattern)

   def raise_priority(self, *ptns):
      for ptn in self.prepare_patterns(ptns):
         self.keypatterns.add(ptn)
         self.highpriority.add(ptn)

   def lower_priority(self, *ptns):
      for ptn in self.prepare_patterns(ptns):
         self.highpriority.remove(ptn)

   def all_matched(self, *keys):
      return self.keypatterns.all_matched(self.prepare_patterns(keys))

   def any_matched(self, *keys):
      return self.keypatterns.any_matched(self.prepare_patterns(keys))

   def buffer_message(self, parms):
      self.count += 1
      parms["index"] = self.count
      self.buffer.append(DbgMessage(parms))

   def dbg(self, key, text, *, src=None, style=None, now=False):
      if (key in self.keypatterns) or not key:
         parms =  {}
         parms["key"] = key or ""
         parms["weakest_match"] = self.keypatterns.weakestPatternFor(key)
         parms["caller"] = self.mycallersname() if src is None else src
         parms["display_priority"] = 3
         if style: parms["style_class"] = style
         elif key in self.highpriority:  parms["style_class"] = "priority_msg"
         else: parms["style_class"] = "ordinary_msg"
         parms["body"] = text
         self.buffer_message(parms)
         if now: 
            if isinstance(now, str): self.flush(after=now)
            else: self.flush()
      # else key is not active, so I do nothing

   def err(self, text_or_err, src=None, bail_out=True):
      parms =  {}
      parms["caller"] =  self.mycallersname() if src is None else src
      parms["body"] = "<pre>"+str(text_or_err)+"</pre>"
      parms["display_priority"] = 1   # in English: "first priority!"
      parms["style_class"] = "error_msg"
      self.buffer_message(parms)
      if bail_out:
         if isinstance(text_or_err, Exception):
            raise text_or_err
         else:
            raise RuntimeError(text_or_err)

   def pre(self, key, text, *, src=None, style=None, now=False):
      if (key in self.keypatterns) or not key:
         if not src:
            src = self.mycallersname()
         self.dbg(key, "<pre>" + text + "</pre>", src=src, style=style, now=now)

   def warn(self, text_or_err, src=None, bail_out = False):
      parms =  {}
      parms["caller"] =  self.mycallersname() if src is None else src
      parms["body"] = "<pre>"+str(text_or_err)+"</pre>"
      parms["display_priority"] = 2   # second priority: after errors
      parms["style_class"] = "warning_msg"
      self.buffer_message(parms)
      if (bail_out or self._bail_on_warning):
         if isinstance(text_or_err, Exception):
            raise text_or_err
         else:
            raise RuntimeError(text_or_err)

   def flush(self, before="", after="", asis=False):
      self.dbg("dbg", "flush() called by {}".format(self.mycallersname()))
      if self.buffer_count() is 0 and len(before) is 0 and len(after) is 0:
         return 
      if not self._head_started:
         self._start_the_head()
      if self._head_is_open: # first time switch: close the head and open the body
         self.stream = open(self.path, mode='x')
         self.stream.write(self._head)
         self.stream.write('</head>\n<body>\n<code>\n')
         self._head_is_open = False
      if self.sortby is not "time":
         self.buffer.sort()
      if len(before) > 0:
         if asis:
            self.stream.write(before)
         else:
            self.stream.write('<p class="flush_before_after">{0}</p>\n'.format(before))
      self.dbg("dbg", "flushing buffer to {}".format(self.stream))
      for entry in self.buffer:
         self.stream.write(str(entry))
      if len(after) > 0:
         if asis:
            self.stream.write(after)
         else:
            self.stream.write('<p class="flush_before_after">{0}</p>\n'.format(after))
      self.stream.write("<hr>\n")
      self.buffer = []
      self._something_written = True

   def close(self, before="", after="", asis=False):
      self.flush(before, after, asis)
      if self._something_written:
         msg = "<p>Log ended, {1}: {0} entries</p>\n".format(self.count, time.asctime())
         self.stream.write(msg)
         self.stream.write('</code>\n</body>\n')
         if self._stream not in [stdout, stderr, None]:
            self._stream.close()
         elif self._stream is not None:
            self._stream.flush() # dump the stream's buffer (ours is empty!!!)
         self._stream = None
