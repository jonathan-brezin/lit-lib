

module CallerId
   def self.who_am_i
      name_from_caller_entry caller[0]
   end

   def self.my_caller
      name_from_caller_entry caller[1]
   end

   def self.name_from_caller_entry caller_entry
      matched = /`([^']*)'/.match caller_entry
      matched.captures[0]
   end
end

