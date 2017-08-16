
require "aliasing"
require "sysutils"


WrapInfo = Struct.new("WrapInfo", :source, :source_alias, :wrap_alias, :is_inherited, :save_alias)

class Module
   def wrap_instance_method(method_name, &block1)
      #puts "wrapping #{method_name} in #{self}"
      Mutex.new.synchronize do
         count = Module.module_eval do
            @_wm_count_ ||= 0
            @_wm_count_ +=1
         end
         alias_for_original = "_original_#{method_name}_#{count}"
         create_an_instance_alias alias_for_original, original: method_name
         wrapped_code = "_wrapped_#{method_name}_#{count}".to_sym
         saved_code = "_saved_#{method_name}_#{count}".to_sym
         the_method = instance_method method_name
         is_inherited = (the_method.owner != self)
         send :define_method, saved_code do
            [the_method, block1]
         end
         send :undef_method, method_name unless method_name.to_s == "initialize"
         send :define_method, wrapped_code do |*args2, &block2|
            the_saver = self.method saved_code 
            old, new = the_saver.call
            old = old.bind self
            new.call(old, args2, block2, self)
         end
         create_an_instance_alias method_name, original: wrapped_code
         WrapInfo.new(method_name.to_sym, alias_for_original, wrapped_code, is_inherited, saved_code)
      end
   end

   def pre_condition(method_name, &block1)
      wrap_instance_method method_name do |org_method, args2, block2, obj2|
         block1.call(obj2, method_name, args2, block2)
         org_method.call(*args2, &block2)
      end
   end

   def post_condition(method_name, &block1)
      wrap_instance_method method_name do |org_method, args2, block2, obj2|
         return_value = org_method.call(*args2, &block2)
         block1.call(obj2, method_name, args2, block2, return_value)
      end
   end

   def pre_and_post_condition(method_name, &block1)
      wrap_instance_method method_name do |org_method, args2, block2, obj2|
         block1.call obj2, :pre, method_name, args2, block2, nil
         return_value = org_method.call(*args2, &block2)
         block1.call obj2, :post, method_name, args2, block2, return_value
      end
   end

   def restore_instance_method(wrap_info)
      send :remove_method, wrap_info.source
      if not wrap_info.is_inherited 
         # if it is inherited source now refers to the current method in the superclass
         # thus we only need an alias if source really was defined here
         create_an_instance_alias wrap_info.source, original: wrap_info.source_alias 
      end
      send :remove_method, wrap_info.source_alias
      send :remove_method, wrap_info.save_alias
      send :remove_method, wrap_info.wrap_alias
   end
end

def turn_on(which, wrap_info)
      send :remove_method, wrap_info.source
      case which.to_sym
      when :wrapped then send :alias_method,  wrap_info.source, wrap_info.wrap_alias
      when :plain then send :alias_method,  wrap_info.source, wrap_info.source_alias
      else raise ArgumentError.new "expected :wrapped or :plain, but got '#{which}'"
      end
   end


class Object
   def wrap_my_method(method_name, &block1)
      #puts "wrapping #{method_name} for object #{self}"
      Mutex.new.synchronize do
         count = Module.module_eval do
            @_wm_count_ ||= 0
            @_wm_count_ +=1
         end
         alias_for_original = "_original_#{method_name}_#{count}"
         create_an_alias alias_for_original, original: method_name
         wrapped_code = "_wrapped_#{method_name}_#{count}".to_sym
         saved_code = "_saved_#{method_name}_#{count}".to_sym
         the_method = method method_name
         is_inherited = (the_method.owner != self)
         singleton_class.send(:define_method, saved_code) do
            [the_method, block1]
         end
         singleton_class.send :undef_method, method_name unless method_name.to_s == "initialize"
         singleton_class.send :define_method, wrapped_code do |*args2, &block2|
            the_saver = self.method saved_code
            old, new = the_saver.call
            new.call(old, args2, block2, self)
         end
         create_an_alias method_name, original: wrapped_code
         WrapInfo.new method_name.to_sym, alias_for_original, wrapped_code, is_inherited, saved_code
      end
   end

   def pre_condition_me(method_name, &block1)
      wrap_my_method method_name do |org_method, args2, block2, obj2|
         block1.call(obj2, method_name, args2, block2)
         org_method.call(*args2, &block2)
      end
   end

   def post_condition_me(method_name, &block1)
      wrap_my_method method_name do |org_method, args2, block2, obj2|
         return_value = org_method.call *args2, &block2
         block1.call obj2, method_name, args2, block2, return_value
      end
   end

   def pre_and_post_condition_me(method_name, &block1)
      wrap_my_method method_name do |org_method, args2, block2, obj2|
         block1.call obj2, :pre, method_name, args2, block2, nil
         return_value = org_method.call(*args2, &block2)
         block1.call obj2, :post, method_name, args2, block2, return_value
         return_value
      end
   end

   def restore_my_method(wrap_info)
      singleton_class.send :remove_method, wrap_info.source
      if not wrap_info.is_inherited
         code, block = send wrap_info.saved_code
         if code.owner == self
            send :alias_method, wrap_info.source_alias, wrap_info.source
         else
            singleton_class.send :alias_method, wrap_info.source_alias, wrap_info.source
         end
      end
      singleton_class.send :remove_method, wrap_info.source_alias
      singleton_class.send :remove_method, wrap_info.save_alias
      singleton_class.send :remove_method, wrap_info.wrap_alias
   end

   def turn_on_my(which, wrap_info)
      singleton_class.send :remove_method, wrap_info.source
      case which.to_sym
      when :wrapped then singleton_class.send :alias_method, wrap_info.source, wrap_info.wrap_alias
      when :plain then singleton_class.send :alias_method, wrap_info.source, wrap_info.source_alias
      else ArgumentError.new "expected :wrapped or :plain, but got '#{which}'"
      end
   end
end
