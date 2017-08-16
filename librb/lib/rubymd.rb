#!/usr/bin/env ruby

require "cmdline"
require "litsrc"


EXPECTED_NAME_RE = /ru?by?md(\.rb(md)?)?/


class RubyMd < LiterateSource
   VERSION       = "1.0.1"
   UPDATED       = "2017-07-11"
   LANG_SPEC     = LanguageSpec.new(
      "ruby", "rbmd", "rb",
      /^=begin[ \t]+<(md|head)>[ \t]*\n?$/, 
      /^=end([ \t]+#[ \t]*<\/(md|head)>)?[ \t]*\n?$/,
      /^#=(=*)>( *)<(show|hide)( code)?>[ \t]*\n?$/,
      false
   )
   def initialize(options)
      super options, LANG_SPEC
   end
end

# Normally this has been invoked directly from the command line...if not do nothing
cmdname = File.basename($PROGRAM_NAME)
if not EXPECTED_NAME_RE.match(cmdname).nil? 
   begin
      fromto = { from: "rbmd", to: "rb"}
      args = CmdLine.parse(appname: cmdname, helpinfo: fromto) do |spec|
         LiterateSource.addCmdlineParameters spec
      end
   rescue RuntimeError => re 
      print "Could not parse the command line: ", re.message, "\n"
      exit(1001)
   end
   RubyMd.new(args).process_files
end
