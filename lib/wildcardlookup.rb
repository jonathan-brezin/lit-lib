=begin <head> 
Title: <span class="titleCode">WildCardLookup</span> simple wild-card matching
Author: Jonathan Brezin
Date: April, 2016
Show source: Yes
Tab Size: 3
=end #head

require "set"


class WildCardLookup
   include Enumerable

   attr_reader :all, :exact, :pairs # these constitute the state of the pattern catalogue

   def self.from_csv(a_csv)
      self.new a_csv.split(',')
   end

   def initialize(*patterns)
      @all = false     # optimization only '*' is a pattern, so all keys match
      @cache = Hash.new false # the results of previous match attempts
      @exact = Set.new # patterns with no wild cards
      @pairs = Hash.new {|hash,head| hash[head] = Set.new} # maps head of match to a set of tails
      add_patterns(patterns)
   end

   def ==(other)
      @exact == other.exact and @pairs == other.pairs and @all == other.all
   end

   def !=(other)
      @exact != other.exact or @pairs != other.pairs or @all != other.all
   end


   def clone()
      WildCardLookup.new @pattern_list
   end

   def lengths
      [@exact.length, @pairs.length, @cache.length]
   end

   def add_pattern(pattern)
      star_index = pattern.index("*")
      if star_index.nil?
         @exact.add(pattern)
      elsif pattern == "*"
         @all = true
         @cache = Hash.new false
      else
         head = pattern[0 ... star_index]
         tail = pattern[star_index+1 .. -1]
         if tail.index('*')
            raise "Pattern '#{pattern}' has too many *'s"
         end
         @pairs[head].add(tail)
         @cache.each do |cached, found|
            if not found and head_tail_match?(cached, head, tail)
               @cache[cached] = true
            end
         end
      end
   end

   def add_patterns(patterns)
      patterns.each do | pattern |
         add_pattern(pattern)
      end
   end

   def remove_pattern(pattern)
      if pattern == '*'
         @all = false
         true
      elsif @exact.member? pattern
         @exact.delete pattern
         true
      else
         head_index = pattern.index '*'
         if not head_index.nil? 
            head = pattern[0 ... head_index]
         end
         if @pairs.member? head
            tail = pattern[head_index+1 .. -1]
            tail_set = @pairs[head]
            if tail_set.member? tail
               tail_set.delete tail
               if tail_set.length == 0
                  @pairs.delete head
               end
               if @cache.length > 0 then @cache = Hash.new false end
               # print("#{pattern} deleted\n")
               return true
            end
         end
         false
      end
   end

   def remove_patterns(dead_patterns)
      removed = 0
      dead_patterns.each do | dead_pattern |
         #print("#{removed}: remove #{dead_pattern}\n")
         if remove_pattern dead_pattern
            #print("Succeeded!\n")
            removed += 1
         end
      end
      removed
   end


   def matched?(key)
      if @all or @exact.member?(key) or @cache[key]
         true
      elsif key.length < 2
         false
      else
         @cache[key] = pattern_match?(key)
      end
   end

   def all_matched?( *args )
      args.each do |arg|
         if arg.kind_of? String 
            if not matched?(arg) then return false end
         elsif arg.kind_of? Array 
            if not all_matched *arg then return false end
         else raise ArgumentError.new "Unexpected argument type, #{args.class}"
         end
      end
      true
   end

   def any_matched?( *args )
      args.each do |arg|
         if arg.kind_of? String 
            if matched?(arg) then return true end
         elsif arg.kind_of? Array
            if any_matched? *arg then return true end
         else
            raise ArgumentError.new "Unexpected argument type, #{arg.class}"
         end
      end
      false
   end

   def head_tail_match?(key, head, tail)
      #puts %Q[ #{key.length>head.length+tail.length}, #{key.start_with?(head)}, #{key[head.length() .. -1].end_with?(tail)}]
      (key.length > head.length + tail.length) &&
         key.start_with?(head) && 
         key[head.length() .. -1].end_with?(tail)
   end

   def pattern_match?(key)
      key_length = key.length
      @pairs.each do |head, tails|
         tails.each do |tail|
            #puts("#{key} matches #{head}*#{tail}?  key tail is #{key[head.length() .. -1]}\n")
            if head_tail_match? key, head, tail
               return true
            end
         end
      end
      false
   end

   def pattern_list()
      list =  @exact.clone.to_a
      if @all then list.push '*' end
      @pairs.each do |head, tails|
         list += tails.collect { |tail| "#{head}*#{tail}" }
      end
      list.sort!
   end

   def strictest_pattern(key)
      # the exact match is definitely the strictest look no further 
      if @exact.member? key then key
      else
         allmatches = patterns_matching key
         if allmatches.length == 0
            if @all then '*' else nil end
         else
            sizes = allmatches.collect {|x| x.length }
            allmatches[sizes.index sizes.max]
         end
      end
   end

   def weakest_pattern(key)
      allmatches = patterns_matching(key)
      case allmatches.length
      when 0 then nil
      when 1 then allmatches[0] 
      else 
         # there are multiple matches, but if there is an exact match it will sort
         # lexicographically after any '*' pattern, even if its length happens to
         # be the same as the pattern length: 'abcd' matches 'a*cd'.  Given a choice
         # between 'a*d' and 'ab*d', we want the weaker pattern, 'a*d', which again
         # sorts earlier.  'a*cd' sorts before 'a*d', so to get the weakest, we 
         # really want the shortest.  If 'a*d' is not a pattern, but 'ab*d' and
         # 'a*cd' both are, we arbitrarily choose 'ab*d', the one that is earlier
         # lexicographically.
         allmatches.sort!{|x, y| x.length <=> y.length }
         min = allmatches[0].length 
         shortest = allmatches.find_all {|x| x.length == min}
         shortest.sort!
         shortest[0] # I'm the first in lexicographic order among the shortest patterns
      end
   end

   def patterns_matching(key)
      list = []
      if @exact.member? key
         list.push key
      end
      if @all 
         list.push '*'
      end
      if key.length >= 2
         @pairs.each do | head, tails |
            if key.start_with?(head) && key.length > head.length
               rest = key[head.length()+1 .. -1]
               tails.each do | tail |
                  if rest.end_with? tail
                     list.push "#{head}*#{tail}"
                  end
               end
            end
         end
      end
      list.sort!
   end
       
   def all_matched(*keys)
      if keys.length > 0 and not @all
         keys.each do | entry |
            entry.split(',').each do | key |
               if not matched? key
                  return false
               end
            end
         end
      end
      true
   end

   def each
      @exact.each do | pattern |
         yield pattern
      end
      @pairs.each do | head, tails |
         tails.each do |tail|
            yield "#{head}*#{tail}"
         end
      end
      nil
   end
end
