
require "callerid"
require "fileutils"
require "htmlentities"
require 'sysutils'
require "wildcardlookup"

class DbgMgr
   prohibit_subclassing!

private
   def self.raise_NoCopyError(method_name)
      msg = "DbgMgr is intended for use as a singleton: '#{method_name}' is not allowed!"
      raise NotImplementedError, msg
   end
public


   def self.new(*args) 
      raise NotImplementedError, 'DbgMgr has no instances!'
   end

   def self.clone(freeze: true)
      raise_NoCopyError("clone")
   end

   def self.dup()
      raise_NoCopyError("dup")
   end

   class << self
      attr_reader :esc, # if true, escape HTML entities in the output (esc is false by default)
         :path,      # if non-nil, the file to which to write the buffer
         :styles,    # user-added CSS definitions
         :count,     # a cumulative count of messages written--not the buffer.length
         :group_by   # how to group the messages before sorting by time of arrival.
      private
      attr_accessor :active,  # the "set" of live keys
         :important, # a subset of the active flags that deserved to be seen first
         :buffer     # when buffered debugging is done, the list of messages
      attr_writer :path, # if non-nil, the file to which to write the buffer
         :styles,    
         :count      
   end
   @active = WildCardLookup.new
   @important = WildCardLookup.new

   @buffer = []
   @count = 0
   @group_by = :time

   @path = nil
   @styles = ''
   @esc = false
   MESSAGE_GROUPS = Set.new %i[caller key match priority time] # for grouping buffered message sets

   def self.add_patterns(*args)
      args.each do |arg|
         if arg.kind_of? String
            raw_patterns = arg.split ','
            raw_patterns.each do |pattern|
               if pattern[0] == '+'
                  real_pattern = pattern[1 .. -1]
                  @active.add_pattern real_pattern
                  @important.add_pattern real_pattern
               elsif pattern[0] == '@'
                  group = pattern[1 .. -1]
                  found = MESSAGE_GROUPS.find { |name| name.to_s.begin_with? group}
                  if found.nil?
                     self.warn("DbgMgr.add_patterns", "unknown message group: '#{group}'")
                     @active.add_pattern pattern
                  else
                     @group_by = found
                  end
               else
                  @active.add_pattern pattern
               end
            end # do |pattern|
         elsif arg.kind_of? Array
            add_patterns *arg
         else 
            raise ArgumentError.new "Unexpected argument type, #{arg}"
         end
      end
      nil 
   end

   def self.remove_patterns(*args)
      args.each do |arg|
         if arg.is_a? String
            patterns = arg.split(',')
            @active.remove_patterns patterns
            @important.remove_patterns patterns
         elsif arg.is_a? Array 
            remove_patterns *arg
         else
            raise ArgumentError.new "Unexpected argument type, #{arg}"
         end
      end
   end


   def self.active?(*args)
      args.each do |arg|
         if arg.is_a? String 
            all = arg.split(',')
            return @active.any_matched? *all
         elsif arg.is_a? Array and active? *arg then return true
         else raise ArgumentError.new "Unexpected argument type, #{arg}"
         end
      end
      false
   end

   def self.all_active?(*args)
      args.each do |arg|
         if arg.is_a? String and not @active.all_matched? arg.split(',') then return false
         elsif arg.is_a? Array and not all_active? *arg then return false
         else raise ArgumentError.new "Unexpected argument type, #{arg}"
         end
      end
      true
   end

   def self.open(path='.', asis: false, esc: false)
      abspath = File.join File.expand_path path
      if not asis and not abspath.end_with? "#{File::SEPARATOR}log"
         abspath = File.join abspath, "#{File::SEPARATOR}log"
      end
      if @path == abspath then return self # caller knows last file is the only one! 
      elsif not @path.nil?
         msg = "Already logging to #{@path}, cannot use #{abspath}"
         STDERR.puts msg
         warn msg
         self
      end
      File.assure_directory(abspath)
      @path = File.join abspath, "dbg#{Time.now.strftime '%y%m%d_%H%M%S'}.html"
      File.open(@path, mode: 'w') do |stream|
         stream.puts "<!DOCTYPE html>\n<html>\n<head>"
         stream.puts "   <meta charset=\"utf-8\">"
         stream.puts "   <meta name=\"generator\" content=\"rubymd\">"
         stream.puts "   <style type=\"text/css\">"
         stream.puts DbgMessage::STYLES
         stream.puts ADMIN_STYLES
         stream.puts " #{@styles}\n    </style>\n</head>\n<body>\n<code>" 
      end
      @esc = esc
      @styles = ''
      self
   end
   def self.add_important_patterns(*args)
      args.each do |arg|
         if arg.is_a? String
            add_patterns arg
            @important.add_patterns arg.split(',')
         elsif arg.is_a? Array 
            add_important_patterns *arg
         else
            raise ArgumentError.new "Unexpected argument type: #{arg.class}"
         end
      end
   end

   def self.not_important(*args)
      args.each do |arg|
         if arg.is_a? String
            @important.remove_patterns arg.split(',')
         elsif arg.is_a? Array 
            not_important *arg
         else
            raise ArgumentError.new "Unexpected argument type: #{arg.class}"
         end
      end
   end
   def self.esc= yes_or_no
      @esc = yes_or_no.to_b
   end
 
   @encoder = HTMLEntities.new 
   def self.html_encode text
      @encoder.encode text, :named
   end

   def self.put(key, text, 
      esc: @esc, my_caller: CallerId.my_caller, style: nil
   )
      if key != "dbgmgr" and @active.matched?("dbgmgr")
         tgt = if @path.nil? then "STDOUT" else @path end
         self.put "dbgmgr", "put #{key}? #{@active.matched? key}, target #{tgt}"
      end
      if not @active.matched? key
         nil
      elsif @path.nil?
         puts text
         text
      else
         matcher = @active.weakest_pattern key
         if esc then text = html_encode text end
         @count += 1
         msg = if @important.matched? key
                  DbgMessage.priority(
                     key: key, match: matcher, index: @count, 
                     caller: my_caller, body: text, style: style
                  )
               else
                  DbgMessage.ordinary(
                     key: key, match: matcher, index: @count,
                     caller: my_caller, body: text, style: style
                  )
               end
         @buffer.push msg
         msg
      end
   end
   def self.err(error, esc: @esc, my_caller: CallerId.my_caller, now: false, bail_out: true)
      if error.respond_to? :backtrace
         backtrace  = (error.backtrace or []).join('\n')
      else
         backtrace = ''
      end
      class_name = if error.kind_of? Exception then "#{error.class}: " else "" end
      if @path.nil?
         STDERR.puts "#{class_name}#{error}"
         if backtrace.length > 0
            STDERR.puts backtrace
         end
      else
         @count += 1
         text = class_name + error.to_s
         if esc then text = html_encode text end
         if backtrace.length > 0
            text += "\nTraceback:\n#{html_encode backtrace}"
         end
         final_text = "<pre>#{text}</pre>"
         msg = DbgMessage.err index: @count, caller: my_caller, body: final_text
         @buffer.push msg
         if now 
            if now.is_a? String then flush after: now
            else DbgMgr.flush
            end
         end
      end
      if bail_out
         if class_name.length > 0
            raise error
         else
            raise RuntimeError(error.to_s)
         end
      else
         msg
      end
   end
   def self.pre(key, text, esc: @esc, my_caller: CallerId.my_caller, style: nil)
      # If the caller wants us to escape, we have to do it here so that our "<pre>"  and
      # "</pre>" do not get escaped later.
      if active? key
         if (@path != nil) and esc then text = html_encode text end
         put key, "<pre>#{text}</pre>", esc: false, my_caller: my_caller
      end
   end  
   def self.warn(warning, esc: nil, my_caller: CallerId.my_caller, now: false, bail_out: false)
      if warning.respond_to? :backtrace
         backtrace  = (warning.backtrace or []).join('\n')
      else
         backtrace = ''
      end
      if @path.nil?
         STDERR.puts warning
         if backtrace.length > 0
            STDERR.puts backtrace
         end
         warning
      else
         @count += 1
         warning = if esc then html_encode warning.to_s else warning.to_s end
         if backtrace.length > 0
            warning += "\nTraceback:\n#{html_encode backtrace}"
         end
         msg = DbgMessage.warn index: @count, caller: my_caller, body: warning
         @buffer.push msg
         if now
            if now.is_a? String then flush after: now
            else now DbgMgr.flush
            end
         end
      end
      if bail_out
         if class_name.length > 0
            raise error
         else
            raise RuntimeError(error.to_s)
         end
      else
         msg
      end
   end
   def self.group_by=(field)
      as_symbol = field.to_sym
      if MESSAGE_GROUPS.member? as_symbol
         @group_by = as_symbol
      else
         raise ArgumentError.new "Unrecognized message group, '#{field}'" 
      end
   end


   ADMIN_STYLES = %[
   .fl { color: #000000; }
   .ref { color: #000000; font-style: oblique}
   ]

   def self.add_style(css_defns)
      if css_defns[-1] != "\n" then css_defns += "\n" end
      @styles += css_defns
   end


   def self.flush(before: "", after: "", asis: false)
      if @buffer.length + @styles.length + before.length + after.length == 0
         return nil  # if there is nothing to do, do NOT open the file at all
      end
      File.open(@path, mode: 'a') do |stream|
         if @styles.length > 0
            stream.puts "<style>"
            stream.puts @styles
            stream.puts "</style>"
            @styles = ''
         end
         if @buffer.length > 0
            stream.puts "<p>Log flushed, #{Time.now}: #{@buffer.length} entries</p>\n"
         end
         if before.length > 0            
            stream.puts( if asis then before else "<p class=\"fl\">#{before}</p>" end )
         end
         if @group_by != :time then @buffer.sort! end
         stream.puts "<table>"
         @buffer.each { |msg| stream.puts msg.to_html(@count) }
         stream.puts "</table>"
         if after.length > 0
            stream.puts( if asis then after else "<p class=\"fl\">#{after}</p>" end )
         end
         stream.puts "<hr>"
      end
      @buffer = []
      nil
   end


   def self.close()
      if @path != nil
         after = "<p>Log ended, #{Time.now}: #{@count} entries in all.</p>\n</code>\n</body>"
         flush(after: after)
         @path = nil
      end
   end

   def self.finalize(exception, esc: self.esc)
      begin
         err "finalize", exception, esc
         if not @path.nil? 
            close
         end
      rescue Exception => exc 
         @path = nil
         STDERR.puts "Finalizing the log failed.\n\n#{exc}"
      end
      nil
   end        
end


class DbgMessage
   include Comparable
   attr_reader :key, :match, :index, :caller
   attr_accessor :body, :priority, :data_class
   #HTML_ESCAPER = HTMLEntities.new 
   PRIORITY_LEVELS = {
      :ERROR => 4, :WARNING => 3, :PRIORITY => 2, :ORDINARY => 1, :UNKNOWN => 0
   }
   STYLE_CLASSES = {
      :ERROR => 'er', :WARNING => 'wn', :PRIORITY => 'hp',
      :ORDINARY => 'lp', :UNKNOWN => 'un'
   }
   STYLES = %[
      .er {
         color: #ff0000; font-weight: bold; background-color: #F0D0D0;
         border: 1px solid red; margin-left: 1em;
      }
      .hp {
         color: #007020; font-weight: bold; background-color: #E1FDC8;
         border: 1px solid #007020; margin-left: 1em;
      } 
      .lp {color: #000000; background-color: #DDDDDD;
         border: 1px solid black; margin-left: 1em;
      } 
      .wn {
         color: #0000ff; font-weight: bold; background-color: #C8E5F8;
         border: 1px solid blue; margin-left: 1em;
      } 
      .un {
         color: #AEAF85; font-weight: bold; background-color: #94A2B7;
         border: 1px solid ccd847; margin-left: 1em;
      } 
   ]
   
   def self.err(index: nil, caller: nil, body: nil, style: nil)
      msg = self.new index: index, caller: caller, body: body
      msg.priority = PRIORITY_LEVELS[:ERROR]
      if style.nil? then msg.data_class = STYLE_CLASSES[:ERROR]
      else  msg.data_class = style
      end
      msg
   end
   def self.warn(index: nil, caller: nil, body: nil, style: nil)
      msg = self.new index: index, caller: caller, body: body
      msg.priority = PRIORITY_LEVELS[:WARNING]
      if style.nil? then msg.data_class = STYLE_CLASSES[:WARNING]
      else  msg.data_class = style
      end
      msg
   end
   private 
   def self.key_check(key)
      if not key.kind_of? String
         raise TypeError.new "DbgMgr key is a #{key.class}, not a String as required."
      elsif key.length == 0
         raise ArgumentError "Empty string is not an allowable DbgMgr key."
      end
   end
   public
   def self.priority(key: nil, match: nil, index: nil, caller: nil, body: nil, style: nil)
      key_check key
      msg = self.new key: key, match: match, index: index, caller: caller, body: body
      msg.priority = PRIORITY_LEVELS[:PRIORITY]
      if style.nil? then msg.data_class = STYLE_CLASSES[:PRIORITY]
      else  msg.data_class = style
      end
      msg
   end
   def self.ordinary(key: nil, match: nil, index: nil, caller: nil, body: nil, style: nil)
      key_check key
      msg = self.new key: key, match: match, index: index, caller: caller, body: body
      msg.priority = PRIORITY_LEVELS[:ORDINARY]
      if style.nil? then msg.data_class = STYLE_CLASSES[:ORDINARY]
      else  msg.data_class = style
      end
      msg
   end

   def initialize(key: nil, match: nil, index: nil, caller: '', body: '')
      @key   = key or ''
      @match = if match then match else key end
      @index = index
      @caller =  DbgMgr.html_encode caller
      @body = body
      @priority = PRIORITY_LEVELS[:UNKNOWN]
      @data_class = STYLE_CLASSES[:UNKNOWN]
   end
   def ==(other)
      @index == other.index
   end
   def !=(other)
      @index != other.index
   end
   def <=>(other)
      grouping = DbgMgr.group_by
      if grouping == :time then return @index <=> other.index # most common call is this
      elsif grouping == :caller # within caller by time, not priority
         if @caller < other.caller then return -1
         elsif other.caller < @caller then return 1
         end
      else # group by priority and, if requested, group within that by key or match
         if @priority > other.priority then return -1 
         elsif other.priority > @priority then return 1
         elsif @key.nil? and other.key.nil?
            return @index <=> other.index # same priority, only time of entry counts
         elsif @key.nil? ^ other.key.nil? # ie. one, but not both are nil... never happens
            raise "Invalid priority for #{self} relative to #{other}"
         end
         # we get here if both have the same priority and both have keys,
         # and thus also have non-nil "match" attributes
         if grouping == :key 
            if @key < other.key then return -1
            elsif other.key < @key then return 1
            end
         elsif grouping == :match
            if @match < other.match then return -1
            elsif other.match < @match then return 1
            end
         end
      end
      @index <=> other.index
   end      
   def to_html(largest_index)
      index_width = 1 + Integer(Math.log10 largest_index)
      formatted_index = index.to_s 
      while formatted_index.length < index_width
         formatted_index = "&nbsp;"+formatted_index
      end
      key = if @key.nil? then '' else "[#{@key}]" end
      source_cell  = "<td class=\"ref\">#{formatted_index}: #{@caller}#{key}</td>\n"
      data_cell = "<td class=\"#{@data_class}\">#{body}</td>"
      "<tr>#{source_cell}#{data_cell}</tr>"
   end
end
