
import idbg
import os
import re
import shutil
import sys
from sysutils import getitem


## Nota bene: the class _FileUtilParameters is here only to provide a single, private
## module-wide repository for the limited state I have to maintain, which are the
## defaults for how many backups to keep and where to put them, and whether to stream
## verbose debugging output.  The upshot is that the class's "__init__" will get called 
## exactly once: that is, in the line of code immediately following the class's
## definition, where the private variable "_fups" is created.  That is why it is
## safe to put the call to "debug_init" in "__init__".  "debug_init" will be called
## exactly once, which just happens to be the number of instances of this class that
## gets created.

class _FileUtilParameters(idbg.DbgClient):
   def __init__(self):
      self.__class__.debug_init()
      idbg.DbgClient.configure_debugging("futils")
      self.backups_kept = 5
      self.backup_to    = "bak"

_fups = _FileUtilParameters()

def get_backup_defaults():
   global _fups
   return [_fups.backups_kept, _fups.backup_to]

def set_default_backups_kept(backups_kept):
   global _fups
   _fups.backups_kept = None if backups_kept is None else int(backups_kept)

def set_default_backup_directory(path, create=None):
   global _fups
   if os.path.isabs(path):
      if os.path.exists(path):
         if not os.path.isdir(path):
            raise NotADirectoryError("'{0}' exists, but is not a directory".format(path))
      elif create is True:
         assureDirectory(path)
      elif create is False:
         raise FileNotFoundError("Directory '{0}' does not exist".format(path))
      elif create is not None:
         msg = "Boolean or None required for 'create', but {0} passed."
         _fups.raise_error(TypeError(msg.format(type(create))))
      else:
         fileutils_debug_out( "'{0}'' does not exist. It will be created if needed.", path)
   _fups.backup_to = path
   fileutils_debug_out("Default backup directory is now {0}!".format(_fups.backup_to))

def start_debug_fileutils():
   global _fups
   _fups.start_debugging()

def pause_debug_fileutils():
   global _fups
   _fups.pause_debugging()

def fileutils_debug_out(msg, *parameters):
   global _fups
   _fups.dbg_write(msg.format(*parameters))


def fopen(path, mode="w", encoding="utf-8", where=None, toKeep=None):
   if os.path.exists(path):
      if 'x' in mode:
         msg = "'{0}' already exists: call fileutils.newVersion directly to copy it."  
         raise FileExistsError(msg.format(path))
      elif 'a' in mode or 'w' in mode or '+' in mode:
         # the file is writable, so we need to back it up, and we can live with just renaming it
         # if we're opening for write ('w' in mode).
         newVersion(path, where, toKeep, 'w' in mode)
   else:
      fileutils_debug_out("{0} is a new file: no backup created.", path)
   return open(path, mode=mode)

def newVersion(path, where=None, toKeep=None, rename=True):
   global _fups
   if not os.path.exists(path):
      return
   elif not os.path.isfile(path):
      msg = "attempt to back up a path, {0}, that is not a regular file."
      _fups.issue_warning(msg.format(path))
      return
   path = os.path.abspath(path)
   defaultToKeep, defaultWhere = get_backup_defaults()
   toKeep = defaultToKeep if toKeep is None else int(toKeep)
   if toKeep == 0:
      msg = "Request to backup '{0}', but 0 versions are to be kept!!!"
      _fups.issue_warning(msg.format(path)) 
      return 
   dirPath, prefix, suffix = parseAPathForVersioning(path)
   if where is not None: 
      backupDir = where
   elif defaultWhere:
      backupDir = defaultWhere
   else:
      _fups.raise_error(FileNotFoundError("No backup directory has been specified!"))
   if not os.path.isabs(backupDir): 
      backupDir = os.path.join(dirPath, backupDir)
   versions = getVersions(backupDir, prefix, suffix)
   newVersion = nextVersionName(prefix, suffix, versions)
   newPath = os.path.join(backupDir, newVersion)
   assureDirectory(backupDir)
   # if there are too many backups, delete some before creating a new one
   if toKeep <= len(versions):
      excess = len(versions) + 1 - toKeep
      for n in range(0, excess):
         fileutils_debug_out("removing version {0} of {1}", versions[n], path)
         os.remove(os.path.join(backupDir, versions[n]))
   if rename: # don't save original: usually because it will be truncated on opening for write
      os.replace(path, newPath)
   else:      # use copy2 to copy as much file metadata as the OS allows
      shutil.copy2(path, newPath) 

def backup(path, where=None, toKeep=None):
   if toKeep is None:
      defaultKept, ignore = get_backup_defaults()
      if defaultKept is 0: toKeep = 1
   newVersion(path, where, toKeep, False)


def parseAPathForVersioning(path):
   global _fups
   dirPath, baseName = os.path.split(path)
   if len(baseName) is 0:
      msg = "Path '{0}' does not name a file.".format(path)
      _fups.raise_error(FileNotFoundError(msg))
   if "." in baseName:
      lastDot = baseName.rfind('.')
      suffix = baseName[lastDot:]
      prefix = baseName[0:lastDot+1]
   else:
      suffix = ""
      prefix = baseName +"." # this is the only dot in baseName!
   return (dirPath, prefix, suffix)

def getVersions(dirpath, prefix, suffix):
   if not os.path.exists(dirpath):
      fileutils_debug_out("no such directory '{0}'?", dirpath)
      return []
   matcher = re.compile(re.escape(prefix)+"[0-9]+"+re.escape(suffix))
   raw = [ entry for entry in os.scandir(dirpath) if matcher.fullmatch(entry.name) ]
   rawSorted = sorted(raw, key = lambda entry: entry.stat().st_ctime)
   return [entry.name for entry in rawSorted]

def nextVersionName(prefix, suffix, versions):
   currentCount = len(versions)
   if currentCount is 0:
      return prefix+"1"+suffix
   lastName = versions[currentCount-1]
   lastVersion = lastName[len(prefix): len(lastName)-len(suffix)]
   nextVersion = int(lastVersion) + 1
   nextName = prefix+str(nextVersion)+suffix
   while nextName in versions:
      nextVersion += 1
      nextName = prefix+str(nextVersion)+suffix
   return nextName


def expandPathList(aStringOrStringTuple):
   if type(aStringOrStringTuple) is str:
      return aStringOrStringTuple.split(os.pathsep)
   else:
      answer = []
      for path in aStringOrStringTuple:
         for adir in path.split(os.pathsep):
            answer.append(adir)
      return answer


def normalizeAPath(rootpath=None, usualchild=None, path=None):
   if not rootpath:
      rootpath = os.getcwd()
   if path:
      if os.path.isabs(path):         
         raw = path
      elif path.startswith("./") or path.startswith("../") or path.startswith("~/"):
         raw = path # implied absolute paths: "here" and "home"                 
      else:
         raw =  os.path.join(rootpath, path)
   elif usualchild:
      raw = os.path.join(rootpath, usualchild)
   else:
      raise FileNotFoundError("Either a path or a usualchild must be supplied")
   return os.path.abspath(raw) # gets rid of pesky dots, double dots and tildes

def assureDirectory(*paths):
   global _fups
   for path in paths:
      if not os.path.exists(path):
         fileutils_debug_out("creating directory '{0}'", path)
         os.makedirs(path)
      elif not os.path.isdir(path):
         msg = "'{0}' exists, but is not a directory".format(path)
         _fups.raise_error(NotADirectoryError(msg))

def getParent(path):
   return os.path.split(os.path.abspath(path))[0]

