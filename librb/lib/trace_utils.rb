

require "set"

class Object
   def is_traceable(variable_name_or_symbol, mode="rw")
      name = variable_name_or_symbol.to_s
      if name.start_with '@@'
         pass
      elsif name.start_with '@'
         pass
      elsif not instance_variables.index('@'+name).to_sym.nil?
         pass
      elsif self.is_a? Class 
         if not class_variables.index('@@'+name).to_sym.nil?
            pass
         end
      else
         if not self.class.class_variables.index('@@'+name).to_sym.nil?
            pass
         else
            raise ArgumentError "'#{name}' does not name a local variable for #{self}"
         end
      end
   end

   def _find_rw_methods(names, mode)
      readers = Set.new
      writers = Set.new
      names.each do |cv|
         stripped = cv.to_s.gsub(/^@+/, '')
         if self.respond_to? stripped
            readers.add stripped.to_sym
         end
         if self.respond_to? stripped+"="
            writers.add stripped.to_sym
         end
      end
      both = readers & writers
      case mode
      when "rw"
         both
      when "r"
         readers
      when "w"
         writers
      when "r!"
         readers - writers
      when "w!"
         writers - readers
      when nil
         all = readers + writers
         answer = {}
         all.each do |name|
            if both.include? name
               answer[name] = "rw"
            elsif readers.include? name
               answer[name] = "r"
            else
               answer[name] = "w"
            end
         end
         answer
      else
         legal = "It should be nil or one of #{%w(r w rw r! w!)}"
         raise ArgumentError "Illegal mode: '#{mode}'.  #{legal}"
      end
   end

   def get_traceable_class_variables(mode=nil)
      owner = if self.kind_of? Class then self else self.class end
      _find_rw_methods owner.class_variables(), mode
   end

   def get_traceable_instance_variables(mode=nil)
      _find_rw_methods self.instance_variables(), mode
   end
end
