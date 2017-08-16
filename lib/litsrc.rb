#!/usr/bin/env ruby
require "awesome_print"
require "cmdline"
require "dbg"
require "fileutils"
require "sysutils"
require "versioning"
class LiterateSource
   VERSION       = "1.0.1"
   UPDATED       = "2017-07-11"


   def self.addCmdlineParameters(spec)
      app      = spec.appname
      from_ext = spec.help_info[:from]
      to_ext   = spec.help_info[:to]
      spec.add_help(
         before: "#{app} transforms .#{from_ext} files into .html and .#{to_ext} files.\n",
         after: "See litsrc.html for more details.")
      spec.add_version(version: LiterateSource::VERSION,
         date: LiterateSource::UPDATED,
         appname: $PROGRAM_NAME)
      spec.add_string('-root',
         default: '',
         help: 'src, doc, and md are all relative to this path when they are relative')
      spec.add_string('-pub',
         default: '',
         help: 'if this is not "", it is the root directory for publishing the project')
      spec.add_string('-src',
         help: 'where to find the source',
         default: "src")
      spec.add_string('-doc',
         help: 'where to put the .html output ',
         default: "doc")
      spec.add_string('-rb',
         help: 'where to put the .rb output ',
         default: "rb")
      spec.add_string('-bak', 
         help: 'where to put backups relative to the directory backed up',
         default: "bak")
      spec.add_string('-css', 
         help: 'where to find stylesheets relative to the doc directory ',
         default: "css")
      spec.add_csv("-dbg", "--debug", 
         help: 'comma-separated list of debug keys',
         optional: true)
      spec.add_flag("-a", "--assure", 
         help: "create any missing output directories",
         default: true )
      spec.add_string("-s", "--show-source", 
         help: "show the Ruby source in the HTML output",
         default: '?' )
      spec.add_integer("-keep", 
         help: "the number of backups to keep per output file",
         default: 3)
      spec.add_integer("-tabs",
         help: "the number of spaces per tab",
         default: 3)
      spec.add_list_here('files',
         help: 'source files',
         optional: true)
   end
end


class LanguageSpec
   attr_reader :begins, :hide_show, :ends, :lang, :left_justify_md, :lib_ext, :src_ext
   attr_accessor :begins_code, :default_css, :ends_code
   def initialize(
      lang_name, src_extension, lib_extension, begins_section, ends_section,
      hide_show, left_justify=false
   )
      lang_name    = lang_name.downcase
      @lang        = lang_name.capitalize
      @src_ext     = src_extension
      @lib_ext     = lib_extension
      @default_css = "#{lang_name}md.css"
      @begins      = if begins_section.kind_of? Regexp then begins_section 
                     else Regexp.new begins_section
                     end
      @ends        = if ends_section.kind_of? Regexp then ends_section
                     else Regexp.new ends_section
                     end
      @hide_show   = if hide_show.kind_of? Regexp then hide_show
                     else Regexp.new hide_show
                     end
      @begins_code = "\n~~~~~{.#{lang_name}}\n"
      @ends_code   = "\n~~~~~~~~~~~~~~\n\n"
      @left_justify_md = left_justify
   end
end


