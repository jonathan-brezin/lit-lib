
require "sysutils"


class Class
   def  aliased_instance_methods
      # see Marc-André Lafortune (http://stackoverflow.com/users/8279/marc-andr%C3%A9-lafortune)
      instance_methods.group_by{|m| instance_method(m)}.map(&:last).keep_if{|syms| syms.length > 1}
   end

   def instance_method_aliases_for sym_or_str
      symbol = sym_or_str.to_sym
      as_array = aliased_instance_methods.keep_if { |symbols| symbols.include? symbol }
      if as_array.length == 0 then []
      else
         answer = as_array[0]
         answer.delete symbol
         answer
      end
   end

   def are_instance_aliases?(this, that)
      instance_method_aliases_for(this).include? that.to_sym
   end

   def create_an_instance_alias(the_alias, original: "")
      original_sym = original.to_sym
      unless instance_methods.include? original_sym 
         raise NameError.new "instances of #{self} do not respond to #{original_sym}"
      end
      alias_sym = the_alias.to_sym
      if instance_methods.include? alias_sym
         false
      else
         self.send :alias_method, alias_sym, original_sym
         true
      end
   end
end

class Object
   def aliased_methods
      # see Marc-André Lafortune (http://stackoverflow.com/users/8279/marc-andr%C3%A9-lafortune) 
      methods.group_by{|m| method(m)}.map(&:last).keep_if{|syms| syms.length > 1}
   end

   def aliases_for sym_or_str
      symbol = sym_or_str.to_sym
      as_array = aliased_methods.keep_if { |symbols| symbols.include? symbol }
      if as_array.length == 0 then []
      else
         answer = as_array[0]
         answer.delete symbol
         answer
      end
   end

   def are_aliases?(this, that)
      method(this.to_sym) == method(that.to_sym)
   end

   def create_an_alias(the_alias, original: "")
      original_sym = original.to_sym
      if not respond_to? original_sym 
         raise NameError.new "#{self} does not respond to #{original_sym}"
      end
      alias_sym = the_alias.to_sym
      if respond_to?(alias_sym)
         false
      else
         singleton_class.send :alias_method, alias_sym, original_sym
         true
      end
   end
end
