#!/usr/bin/env ruby
require "cmdline"
require "litsrc"


class Panpype < LiterateSource
   VERSION       = "1.0.1"
   UPDATED       = "2017-07-11"
   LANG_SPEC     = LanguageSpec.new(
      "python", "pype", "py",
      /^[ \t]*('''|""") +<(md|head)>[ \t]*\n?$/, 
      /^[ \t]*('''|""")([ \t]+#[ \t]*<\/(md|head)>)?[ \t]*\n?$/,
      /^[ \t]*#=(=*)>( *)<(show|hide)( code)?>[ \t]*\n?$/,
      true
      )
   def initialize(options)
      super options, LANG_SPEC
   end
end

# If this has been invoked directly from the command line...
cmd_names = Set.new ["panpype.rb", "panpype", "pythonmd.rb", "pythonmd"]
cmdname =  File.basename($PROGRAM_NAME)
if cmd_names.member? cmdname
   begin
      fromto = { from: "pype", to: "py"}
      args = CmdLine.parse(appname: cmdname, helpinfo: fromto) do |spec|
         LiterateSource.addCmdlineParameters spec
      end
   rescue RuntimeError => re 
      print("Could not parse the command line: ", re.message, "\n")
      exit(1001)
   end
   Panpype.new(args).process_files
   exit(0)
end
