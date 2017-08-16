
require 'awesome_print'
require 'csv'
require 'ostruct'
require 'rbconfig'
require 'set'
require 'sysutils'



module CmdLine

   def self.parse(argv=ARGV, 
                  appname: nil, 
                  helpinfo: {},
                  debug: '', 
                  group_flags: true, 
                  may_abbreviate: true, 
                  cat_on_dup: true,
                  spec: nil, 
                  &spec_builder)
      if spec.nil?
         spec = CmdLine::Spec.new(
               appname: appname, 
               helpinfo: helpinfo,
               debug: debug, 
               group_flags: group_flags, 
               may_abbreviate: may_abbreviate, 
               cat_on_dup: cat_on_dup, 
               &spec_builder)
      end
      if debug.length == 0
         debug = spec.debug
      end
      CmdLine::Parser.new(spec, argv, debug: debug).args
   end


   CMD_LINE_END = /^--$/
   LEADING_NO_REG_EXP = /^((NO|no)-?)?(.+)$/
   VALUE_TYPES  = [:NIL, :BOOL, :CSV, :END, :HELP, :LIST, :STRING, :VERSION]
   COUNT_TYPES  = [:UNKNOWN, :NONE, :ONE, :ZERO_OR_ONE, :ZERO_OR_MORE, :ONE_OR_MORE]
   ROLE_TYPES = [:UNKNOWN, :END, :HELP, :KEYWORD, :POSITION, :VERSION]
   VALUE_SEPARATORS = Regexp.new("[,#{RbConfig::CONFIG['PATH_SEPARATOR']}]")


   class Parm

      attr_reader :role, :debug, :howmany, :long_key, :short_key, :value_type
      attr_reader :attrnames, :position
      attr_accessor :default, :help, :vet

      SHORT_REG_EXP  = /^((-{1,2})?([^-=][^=]*)?)$/
      LONG_REG_EXP   = /^--([^-=][^=]*)/

      def initialize(short_key, long_key='', rest)
         # set the debug keys early, so we can do filtered debugging prints from the start
         # this is really for debugging...ordinary users should ignore this.  It is passed
         # in by Spec's methods for registering parameters.
         @debug = rest[:debug]
         # the short (or only) name determines the role
         short_match = SHORT_REG_EXP.match short_key
         if short_match.nil?
            raise ArgumentError.new "#{short_key} is not a valid short key"
         end
         ignore, short_dashes, short_name = short_match.captures
         @short_key = short_key
         role = rest[:role]
         @role = if not role.nil?
                     role.to_sym
                  elsif short_key == '--' 
                     :END
                  elsif short_dashes.nil?
                     :POSITION
                  else 
                     :KEYWORD
                  end
         if not ROLE_TYPES.member?(@role)
            raise "role, #{@role} not recognized"
         end
         long_match = LONG_REG_EXP.match long_key
         if long_match.nil? 
            if long_key.length > 0
               raise ArgumentError.new "#{long_key} is not a valid long key"
            else
               @long_key = nil
            end
         else
            if @role == :POSITION
               raise ArgumentError.new "#{@short_key} is positional: long key not permitted"
            end
            @long_key = long_key
            long_name = long_match.captures[0] 
            if @short_key.start_with? '--' 
               if @long_key != @short_key
                  raise "only one double-dashed key allowed, not #{short_key}/#{long_key}."
               else
                  @long_key = nil
               end
            end
         end
         # derive the attribute names from the short and long names.  A single name may be 
         # provided in the arguments to this call as rest[:attrname].  If no such name is
         # provided, the short and long names are both used.  They are stripped of the leading
         # dashes, the remaining dashes are converted to underscores, and non-"word"
         # characters are removed.    
         @attrnames = []
         attrname = rest[:attrname]
         if attrname != nil && attrname.length > 0
            if @debug.member? 'attrs' then print "attr from user\n" end
            @attrnames.push attrname
         else 
            if short_name != nil
               short_name = short_name.tr_s('-', '_')-/\W/
               if short_name.length > 0 
                  @attrnames.push short_name
                  if @debug.member? 'attrs'
                     print "attribute name '#{short_name}' pushed\n"
                  end
               end
            end
            if not @long_key.nil?
               long_name = long_name.tr_s('-', '_')-/\W/
               @attrnames.push long_name
               if @debug.member? 'attrs' 
                  print "attribute name '#{long_name}' pushed\n"
               end
            end
         end
         @default = rest[:default]
         howmany = rest[:howmany]
         if howmany == nil
            @howmany = if default.nil? then :ONE # no default: cmd line must supply if key found
                       else :ZERO_OR_ONE
                       end
         else
            @howmany = howmany.to_sym
            if not COUNT_TYPES.member?(@howmany)
               raise "count type, #{@howmany} not recognized"
            end
         end

         value_type = rest[:value_type]
         if value_type.nil?
            if @role == :KEYWORD and @howmany == :NONE then @value_type = :BOOL
            else @value_type =:STRING
            end
         else
            @value_type = value_type.to_sym
            if VALUE_TYPES.index(@value_type) == nil
               raise "value type, #{@value_type} not recognized"
            end
         end

         @vet = rest[:vet]
         if not (@vet.nil? or vet.respond_to?(:call))
            raise "if non-nil, vet must respond to :call: #{@vet} does not!"
         end
         @help = rest[:help] || '???'
      end

      def arg_look
         raise "subclass must implement"
      end

      def help_msg
         if @default.nil?
            "\t#{arg_look}:  #{@help}.\n"
         else
            "\t#{arg_look}:  #{@help}. Default: #{@default}\n"
         end
      end

      def printname
         if @long_key.nil?
            @short_key
         else
            "#{@short_key}[#{@long_key}]"
         end
      end

      # the following methods are not intended for public use, but rather by Spec and Parser
      # instances in this module

      def _call_vet(what_to_check)
         if @vet.nil? then what_to_check
         else @vet.call what_to_check
         end
      end

      def _set_position(value); @position = value end       
   end

   class Flag < Parm
      def initialize(short_key, long_key='', **rest)
         rest[:howmany] = :NONE
         rest[:value_type] = :BOOL
         rest[:default] = if rest[:default].nil? then false else rest[:default] end
         super(short_key, long_key, rest)
         @add_negative = rest[:add_negative] || false
      end
      def arg_look
         if @add_negative
            negative_prefix = if @add_negative then "[NO|no][-]"; else "" end
            dashes, short = /(--?)?(\w*)/.match(@short_key).captures
            short = "#{dashes}#{negative_prefix}#{short}"
            if not @long_key.nil?
               dashes, long_key = /(--?)?(\w*)/.match(@long_key).captures
               long_key = ", #{dashes}#{negative_prefix}#{long_key}"
            else
               long_key = ""
            end
         else
            short = @short_key
            long_key = if not @long_key.nil? then @long_key; else "" end
         end
         "#{short}#{long_key}"
      end
   end

   class KeyValue < Parm
      def initialize(short_key, long_key='', **rest)
         super
         if short_key[0] != '-'
            raise "command line key, #{short_key}, does not start with '-' as required."
         end
      end
      def arg_look
         dashes, body = /(--?)?(\w*)/.match(@short_key).captures
         body.upcase!
         case @howmany
         when :ZERO_OR_ONE then data = "#{body}?"
         when :ONE then data = body
         when :ZERO_OR_MORE then data =  "[#{body}1[,#{body}2[,...]]]}"
         when :ONE_OR_MORE then data = "#{body}1[,#{body}2[,...]]}"
         end
         if @long_key.nil? then "#{@short_key} #{data}"
         else "#{@short_key}[#{@long_key}] #{data}"
         end
      end
   end

   class End < KeyValue
      def initialize(key, **rest)
         rest[:value_type] = :END
         rest[:role] = :END
         super(key, '', rest)
         @help = "end of argument list: remainder ignored"
      end
      def arg_look; "-- (ignored)" end
   end

   class Help < KeyValue
      def initialize(short_key, long_key='', **rest)
         super
         @role = @value_type = :HELP
         @help = "print this message to the console and exit." 
      end
   end

   class Version < KeyValue
      attr_reader :message
      def initialize(short_key, long_key='', **rest)
         rest[:value_type] = :VERSION
         rest[:role] = :VERSION
         super short_key, long_key, rest
         @version = rest[:version]
         @date = rest[:date] || nil
         @appname = rest[:appname]
         @help = "print version information to the console"
         msg = ''
         if not @appname.nil? then msg = "#{@appname}: " end
         msg += if @version.nil? then "(no version provided)"
                else  "Version #{@version}"
                end
         if not @date.nil? then msg += ", #{@date}" end
         @message = msg
      end
   end

   class Positional < Parm
      def initialize(short_key, **rest)
         super(short_key, '', rest)
         if @role != :POSITION
            raise "positional option name, #{short_key}, illegal: no leading dashes!" 
         end
         if @debug.member? "all"
            print "leaving constructor for #{@short_key}, #{@attributes}\n"
         end
      end
      def arg_look
         data = @short_key.upcase
         case @howmany
         when :ZERO_OR_ONE then "#{data}?"
         when :ONE then data
         when :ZERO_OR_MORE then "[#{data}1 [,#{data}2[,...]]]"
         when :ONE_OR_MORE then "#{data}1[,#{data}2[,...]]}"
         end
      end
   end



   class Spec 

      attr_accessor :appname, :help_prefix, :help_suffix, :help_info
      attr_reader   :cat_on_dup, :debug, :defaults, :may_group_flags, :may_abbreviate
      attr_reader   :parms_list, :parms_hash, :positionals, :simple_flags, :attributes

      def self.vet_a_path(path, must_exist, must_be_dir)
         exists = File.exists? path
         if must_exist and not exists
            raise ArgumentError.new "'#{path}' does not exist"
         else
            if exists and must_be_dir and not File.directory? path
               raise ArgumentError.new "'#{path}' exists, but does not name a directory"
            end
         end
         path
      end
      def self.vet_a_path_list(paths, must_exist, must_be_dir)
         missing = paths.find_all  { |path| not File.exists? path }
         if must_exist and missing.length > 0
            raise ArgumentError.new "Paths #{missing} do not exist."
         end
         if must_be_dir
            non_dirs = paths.find_all { |path| not File.directory? path }
            if non_dirs.length > 0
               raise ArgumentError.new "#{non_dirs} all exist, but do not name directories"
            end
         end
         paths
      end

      def initialize(appname: nil,
                     helpinfo: {},
                     group_flags: true, 
                     may_abbreviate: true, 
                     cat_on_dup: true, 
                     debug: Set.new,
                     &builder)
         @appname       = appname
         @help_info     = helpinfo
         @parms_list    = [] # position to CmdLineOption map
         @parms_hash    = Hash.new # key to CmdLineOption map
         @simple_flags  = Set.new # to make finding grouped flags easy to unravel
         @attributes    = [] # for use in constructing the OpenStruct
         @defaults      = OpenStruct.new # maps attributes to default values
         @positionals   = []
         @help_prefix   = "USAGE:\n"
         @help_suffix   = '--------'
         # flags limiting what may appear
         @may_group_flags = group_flags
         @may_abbreviate  = may_abbreviate
         @cat_on_dup      = cat_on_dup
         @needs_help      = true
         @ready_to_go     = false
         @version_parm    = nil
         @debug           = Set.new
         if debug.kind_of? String 
            debug.strip!
            if debug.length > 0 # it had better be a string that is a comma-separated list of debug keys
               debug.split('.').each {|dk| @debug.add dk}
            end
         elsif debug.respond_to? :each
            debug.each {|dk| @debug.add dk}
         end
         if not builder.nil?
            builder.call self
         end
      end

      def register_a_parm(parm, **rest)
         if @parms_hash[parm.short_key] != nil
            raise "Duplicate (short) parameter name, '#{parm.short_key}' rejected." 
         elsif parm.long_key != nil && @parms_hash[parm.long_key] != nil
            raise "Duplicate long parameter name, '#{parm.long_key}' rejected."
         end
         parm._set_position @parms_list.length
         @parms_list.push(parm)
         if parm.short_key.length == 2 and parm.value_type == :BOOL
            @simple_flags.add(parm.short_key[1])
         end
         @parms_hash[parm.short_key] = parm
         if not parm.long_key.nil?
            @parms_hash[parm.long_key] = parm 
         end
         if @debug.member? "attrs" 
            puts "Register #{parm.short_key}[#{parm.long_key}]}"
            ap parm.attrnames
            print "\n"
         end
         parm.attrnames.each do |name|  
            @attributes.push name
            @defaults[name] = parm.default
         end
         if parm.role == :POSITION
            @positionals.push parm.position
         end
         parm
      end

      #################### Adding keyword parameters ####################

      def add_csv(short_key, long_key = '', help: '???', optional: false)
         howmany = if optional then :ZERO_OR_ONE else :ONE end
         vetter = ->x {
            if x.kind_of? String then x.split(',') 
            elsif x.kind_of? Array then x
            else raise TypeError.new "Illegal type, #{x.class} for #{short_key}"
            end
            }
         register_a_parm KeyValue.new(short_key, long_key, howmany: howmany,
               default: "", help: help, value_type: :CSV, vet: vetter, debug: @debug)
      end

      def add_flag(short_key, long_key = '', default: true, help: '???', add_negative: true)
         register_a_parm Flag.new(short_key, long_key,
            default: default,  help: help, add_negative: true, debug: @debug
            )
      end

      def add_float(short_key, long_key = '', default: nil, help: '???')
         howmany = if default.nil? then :ONE else :ZERO_OR_ONE end
         register_a_parm KeyValue.new(short_key, long_key, howmany: howmany,
               default: default, help: help, vet: ->(x) {Float(x)}, debug: @debug)
      end

      def add_integer(short_key, long_key = '', default: nil, help: '???')
         howmany = if default.nil? then :ONE else :ZERO_OR_ONE end
         register_a_parm KeyValue.new(short_key, long_key, howmany: howmany,
               default: default, help: help, vet: ->(x) {Integer(x)}, debug: @debug)
      end

      def add_list(short_key, long_key = '', help: '???', optional: false)
         howmany = if optional then :ZERO_OR_MORE else :ONE_OR_MORE end
         register_a_parm KeyValue.new(short_key, long_key, howmany: howmany,
               default: [], help: help, value_type: :LIST, debug: @debug)
      end

      def add_path(short_key, long_key = '', 
                   default: nil, help: '???', 
                   must_exist: false, must_be_dir: false)
         howmany = if default.nil? then :ONE else :ZERO_OR_ONE end
         vet =  ->(x) {Spec.vet_a_path(x, must_exist, must_be_dir)}
         register_a_parm KeyValue.new(short_key, long_key, howmany: howmany,
               default: default, help: help, vet: vet, debug: @debug)
      end

      def add_path_list(short_key, long_key = '', 
                   optional: false, help: '???', 
                   must_exist: false, must_be_dir: false)
         howmany = if optional then :ZERO_OR_MORE else :ONE_OR_MORE end
         vet =  ->(x) {Spec.vet_a_path_list(x, must_exist, must_be_dir)}
         register_a_parm KeyValue.new(short_key, long_key, howmany: howmany,
               default: [], help: help, vet: vet, value_type: :LIST, debug: @debug)
      end

      def add_string(short_key, long_key = '', default: nil, help: '???')
         howmany = if default.nil? then :ONE else :ZERO_OR_ONE end
         register_a_parm KeyValue.new(short_key, long_key, howmany: howmany,
               default: default, help: help, debug: @debug)
      end

      #################### Adding positional parameters ####################
      
      def add_csv_here(key, help: '???', optional: false)
         howmany = if optional then :ZERO_OR_ONE else :ONE end
         vetter = ->(x) {CSV.parse(x)[0]}
         register_a_parm Positional.new(key, howmany: howmany,
               default: "", help: help, value_type: :CSV, vet: vetter)
      end

      def add_float_here(key, default: nil, help:'???')
         howmany = if default.nil? then :ONE else :ZERO_OR_ONE end
         register_a_parm Positional.new(key, howmany: howmany,
               default: default, help: help, vet: ->(x) {Float(x)}, debug: @debug)
      end

      def add_integer_here(key, default: nil, help:'???')
         howmany = if default.nil? then :ONE else :ZERO_OR_ONE end
         register_a_parm Positional.new(key,
               default: default, howmany: howmany, help: help,
               vet: ->(x) {Integer(x)}, debug: @debug)
      end

      def add_list_here(attrname, help:'???', optional: false)
         howmany = if optional then :ZERO_OR_MORE else :ONE_OR_MORE end
         register_a_parm Positional.new(attrname, howmany: howmany,
               default: [], help: help, value_type: :LIST, debug: @debug)
      end

      def add_path_here(attrname, 
                   default: nil, help: '???', 
                   must_exist: false, must_be_dir: false)
         howmany = if default.nil? then :ONE else :ZERO_OR_ONE end
         vet =  ->(x) {Spec.vet_a_path(x, must_exist, must_be_dir)}
         register_a_parm Positional.new(attrname, howmany: howmany,
               default: default, help: help, vet: vet, debug: @debug)
      end

      def add_path_list_here(attrname, 
                   optional: false, help: '???', 
                   must_exist: false, must_be_dir: false)
         howmany = if optional then :ZERO_OR_MORE else :ONE_OR_MORE end
         vet =  ->(x) {Spec.vet_a_path_list(x, must_exist, must_be_dir)}
         register_a_parm Positional.new(attrname, howmany: howmany,
               default: [], help: help, vet: vet, value_type: :LIST, debug: @debug)
      end

      def add_string_here(key, default:nil, help:'???')
         howmany = if default.nil? then :ONE else :ZERO_OR_ONE end
         register_a_parm Positional.new(key,
            howmany: howmany, default: default, help: help, debug: @debug)
      end

      ############ Adding end markers, help, and version info #############
      
      def add_end_marker_here(marker='--')
         register_a_parm End.new(marker, howmany: :NONE, debug: @debug)
      end

      def add_help(short_key="-?", long_key="--help", before: "USAGE:\n", after: '--------')
         register_a_parm Help.new(short_key, long_key,
            howmany: :NONE, help: "Display this message", debug: @debug)
         @help_prefix = before
         @help_suffix = after
         @needs_help = false
      end

      def add_version(short_key="-v", long_key="--version", appname: nil, version: "0.0.0", date: nil)
         if appname.nil? then appname = @appname end
         version_parm = register_a_parm Version.new(short_key, long_key, 
            appname: (appname||@appname), version: version, date: date, howmany: :NONE,
            help: "print version to stdout", debug: @debug)
         @version_parm = version_parm
      end

      ################### Methods required by the parser ####################

      def finalize()
         if @ready_to_go
            return
         end
         if @needs_help
            add_help 
         end
         @attributes.sort!
         dups = []
         previous = nil
         @attributes.each do |an_attr|
            if an_attr ==  previous
               dups.push(an_attr)
            else
               previous = an_attr
            end
         end
         if dups.length > 0
            raise "Duplicate attribute names, #{dups}, for command line options."
         end
         @positionals.push(@parms_list.length)
         @attributes.freeze
         @defaults.freeze
         @parms_list.freeze
         @parms_hash.freeze
         @positionals.freeze
         @ready_to_go = true
      end

      def [](key_or_int)
         if key_or_int.is_a? Fixnum then @parms_list[key_or_int] else @parms_hash[key_or_int] end
      end

      def help_msg
         as_list = @parms_list.map { |parm| "#{parm.arg_look}" }
         parameters = as_list.join(" ")
         cmdline = "  #{@appname} #{parameters}\n\n"
         help_list =  @parms_list.map { |parm| "\n#{parm.help_msg}" }.join('')
         prefix = if @version_parm.nil?  then @help_prefix
                  else "#{@version_parm.message}\n\n#{@help_prefix}"
                  end
         "#{prefix}\n#{cmdline}PARAMETERS:\n#{help_list}\n#{@help_suffix}\n\n"
      end

      def version_msg(parm); parm.version_msg end

      def determines_key(arg)
         arg = arg.split("=")[0] # trim off any trailing value
         arglength = arg.length
         if arglength == 0
            return nil
         end
         if arglength == 0 or arg[0] != '-'
            return nil
         end
         first = if arg[1] == '-' then 2 else 1 end
         last = arglength - 1
         if first == 2 and last == 2
            return @parms_hash['--']
         end
         candidates = []
         @parms_hash.each do |key, parm|
            if key.start_with? arg
               if key.length == arglength then return key
               else candidates.push parm
               end
            end
         end
         if candidates.length == 1 then candidates[0] else nil end
      end
   end
   class Parser 
      attr_reader :args, :debug
      KEY_ARG_REG_EXP  = /^((-{1,2})?([^-=0-9][^=]*)?)(=(.*))?$/
      def parse_an_arg(arg)
         matched = KEY_ARG_REG_EXP.match(arg)
         if not matched
            [nil, nil, nil, nil]
         else
            whole_key, dashes, key, ignore, value = matched.captures
            [whole_key, dashes, key, value]
         end
      end

      def initialize(spec, argv = ARGV, debug: nil)
         @spec = spec
         @spec.finalize
         @debug = Set.new
         if not debug.nil?
            if debug.is_a? Array or debug.is_a? Set 
               debug.each {|dk| @debug.add dk}
            else # it had better be a string that is a comma-separated list of debug keys
               CSV.parse(debug)[0].each do|dk| 
                  @debug.add dk
               end
            end
            if @debug.length > 0
               print("Final debug flags: ")
               ap(@debug)
            end
         end
         if @debug.member? "final"
            print "Final parms list:\n-------\n"
            ap @spec.parms_list
            print "\n------\n"
         end
         @args = OpenStruct.new(@spec.defaults)
         @positionals_seen = 0
         @last_positional = -1
         @next_positional = @spec.positionals[0]
         @done = false
         @parms_seen_set = Set.new() # so we can quickly find duplicate keys
         while argv.length > 0 and not @done
            arg = argv.shift
            if @debug.member? "parser"
               print "next arg is '#{arg}' and key? arg is #{key? arg}\n"
            end
            if not key? arg # it is a value, not a key
               handle_positional(arg, argv)
            elsif not (
               handle_keyword(arg, argv) || handle_possible_flags(arg, argv)|| handle_abbreviation(arg, argv)
               )
               raise "Unexpected command line key, '#{arg}'"
            end
         end
         @args.freeze
         mia = []
         @spec.parms_list.each do |parm|
            if not @parms_seen_set.member? parm.short_key
               if parm.howmany == :ONE || parm.howmany == :ONE_OR_MORE
                  mia.push(parm.printname)
               end
            end
         end
         if mia.length > 0
            raise "required parameters missing: "+mia.join(", ")+"."
         end
      end

      private
      def key? a_string 
         # return true if a_string is a keyword plus (possibly) a value
         if a_string.length < 2
            false
         else # parse to avoid having to check for a negative integer using begin/rescue
            whole_key, dashes, key, value = parse_an_arg(a_string)
            dashes == '-' || dashes == '--'
         end
      end

      def check_parm_position(parm)
         # the parameter's position must lie between the last and the next required positional
         # parameter.  Otherwise, that required parameter's value is missing!
         if parm.position < @last_positional
            last_name = @spec[@last_positional].short_key
            raise "#{parm.short_key} cannot occur after #{last_name}"
         else
            while parm.position > @next_positional
               next_pparm = @spec[@next_positional]
               if next_pparm.role == :ONE or next_pparm.role == :ONE_OR_MORE
                  psn = parm.short_key
                  npp = next_pparm.short_key
                  raise "missing value for required positional parameter #{mpp}: #{psn} seen first"
               else
                  @last_positional = @next_positional
                  @positionals_seen += 1
                  @next_positional = @spec.positionals[@positionals_seen]
               end
            end
         end
      end

      def handle_abbreviation(arg, argv)
         whole_key, dashes, key, value = parse_an_arg arg
         matches = Set.new
         @spec.parms_list.each do |parm|
            if parm.short_key.start_with?(whole_key) then matches.add(parm) end
            if not parm.long_key.nil? and parm.long_key.start_with?(whole_key)
               matches.add(parm)
            end
         end
         if matches.length != 1
            return false
         else
            parm = matches.delete()
            wholearg = parm.short_key + (if value.nil? then "" else "="+value end)
            return handle_keyword(wholearg, argv)
         end
      end

      def handle_keyword(arg, argv)
         whole_key, dashes, key, value = parse_an_arg arg
         parm = @spec[whole_key]
         if @debug.member? "parser"
            print "whole key #{whole_key} and parm is\n  " 
            ap parm
         end
         if parm.nil?
            return false
         elsif parm.role == :HELP
            print @spec.help_msg
            exit 101
         elsif parm.role == :VERSION
            print(@spec.version_msg(parm), "\n")
            return true
         elsif parm.role == :END
            @rest = argv
            @done = true
            return true
         end
         check_parm_position(parm) # fails only by raising an error

         case parm.howmany
         when :ONE, :ZERO_OR_ONE
            if value.nil?
               if not key? argv[0]
                  value = argv.shift
               elsif parm.howmany == :ZERO_OR_ONE
                  value = parm.default
               else
                  raise "The parameter #{arg} requires a value, but none was supplied ."
               end
            end
            if parm.value_type == :CSV
               expanded = if value.kind_of? String then value.split ',' else value end
               if @parms_seen_set.find_index(key) == nil then value = expanded
               elsif @spec.cat_on_dup then value = @args[parm.short_key] + expanded
               elsif expanded != @args[parm.short_key]
                  raise "Duplicate key '#{key} for comma-separated values"
               end
            elsif @parms_seen_set.find_index(key) != nil and value != @args[parm.short_key]
               raise "Duplicate key '#{key}"
            end
         when :ZERO_OR_MORE, :ONE_OR_MORE
            if not value.nil? # saw key=stuff as the argument, so stuff is a CSV
               expanded = if value.kind_of String then value.split ',' else value end 
            else 
               expanded = [] 
               while argv.length > 0 and not key? argv[0]
                  expanded.push(argv.shift)
               end
               if expanded.length == 0 # if it appears in the command line, it must have a value
                  raise "#{key} requires at least one value, but none were supplied."
               end
            end
            if @debug.member? "parser"
               ap @parms_seen_set
               print "#{key} is the next key? #{@parms_seen_set.member? key}\n"
            end
            if not @parms_seen_set.member? key then value = expanded
            elsif @spec.cat_on_dup then value = @args[parm.short_key] + expanded
            elsif expanded != @args[parm.short_key]
               raise "Duplicate key '#{key}' with differing value lists"
            end
         when :NONE
            value = true # it must be a boolean
         end
         value = parm._call_vet(value)
         @args[parm.short_key] = value
         if parm.long_key then @args[parm.long_key] = value end
         parm.attrnames.each { |name|  @args[name] = value }
         @parms_seen_set.add(parm.short_key)
         if parm.long_key != nil then @parms_seen_set.add(parm.long_key) end
         true
      end

      def handle_positional(arg, argv)
         @last_positional = @next_positional
         if @next_positional == @spec.parms_list.length
            raise "Unexpected value '#{arg}' after the last positional parameter."
         end
         @positionals_seen += 1
         @next_positional = @spec.positionals[@positionals_seen]
         parm = @spec.parms_list[@last_positional]
         if debug.member? "parser"
            print "The current positional is "
            ap(parm)
            print "and the next is #{@next_positional}\n"
         end
         @parms_seen_set.add(parm.short_key)
         @parms_seen_set.add(parm.long_key) if not parm.long_key.nil?
         if parm.howmany == :ONE_OR_MORE or parm.howmany == :ZERO_OR_MORE 
            value = [arg]
            while argv.length > 0 and not key? argv[0]
               value.push(argv.shift)
            end
         else
            value = arg
         end
         value = parm._call_vet(value)
         if @debug.member? "all"
            print"Assign #{value} to #{parm.attrnames}\n"
         end
         @args[parm.attrnames[0]] = value
         if parm.position == @spec.parms_list.length-1
            @done = true
         end
         true
      end

      def handle_possible_flags(arg, argv)
         whole_key, dashes, key, ignore = parse_an_arg arg
         negator, ignore, flaglist = LEADING_NO_REG_EXP.match(key).captures
         # no-v always means "v is off", and "-v" always means "v is on": defaults are irrelevant
         boolean_to_use = negator.nil?
         flags = flaglist.split('')
         flags.each do |flag|
            if not @spec.simple_flags.member?(flag) then return false end
         end
         flags.each do |flag|
            parm = @spec.parms_hash["-"+flag]
            @args[parm.short_key] = boolean_to_use
            @args[parm.long_key]  = boolean_to_use if not parm.long_key.nil?
            parm.attrnames.each {|name| @args[name] = boolean_to_use}
            if @debug.member? "all"
               print"Assign #{boolean_to_use} to #{parm.attrnames}\n"
            end
         end
         true
      end

      def [](key_or_int)
         if @spec.attributes.member? key_or_int
            args[key_or_int]
         else
            parm = @spec[key_or_int]
            if parm.nil? then nil? else args[parm.attrnames[0]] end
         end
      end
   end
end

