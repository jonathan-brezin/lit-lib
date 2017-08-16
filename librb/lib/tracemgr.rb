
require "awesome_print"
require "dbg"
require "sysutils"
require "wrapping"

class TraceManagement
   class TraceImpl
      attr_accessor :dbg_key
      attr_reader   :registry

      def initialize dbg_key: 'trc'
         @dbg_key = dbg_key
         DbgMgr.add_patterns dbg_key
         @registry = {}  # maps context+variable names to the info needed to trace
      end
   end
   @mgr = TraceImpl.new
   class << self
      attr_reader :mgr
   end
end

TraceMgr = TraceManagement.mgr

class TraceManagement
   class TraceImpl
      private
      def _trace(context, variable, own, mode, guard_block)
         info = find_key context, variable, own
         if info.nil? 
            info = TraceItem.new context, variable, own, guard_block
            key = make_key context, variable, own
            @registry[key] = info
            admin_msg "trace for #{key} registered"
         else
            admin_warn "trace(#{key}) already active."
         end
         # registering starts tracing by default, so if we don't want that, we need to pause.
         off = if not mode.include? 'r' then 'r' else '' end
         if not mode.include? 'w' then off += 'w' end
         _pause(context, variable, own, off) if off.length > 0    
      end

      def make_key(context, variable, own)
         variable = variable.to_s.gsub('@', '')
         key = if own then "#{context}.#{variable}"
               else "#{context}@#{variable}"
               end
      end

      def find_key(context, variable, own, show_missing: false)
         key = make_key context, variable, own
         if @registry[key].nil?
            altkey = make_key context, variable, (not own)
            if show_missing
               admin_err "Could not find #{key}.  Did you mean #{altkey}"
            end
            nil
         else
            @registry[key]
         end
      end

      def _replace_the_guard(context, variable, own, &guard_block)
         info = find_key context, variable, own, show_missing: true
         if not info.nil?
            _end(context, variable, own)
            trace info.context, info.variable, info.own, info.current_mode, guard_block
         else
            admin_err "'#{context}, #{variable}' is not a registered trace pair"
         end
      end

      public 
      def trace_instance(context, variable, mode='rw', &guard_block)
         _trace context, variable, false, mode, guard_block
      end

      def trace_me(context, variable, mode='rw', &guard_block)
         _trace context, variable, true, mode, guard_block
      end

      def replace_instance_guard(context, variable, &guard_block)
         _replace_the_guard context, variable, false, guard_block
      end

      def replace_my_guard(context, variable, &guard_block)
         _replace_the_guard context, variable, true, guard_block
      end

      def replace_the_guard(context, variable, &guard_block)
         info = find_key context, variable, true
         altinfo = find_key context, variable, false
         if info.nil?
            if altinfo.nil?
               admin_err "No TraceMgr entry for #{context}, #{variable}"
            else
               _replace_the_guard context, variable, false, guard_block
            end
         elsif altinfo.nil?
            _replace_the_guard context, variable, true, guard_block
         else
            admin_err "Ambiguous call for #{context},#{variable}: use _instance and _my calls"
         end
      end

      private
      def _end(context, variable, own, should_flush = false)
         info = find_key context, variable, own
         unless info.nil?
            _pause context, variable, own, "rw", false 
            @registry.delete make_key context, variable, own
            admin_msg "ended tracing for #{make_key(context, variable, own)}", should_flush
         end
      end
         
      def _pause(context, variable, own, mode, should_flush = false)
         info = find_key context, variable, own
         if info.nil?
            key = make_key context, variable, own
            admin_warn "#{key} is no longer registered with the TraceMgr"
         else
            paused = _swap mode, info, :pause
            if paused.length > 0
               key = make_key(context, variable, own)
               admin_msg "paused tracing '#{paused}' for #{key}", should_flush
            end
         end
      end

      def _start(context, variable, own, mode, should_flush=false)
         info = find_key context, variable, own
         if info.nil?
            admin_warn "#{make_key(context, variable, own)} is no longer registered with the TraceMgr"
         else
            started = _swap mode, info, :start
            if started.length > 0
               key = make_key context, variable, own
               admin_msg "started tracing  '#{started}' for #{key} now", should_flush
            end
         end
      end

      public
      def end_instance(context, variable, should_flush = false)
         _end context, variable, false, should_flush
      end
         
      def end_me(context, variable, should_flush = false)
         _end context, variable, true, should_flush
      end
         
      def pause_instance(context, variable, mode="rw", should_flush = false)
         _pause context, variable, false, mode, should_flush
      end
         
      def pause_me(context, variable, mode="rw", should_flush = false)
         _pause context, variable, true, mode, should_flush
      end

      def start_instance(context, variable, mode="rw", should_flush=false)
         _start context, variable, false, mode, should_flush
      end

      def start_me(context, variable, mode="rw", should_flush=false)
         _start context, variable, true, mode, should_flush
      end


      def admin_msg(message, should_flush = false)
         DbgMgr.put @dbg_key, message, esc: true, my_caller: "TraceMgr"
         if should_flush
            TraceMgr.flush
         end
      end

      def admin_err(message, should_flush = false)
         DbgMgr.err message, esc: true, my_caller: "TraceMgr"
         if should_flush 
            TraceMgr.flush before: "Trace Manager flush requested due to an error"
         end
      end

      def admin_warn(message, should_flush = false)
         DbgMgr.warn message, esc: true, my_caller: "TraceMgr"
         if should_flush
            TraceMgr.flush
         end
      end

      def buffer(path='.', asis: false, esc: false)
         DbgMgr.open(path=path, asis: asis, esc: esc)
         self
      end

      def flush(before: 'Trace Manager flush request', after: "")
         DbgMgr.flush before: before, after: after
      end

      private
      def _swap(mode, info, action)
         msg = "swap #{info.reader}, mode=#{mode}, action: #{action}, state=#{info.active_reads}/#{info.active_writes}"
         admin_msg msg
         swapped = ''
         if mode.include? 'r'
            if info.r_info.nil?
               admin_warn "Cannot trace #{info.variable} reads: no method defined", true
            elsif ((action == :start and not info.active_reads) or 
               (action == :pause and info.active_reads))
               swapper = if info.own then :turn_on_my else :turn_on end
               which = if info.active_reads then :plain else :wrapped end
               info.context.send swapper, which, info.r_info         
               info.active_reads ^= true
               swapped = 'r'
            end
         end
         if mode.include? 'w'
            if info.w_info.nil?
               admin_warn "Cannot trace #{info.variable} writes: no method defined", true
            elsif ((action == :start and not info.active_writes) or 
               (action == :pause and info.active_writes))
               swapper = if info.own then :turn_on_my else :turn_on end
               which = if info.active_writes then :plain else :wrapped end
               info.context.send swapper, which, info.w_info                               
               info.active_writes ^= true
               swapped += 'w'
            end
         end
         swapped
      end
   end

   protected
   class TraceItem
      attr_reader :context,  # the class or object id to which the identifier belongs
         :variable,          # the symbol (including leading @'s) naming the variable
         :reader,            # var stripped of '@'s
         :writer,            # var stripped of '@'s, followed by '='
         :own,               # true means only the context's method is wrapped 
         :r_info,            # template returned by the wrapping call for the getter
         :w_info             # template returned by the wrapping call for the setter
      attr_accessor :active_reads, # boolean--true if we are currently tracing reads
         :active_writes            # boolean--true if we are currently tracing writes

      def initialize(context, variable, own, guard_block)
         @context = context
         @variable = variable.to_s
         @own = own
         @reader = @variable.gsub('@', '').to_sym
         @writer = (@reader.to_s + "=").to_sym
         @r_info = read_action(guard_block)
         @w_info = write_action(guard_block)
         @active_reads = true
         @active_writes = true # see start and pause methods for TraceImpl
      end

      # the actions are set after the mode has been established
      def read_action(guard_block)
         if not @own
            return nil unless @context.instance_methods.include? @reader
            called = @context.instance_method @reader
            method_to_call = :wrap_instance_method
         else
            return nil unless @context.methods.include? @reader
            called = @context.method @reader
            method_to_call = :wrap_my_method
         end
         variable = @variable
         if guard_block.nil?
            @context.send method_to_call, @reader do |org, args, block_in, zelf|
               value = org.call
               message = "#{zelf}.#{variable} ---> #{value}"
               DbgMgr.put TraceMgr.dbg_key, message, esc: true, my_caller: "TraceMgr"
               value
            end
         else
            @context.send method_to_call, @reader  do |org, args, block_in, zelf|
               value = org.call
               if guard_block.call zelf, variable, value, nil
                  message = "#{zelf}.#{variable} ---> #{value}"
                  DbgMgr.put TraceMgr.dbg_key, message, esc: true, my_caller: "TraceMgr"
               end
               value
            end
         end
      end

      def write_action(guard_block)
         if not @own
            return nil unless @context.instance_methods.include? @writer
            called = @context.instance_method @writer
            method_to_call = :wrap_instance_method
         else
            return nil unless @context.methods.include? @writer
            called = @context.method @writer
            method_to_call = :wrap_my_method
         end
         variable = @variable
         if guard_block.nil?
            @context.send method_to_call, @writer do |org, args, block_in, zelf|
               value = args[0]
               message = "#{zelf}.#{variable} <--- #{value}"
               DbgMgr.put TraceMgr.dbg_key, message, esc: true, my_caller: "TraceMgr"
               org.call value
            end
         else
            getter = @r_info.source_alias
            @context.send method_to_call, @writer  do |org, args, block_in, zelf|
               new_value = args[0]
               old_value = zelf.send getter
               if guard_block.call zelf, variable, old_value, new_value
                  message = "#{zelf}.#{variable} <--- #{new_value}"
                  DbgMgr.put TraceMgr.dbg_key, message, esc: true, my_caller: "TraceMgr"
               end
               org.call new_value
            end
         end
      end

      def to_s; "TraceItem[#{@context}#{if @own then '.' else '#' end}#{@variable}]" end
   end
end