class LiterateSource

   attr_reader :root, :src, :css, :files,                     # input parameters
               :doc, :ext, :md, :pub, :keep, :assure, :tabs   # output parameters

   def initialize(options, lang_spec)
      @options = options
      @lang_spec = lang_spec
      if options.dbg.length > 0
         DbgMgr.add_patterns options.dbg
         if DbgMgr.active? 'file'
            File.debug_on 'file'
         else
            File.debug_off
         end
         DbgMgr.open
      end
      DbgMgr.add_patterns options.dbg
      DbgMgr.pre "opt", "---------\n#{options.to_s.gsub(" ", "\n   ")}\n---------", esc: true
      # Paths are relative to the "root":
      @root = options.root
      # Input paths
      begin
         get_the_source_paths options
         get_the_output_paths options, lang_spec
         get_the_css_path options.css, lang_spec.default_css
      rescue Exception => e
         DbgMgr.close
         raise e
      end
      DbgMgr.pre("paths",
          "Directory paths:\n    root=#{root}\n    src=#{@src}\n" +
          "    doc=#{@doc}\n    css=#{@css}\n    lib=#{@lib}\n    md=#{@md}"
          )
      # some admin stuff
      @show_source = options.s
      @head_index = -1
      @head = nil
   end


   def process_files
      begin
         @files.each do |file|
            name = File.basename(file, File.extname(file))
            if not name.end_with? '.' then name += '.' end
            lines = File.readlines file
            sections = Sections.new lines, name, @options, @lang_spec
            if DbgMgr.active? "out"
               output = "non source sections:\n"
               sections.md_sections.each {|s| 
                  output += "  #{s.class}: #{s.first_in}...#{s.first_after}"
               }
               ouput += "\nruby sections\n"
               sections.lib_sections.each {|s|
                  output += "  #{s.class}: #{s.first_in}...#{s.first_after}"
               }
               DbgMgr.put "out", (output + "\nend\n")
            end
            write_the_lib_file name, lines, sections.sections
            md_file = write_the_md_file name, lines, sections.head, sections.sections
            if write_the_html_file md_file, name
               if  not @save_md
                  File.delete md_file
               end
            end
            DbgMgr.flush 
         end     
      rescue Exception => e
         DbgMgr.err e, now: true # flush the debugging buffer, but do NOT close the stream
      end
      DbgMgr.close
   end

   def publish
      if not @pub.nil?
         begin
            create_the_index
            populate_a_directory @src, @pub_src, @src_ext
            populate_a_directory @lib, @pub_lib, @lib_ext
            populate_a_directory @doc, @pub_doc, 'html'
            populate_a_directory @css, @pub_css, 'css'
            populate_a_directory @xmp, @pub_xmp, @lib_ext         
         rescue Exception => e
            DbgMgr.err e, now: true # flush the debugging buffer, but do NOT close the stream
         end
      end
      DbgMgr.close
   end

   private
   def get_the_source_paths(options)
      @src = options.src
      DbgMgr.put "paths", "before: options src is '#{@src}' and @root is '#{@root}'"
      if @root.nil? or @root == ''
         if @src.nil?
            @root = Dir.getwd
            @src = File.normalized_path @root, child: 'src'
         else
            @src = File.absolute_path @src
            @root = File.parent_directory @src
         end
      else
         @root = File.absolute_path @root
         @src = File.normalized_path @root, child: 'src', alternate: @src
      end
      DbgMgr.put "paths", "after: options src is '#{@src}' and @root is '#{@root}'"
      @files = options.files.collect { | file | File.expand_path file, @src}
   end

   def get_the_output_paths(options, lang_spec)
      # the output paths
      @save_md = DbgMgr.active? "md"
      @doc = File.normalized_path @root, child: 'doc', alternate: options.doc
      @examples = File.normalized_path @doc, child: 'examples'
      @md = if @save_md then File.normalized_path @root, child: 'md', alternate: options.md
            else @doc
            end
      @lib = File.normalized_path @root, child: 'lib', alternate: options.lib
      @src_ext = lang_spec.src_ext
      @lib_ext = lang_spec.lib_ext
      if options.pub == ''
         @pub = @pub_src = @pub_lib = @pub_doc = @pub_css = @pub_xmp = nil
      else
         @pub = File.expand_path options.pub
         File.assure_directory @pub
         @pub_src = File.normalized_path @pub, child: 'src'
         @pub_lib = File.normalized_path @pub, child: 'lib'
         @pub_doc = File.normalized_path @pub, child: 'doc'
         @pub_css = File.normalized_path @doc, child: 'css'
         @pub_xmp = File.normalized_path @doc, child: 'examples'
         File.assure_directory @pub_src
         File.assure_directory @pub_lib
         File.assure_directory @pub_doc
         File.assure_directory @pub_css
         File.assure_directory @pub_xmp
      end
      if options.assure
         File.assure_directory @doc
         File.assure_directory @examples
         File.assure_directory @md if @save_md
         File.assure_directory @lib
      end
      # what previous output should be saved as backups?
      @keep = options.keep
      if @keep == 0 or options.bak.nil?
         @doc_bak = @md_bak = @lib_bak = nil
      else
         @doc_bak = File.normalized_path @doc, child: options.bak
         @md_bak = File.normalized_path @md, child: options.bak
         @lib_bak = File.normalized_path @lib, child: options.bak
         DbgMgr.pre("paths", "bak:\n    doc=#{@doc_bak}\n    md=#{@md_bak}\n    lib=#{@lib_bak}")
         if options.assure
            File.assure_directory @doc_bak if @doc != @doc_bak
            File.assure_directory @md_bak if @save_md and @md != @md_bak
            File.assure_directory @lib_bak if @lib != @lib_bak
         end
      end
   end

   DEFAULT_CSS = %q<
