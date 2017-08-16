
require "dbg"
require "sysutils"

module DbgClient


   def self.key(klass)
      @@debug_configuration[klass][:key]
   end
   def self.set_key(klass, a_string)
      @@debug_configuration[klass][:key] = a_string
   end

   def self.pattern(klass)
      @@debug_configuration[klass][:pattern]
   end
   def self.set_pattern(klass, a_string)
      @@debug_configuration[klass][:pattern] = a_string
   end

   def self.active?(klass)
      @@debug_configuration[klass][:active]
   end
   def self.set_active(klass, boolean)
      @@debug_configuration[klass][:active] = boolean.to_b
   end

   def self.class_active?(klass)
      @@debug_configuration[klass][:class_active]
   end
   def self.set_class_active(klass, boolean)
      @@debug_configuration[klass][:class_active] = boolean.to_b
   end

   def self.show_classes()
      all = []
      @@debug_configuration.each do |key, value|
         all.push  "#{key.name}(#{value[:key]}, #{value[:pattern]}, #{value[:active]})"
      end
      all.join("\n")
   end


   def self.configure(klass, key, pattern=key)
      @@debug_configuration ||= {}
      @@debug_configuration[klass] = {
         :class => klass, :key => key, :pattern => pattern,
         :active => false, :class_active => false
      }
      # to be continued below with class method definitions...

      def klass.start_debugging(*patterns)
         DbgClient::set_active self, true
         DbgClient::set_class_active self, true
         if patterns.length == 0
            DbgMgr.add_patterns DbgClient::pattern(self)
         else
            DbgMgr.add_patterns patterns
         end
      end
      
      def klass.pause_debugging(*dead_patterns)
         DbgClient::set_active self, false
         DbgMgr.remove_patterns *dead_patterns
      end

      def klass.stop_debugging(msg: nil)
         if msg 
            if msg.is_a? String then DbgMgr.flush after: msg end
         end
         DbgClient::set_active self, false
         DbgMgr.close
      end
   
      def klass.write_dbg_msg(msg, key: nil, pre: false,
            now: false, src: CallerId.my_caller, style: nil, esc: nil
         )
         key ||= DbgClient::key self
         if not ((DbgClient.active? self) and (DbgMgr.active? key))
            return false
         end
         esc ||= DbgMgr.esc
         if pre
            DbgMgr.pre key, msg, my_caller: src, style: style, esc: esc
         else
            DbgMgr.put key, msg, my_caller: src, style: style, esc: esc
         end
         if now 
            if now.is_a? String then DbgMgr.flush after: now
            else DbgMgr.flush
            end
         end
         true
      end

      def klass.issue_a_warning(the_warning, src: CallerId.my_caller, now: false,
            esc: nil, bail_out: false
         )
         esc ||= DbgMgr.esc
         DbgMgr.warn the_warning.to_s, my_caller: src, esc: esc, now: now
         if the_warning.is_a? Exception and bail_out
            raise the_warning
         else
            the_warning
         end
      end

      def klass.raise_an_error(the_error, src: CallerId.my_caller, now: false, 
            esc: nil, bail_out: true
         )
         esc ||= DbgMgr.esc
         DbgMgr.err the_error, my_caller: src, esc: esc, now: now
         if bail_out
            if the_error.is_a? Exception
               raise the_error
            else
               raise RuntimeError the_error
            end
         else # return the error, whatever it is
            the_error
         end
      end
   end # self.configure()


   def debugging_on?()
      if instance_variable_defined?(:@debugging_on) # instance attribute overrides the default
         @debugging_on
      else
         DbgClient::active? self.class
      end
   end

   def debugging_on=(boolean)
      @debugging_on = boolean.to_b
   end

   def debugging_key_on?(key)
      (DbgMgr.active? key) and debugging_on?
   end


   def write_dbg_stream(msg, key: nil, pre: false,
         now: false, src: CallerId.my_caller, style: nil, esc: nil
      )
      key ||= DbgClient::key self.class 
      if not debugging_key_on? key then return false end
      esc ||= DbgMgr.esc
      if pre
         DbgMgr.pre key, msg, my_caller: src, style: style, esc: esc
      else
         DbgMgr.put key, msg, my_caller: src, style: style, esc: esc
      end
      if now 
         if now.is_a? String then DbgMgr.flush after: now
         else DbgMgr.flush
         end
      end
      true
   end

   def issue_warning(the_warning, src: CallerId.my_caller, now: false,
         esc: nil, bail_out: false
      )
      esc ||= DbgMgr.esc
      DbgMgr.warn the_warning.to_s, my_caller: src, esc: esc, now: now
      if the_warning.is_a? Exception and bail_out
         raise the_warning
      else
         the_warning
      end
   end

   def raise_error(the_error, src: CallerId.my_caller, now: false, 
         esc: nil, bail_out: true
      )
      esc ||= DbgMgr.esc
      DbgMgr.err the_error, my_caller: src, esc: esc, now: now
      if bail_out
         if the_error.is_a? Exception
            raise the_error
         else
            raise RuntimeError the_error
         end
      else # return the error, whatever it is
         the_error
      end
   end
end
