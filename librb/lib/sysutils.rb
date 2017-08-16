require "set"

# cf https://www.ruby-forum.com/topic/65458
class Class
   def prohibit_subclassing!
      class << self
         def inherited(subclass)
            error = "Illegal attempt to subclass #{self} with #{subclass}"
            raise RuntimeError, error
         end
      end
   end
end


class Array
   alias :add :push
end

class Set
   alias :add_one :add
   def add( *args )
      args.each {|arg| add_one arg}
   end
   alias :push :add
end

class Symbol
   def to_sym_string_pair
      [self, self.to_s]
   end
end


class String
   def self.a_classname(what)
      if not what.is_a? Class then what = what.class end
      what.name.a_or_an
   end
   def self.A_classname(what)
      if not what.is_a? Class then what = what.class end
      what.name.a_or_an(true)
   end
   def a_or_an(capitalize=false)
      if self.length == 0 then ""
      else
         first = self[0].downcase
         choices = if capitalize then ['A ','An '] else ['a ','an '] end
         if self.length > 1 and 'bcdfgjklmnpqrstvwxyz'.index(first) != nil
            choices[0] + self
         elsif (self.length == 1 and 'aefhimnorsx'.index(first)!= nil) or
                  ('aio'.index(first) != nil) or
                  (first == 'e' and 'uw'.index(self[1].downcase) == nil) or
                  (first == 'u' and self[1...3] != 'ni') or
                  (first == 'h' and self[1..5] == 'onest' or self[1..4] == 'onor')
            choices[1] + self
         else 
            choices[0] + self
         end
      end
   end
   def to_sym_string_pair
      [self.to_sym, self]
   end

   def to_num
      begin
         return Integer(self)
      rescue ArgumentError
         begin
            return Float(self)
         rescue ArgumentError
            erm = "'#{self}' cannot be converted to either an Integer or a Float."
            raise ArgumentError.new erm
         end
      end
   end

   def -(string_or_regexp)
      self.gsub(string_or_regexp, '')
   end
 
   def expandtabs(tabs=8)
      def first_after(tabs, tab_column)
         last = tabs[-1]
         if tab_column >= last
            raise "Tab in column #{tab_column}, which is beyond the last tab stop, #{last}"
         end
         (0 ... tabs.length).each do |n|
            if tabs[n] > tab_column
               return tabs[n]
            end
         end
      end
      if index("\t").nil?
         return self
      end
      evenly_spaced = tabs.is_a? Integer
      answer = ''
      lines = self.scan /[^\n]*\n?/
      lines.each do |line|
         sections = line.split /(\t)/
         expanded = ''
         sections.each do |section|
            if section.length == 0 then next
            elsif section[0] != "\t" then expanded += section
            else # expand the tab
               current_column = expanded.length
               if evenly_spaced
                  mod_tabs = current_column % tabs
                  need = tabs - mod_tabs
               else
                  tab_stop = first_after tabs, current_column
                  need = tab_stop - current_column
               end
               expanded += ' '*need
            end
         end
         answer += expanded
      end
      answer
   end

   def downcase?
      downcase == self
   end

   def upcase?
      upcase == self
   end
end


class FalseClass
   def to_b
      return self
   end
end

class TrueClass
   def to_b
      return self
   end
end

class Numeric
   def to_b
      if self == 1 then true
      elsif self == 0 then false
      else
         raise ArgumentError.new "cannot convert #{self} to a Boolean"
      end
   end
end

class Object
   def boolean?
      self == true || self == false
   end
   def to_b
      raise NoMethodError.new "#{self.class.name} does not implement 'to_b'"
   end
end

class String
   @@true_words = Set.new %w[true yes on ok 1]
   @@false_words = Set.new %w[false no off 0]
   def self.add_boolean(yes: nil, no: nil)
      if not yes.nil?
         @@true_words.add yes.downcase
      end
      if not no.nil?
         @@false_words.add no.downcase
      end
   end
   def to_b
      if @@true_words.member?(self.downcase)
         true
      elsif @@false_words.member?(self.downcase)
         false
      else
         raise ArgumentError.new "'#{self}' is not convertible to a Boolean"
      end
   end
end


if not nil.respond_to? :to_sym
   class NilClass
      def to_sym; nil end
   end
end


class Object
   def a_or_an_type
      String.a_classname(self)
   end
   def A_or_An_type
      String.A_classname(self)
   end
end