@media print { 
   body { font-size: 11pt; }
   pre { font-family: Courier; font-size: smaller; }
   .exampleCode {
      background-color: blanchedalmond !important;
      -webkit-print-color-adjust: exact; 
      font-family: Monaco; 
      font-size: 9pt;
   }
   .sourceCode  { 
      background-color: lightgray !important;
      -webkit-print-color-adjust: exact; 
      font-family: Courier; 
      font-size: 9pt; ]
    }
}
.author { text-align: center; font-size: 12pt; font-weight: bold; }
.date { text-align: center; font-size: smaller; }
code { font-family: Monaco; font-size: smaller; }
pre {
    -moz-tab-size:    3;
    -o-tab-size:      3;
    -webkit-tab-size: 3;
    -ms-tab-size:     3;
    tab-size:         3;
    line-height: 1.125em
}
@media screen {
   h4 { text-decoration: underline; }
   .exampleCode { background-color: blanchedalmond; font-family: Monaco; font-size: 9pt; }
   .sourceCode  { background-color: lightgray; font-family: Courier; font-size: 11pt;  }
}
.h1Code { font-family:Courier; font-size: 20pt; font-weight: normal; }
.h2Code { font-family:Courier; font-size: 18pt; font-weight: normal; }
.h3Code { font-family:Courier; font-size: 14pt; }
.title     { text-align: center;  font-size: 17pt; font-weight: bold;}}
.titleCode { font-family: Courier; font-size: 17pt; font-weight: normal; }
>
   def get_the_css_path(css_path, default_css_filename)
      #exists = File.exists? css_path
      css_path = File.expand_path css_path, @doc
      DbgMgr.put "in_css",  "css file at #{css_path}?"
      if File.exists?(css_path) and  File.directory?(css_path)
         css_path +=  "/#{default_css_filename}"
      end
      if not css_path.end_with? ".css"  # then it cannot be the file!
         File.assure_directory css_path # make sure it exists as a directory
         css_path += "/#{default_css_filename}" # and use the default file name
      end
      if not File.exists? css_path
         DbgMgr.warn "New .css file #{css_path} created."
         File.open(css_path, "w") { |io| io.puts DEFAULT_CSS }
      else
         DbgMgr.put "in_css", "using css file '#{css_path}'"
      end
      @css = css_path
   end


   def write_the_html_file(mdpath, name)
      DbgMgr.put "out_html", "writing #{name}html"
      file = File.join @doc, (name + "html")
      VersionedFile.new_version file, true, bak: @doc_bak, keep: @keep
      cmd = "pandoc  -p -s -S -f markdown -t html5 --toc --toc-depth=4 " +
            "--self-contained --css #{@css} -o #{file} #{mdpath}"
      DbgMgr.put "out_html", cmd
      output = %x[#{cmd}]
      [$?.exitstatus, output]

   end
   def write_the_md_file(name, lines, head, sections) 
      DbgMgr.put "out_md",  "Writing #{name}md!"
      begin
         keep = if @save_md then @keep else 0 end
         output_path = File.join @md, (name + "md")
         #show_source = if head.show.nil? then false else head.show
         VersionedFile.open(output_path, bak: @md_bak, keep: keep, mode: 'w') do |fd|
            fd.puts "% #{head.title}\n% #{head.author}\n% #{head.date}\n"
            sections.each {| section | section.to_md(fd) }
         end
      rescue Exception => ex
         DbgMgr.err ex, my_caller: "write_the_md_file"
         raise
      end
      output_path
   end

   def write_the_lib_file(name, lines, sections)
      DbgMgr.put "out_lib",  "Writing #{name}#{@lib_ext}!"
      begin
         file = File.join @lib, "#{name}#{@lib_ext}"
         VersionedFile.open(file, bak: @lib_bak, keep: @keep, mode: 'w') do |fd|
            sections.each { | section | section.to_lib fd }
         end 
      rescue Exception => ex
         DbgMgr.err ex, my_caller: "write_the_lib_file"
         raise
      end
   end
      
   def exec_cmd cmd, check_output = true
      DbgMgr.put "exec", cmd
      output = %x[#{cmd}]
      status = $?.exitstatus
      if status != 0 or (check_output and output != nil and output.length > 0)
          msg = "'#{cmd}' failed with exit status=#{exit_status}"
          if check_output
            msg += ", output='#{output}'"
          end
         STDERR.puts msg
         DbgMgr.warn output
         return false
      else
         DbgMgr.put "exec", "#{name}html created, exit code #{status}"
         return true
      end
  end

   def create_the_index
      pubname = File.basename @pub
      index_md = File.expand_path "index.md", @root
      if not File.exists(index_md)
         File.write index_md, "The source files for the #{pubname} package are:\n"+
            "<blockquote>\n<!-- source links -->\n</blockquote>\n"
      end
      index_in = File.new(index_md)
      ls_cmd = "ls #{@src}/*.#{@src_ext}"
      file_list = %x[ls_cmd].collect do |path|
         "[#{File.basename path}](path)"
      end
      Range.new(0, file_list.size() - 2).each do |n|
         file_list[n] += "\\\n"
      end
      temp_index_md = "#{@pub_doc}/index.md"
      File.open(temp_index_md, "w") do |out|
         line = index_in.gets
         while not line.nil?
            if line.strip.start_with? "<!-- source links -->"
               file_list.each do |line|
                  out.puts line
               end
            else
               out.puts line
            end
         end
      end
      file = File.join @pub_doc, "index.html"
      cmd = "pandoc  -p -s -S -f markdown -t html5 --toc --toc-depth=4 " +
            "--self-contained --css #{@css} -o #{file} #{temp_index_md}"
      if exec_cmd cmd
         return exec_cmd("rm #{temp_index_md}")
      end
      false 
   end

   def populate_a_directory src_path, tgt_path, extension
      # empty the target directory of files that have the same extension as
      # the copied files, and if that succeeds, do the copy from the source
      dead_files = File.join tgt_path, "*#{extension}"
      if exec_cmd "rm #{dead_files}"
         new_files = File.join src_path, "*#{extension}"
         return exec_cmd "cp #{new_files} #{tgt_path}"
      end
      false
   end

   
   class Section
      attr_reader :first_in, :first_after
      def initialize(first_in, first_after, lines)
         @first_in = first_in
         @first_after = first_after
         @lines = lines
      end
      def to_s()
         "#{self.class}(#{@first_in}, #{@first_after})"
      end
   end

   class Head < Section
      attr_accessor :title, :author, :date, :tabsize, :show, :left_justify
      attr_reader :lines
      def self.newFromOptions(options, lang_spec, name)
         head = Head.new -1, 0, []
         head.set_from_defaults options, lang_spec, name
         head
      end

      def self.newFromLines(begins, ends, lines, options, lang_spec, name)
         head = Head.new begins, ends, lines
         head.set_from_lines 
         head.set_from_defaults options, lang_spec, name
         head
      end

      def initialize(first_in, first_after, lines)
         super first_in, first_after, lines
         @title = nil
         @author = nil
         @date = Date.today.iso8601
         @tabsize = nil
         @show = false
         @left_justify = false
      end

      KEYS = Set.new ['author', "date", 'show source', 'tab size', 'title']
      def set_from_lines()
         type = ''
         buffers = Hash.new ''
         (@first_in+1 ... @first_after).each do |n|
            line = @lines[n].rstrip
            if line.length == 0 then next
            elsif line[0] == " " or line[0] == "\t"
               if type != '' # this is a continuation line
                  buffers[type] += "\n "+line[1 .. -1] # get rid of the tab if one leads off
               else
                  raise SyntaxError.new "No section key for line #{n} in the head"
               end
            else
               line.lstrip!
               colon_index = line.index ':'
               if colon_index.nil? then possible_key = ''
               else 
                  possible_key = line[0 ... colon_index].downcase 
                  rest_of_line = line[colon_index+1 .. -1].lstrip
               end
               DbgMgr.put "head",  "#{possible_key} key?"
               if KEYS.member? possible_key
                  type = possible_key
                  if type == 'tab size'
                     @tabsize = Integer(rest_of_line)
                  elsif type == 'show source'
                     @show = rest_of_line.strip.to_b
                  else
                     if buffers[type].length > 0
                        buffers[type] += "\n  "
                     end
                     buffers[type] += line[colon_index+1 .. -1]
                  end
               elsif type != '' # may just be a ':' in an address or title continuation line
                  buffers[type] += "\n  " + line
               else
                  raise SyntaxError.new "Bad section key, #{type} for line #{n} in the head"
               end
            end
         end
         if buffers.member? "title" then @title = buffers["title"] end
         if buffers.member? "author" then @author = buffers["author"] end
         if buffers.member? "date" then @date = buffers["date"] end
         if buffers.member? "tab size" then @tabsize = Integer buffers["tab size"] end
         if buffers.member? "show source" then @show = buffers["show source"].to_b end
         if buffers.member? "left justify markdown"
            @left_justify = buffers["left justify markdown"]
         end
      end

      def set_from_defaults(options, lang_spec, name)
         if @title.nil? then @title = "#{name}.#{lang_spec.src_ext}" end
         if @date.nil? then @date = Date.today.iso8601 end
         if @tabsize.nil? then @tabsize = options.tabs end
         if @left_justify.nil? then @left_justify = lang_spec.left_justify_md end
         if options.s != '?' then @show = options.s.to_b 
         elsif @show.nil? then @show = false
         end
      end
      def to_md(fd)
         # do nothing!
      end
      def to_lib(fd)
         # do nothing!
      end
   end

   class Markdown < Section
      def initialize(section_spec, lines, undent)
         super section_spec.begins+1, section_spec.ends, lines
         @indent = if undent then section_spec.indent else 0 end
      end
      def to_md(fd)
         if @indent == 0
            (@first_in ... @first_after).each do |n|
               fd.puts @lines[n] 
            end
         else # trim on the  left to justify the markdown
            (@first_in ... @first_after).each do |n|
               line = @lines[n]
               fd.puts line[@indent ... line.length]
            end
         end
      end
      def to_lib(fd)
         # do nothing!
      end
   end

   class Code < Section 
      def initialize(first_in, first_after, lines, show, lang_spec)
         super first_in, first_after, lines
         @show    = show.to_b
         @leader  = lang_spec.begins_code
         @trailer = lang_spec.ends_code
      end
      def to_md(fd)
         if @show
            fd.puts @leader # pandoc "fence": \n~~~~{.lang_name}\n
            (@first_in ... @first_after).each {|n| fd.puts @lines[n]}
            fd.puts @trailer # pandoc "fence": ~~~~~~\n\n
         end
      end
      def to_lib(fd)
         (@first_in ... @first_after).each {|n| fd.puts @lines[n]}
      end
   end

   
   class Sections
      SectionSpec = Struct.new :begins, :ends, :indent, :kind
      attr_reader :head, :sections
      def initialize(lines, name, options, lang_spec)
         @lines = lines
         @name = name
         @head = Head.newFromOptions options, lang_spec, @name
         section_specs = find_the_section_specs options, lang_spec
         @sections = list_all_the_sections section_specs, lang_spec
      end
      private
      def find_the_section_specs(options, lang_spec)
         section_specs = [SectionSpec.new(-1, -1, 0, :before)]
         last_start = -1
         type_started = :none
         indent = 0
         head_seen = false
         first_md = -1
         begins = lang_spec.begins
         ends = lang_spec.ends
         hide_show = lang_spec.hide_show
         @lines.each_with_index do | line, n | # find the head and md sections
            case 
            when (begins =~line) == 0
               last_start = n
               line = line.downcase
               if line.index("<head>") != nil
                  type_started = :head
                  if  first_md >= 0
                     raise SyntaxError.new "line #{n}: head section must come before any markdown"
                  elsif head_seen
                     raise SyntaxError.new "Second 'head' begun at line #{n}"
                  else 
                     head_seen = true
                  end
               elsif line.index("<md>") != nil
                  type_started = :md
                  indent = line.index /\S/
                  if first_md < 0 and (not head_seen) and @head.tabsize != 0
                     tabsize = @head.tabsize
                     @lines = @lines.collect { |line| line.expandtabs tabsize}
                  end
               else
                  raise SyntaxError.new "Unexpected begin line match: '#{@lines[n]}'"
               end
            when (ends =~ line) == 0
               end_match = /<\/(md|head)>[ \t]*\n?/.match(line)
               line_ender = if end_match.nil? then nil else line[end_match.captures[0]] end
               case type_started
               when :head
                  if line_ender.nil? or line_ender=='head'
                     section_specs.push SectionSpec.new(last_start, n, indent, :head)
                     @head = Head.newFromLines last_start, n, @lines, options, lang_spec, @name
                     if @head.tabsize != 0
                        @lines = @lines.collect { |line| line.expandtabs @head.tabsize}
                     end
                  else
                     SyntaxError.new "Bad ender, '#{line} 'for a <head> section"
                  end
               when :md 
                  if line_ender.nil? or line_ender=='md'
                     section_specs.push SectionSpec.new(last_start, n, indent, :md)
                  else
                     SyntaxError.new "Bad ender, '#{line}' for an <md> section"
                  end
               when :none
                  if not line_ender.nil?
                     raise SyntaxError.new "Unmatched ender '#{line}' at line #{n}"
                  end
               end
               last_start = -1
               type_started = :none
            when (hide_show =~ line) == 0
               if type_started == :none
                  line.downcase!
                  kind = if line.index("show") != nil then :show
                         elsif line.index("hide") != nil then :hide
                         else raise SyntaxError.new "unrecognized hide/show directive '#{line}'"
                         end
                  section_specs.push SectionSpec.new n, n, 0, kind
               else
                  msg = "directive '#{line.strip}' cannot sit in a(n) #{type_started} section"
                  raise SyntaxError.new msg
               end
            end
         end
         if type_started != :none
            msg = "Unexpected EOF with open #{type_started} at line #{last_start}"
            raise EOFError.new msg
         end
         section_specs.push SectionSpec.new @lines.length, @lines.length, 0, :ends
         DbgMgr.pre "section_specs", section_specs.to_s.gsub(/, #/, "\n #"), esc: true
         section_specs
      end

      def list_all_the_sections section_specs, lang_spec
         # Code sections can now be found as the lines not in the head or md sections
         sections = []
         prior_stop = -1     # the ends index or the directive index
         show = @head.show   # initially the default, then managed by directives
         left_justify = lang_spec.left_justify_md or @head.left_justify
         section_specs.each do |section_spec|
            first_code  = prior_stop + 1 
            prior_stop  = section_spec.ends  # first after the section delimited by section_spec
            if first_code < section_spec.begins # there may be some code immediately before
               code_section = Code.new first_code, section_spec.begins, @lines, show, lang_spec
               sections.push code_section
            end
            case section_spec.kind
            when :ends then return sections
            when :head then sections.push @head
            when :hide then show = false
            when :md   then sections.push Markdown.new section_spec, @lines, left_justify
            when :show then show = true
            else
               DbgMgr.put "out_list", "skip a #{section_spec.kind} section_spec" 
            end
         end
         raise Exception.new "Missing :ends SectionSpec"
      end
   end
end
