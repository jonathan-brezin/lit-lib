
require "dbgclient"
require "fileaddons"

class VersionedFile < File
   include DbgClient
   DbgClient::configure self, "versions", "versions"
   def initialize(path, options)
      if not options.key? :mode then options[:mode] = 'r' end
      if not File.exists? path
         write_dbg_stream "#{path} is a new file: no backup created."
      else
         case options[:mode].gsub('b', '')
         when 'w', 'w+'
            VersionedFile.new_version path, true, options
         when 'a', 'a+', 'r+'
            VersionedFile.new_version path, false, options
         else # do nothing
            write_dbg_stream "#{path} opened read-only: no new version needed"
         end
      end
      super path, options
   end
   @@backup_limit = 5  # the default is to keep at most 5 backup versions
   @@backup_path = '.' # the default is to backup in the same directory as the file
   def self.backup_limit=(new_limit)
      old_limit = @@backup_limit
      @@backup_limit = if new_limit.nil? then nil else Integer(new_limit) end
      write_dbg_msg "Default backup limit reset to #{new_limit}", key: "backup"
      old_limit
   end
   def self.backup_limit
       @@backup_limit
   end
   def self.backup_path=(new_path)
      old_path = @@backup_path
      @@backup_path = new_path
      write_dbg_msg "Default backup path reset to #{new_path}", key: "backup"
      old_path
   end
   def self.backup_path
      @@backup_path
   end


   def self.new_version(path, may_rename, options)
      write_dbg_msg "new=#{path}, bak='#{options[:bak]}'"
      path = File.expand_path path
      if not File.exists? path
         return
      end
      
      to_keep = if options[:keep].nil? then @@backup_limit else Integer options[:keep] end
      if to_keep == 0
         msg = "Request to backup '#{path}', but 0 versions are to be kept!!!"
         write_dbg_msg msg
         return
      end 
      directory = File.dirname path # path is already absolute here, so dirname works ok
      filename = File.basename path
      write_dbg_msg "File name from path is #{filename}"
      last_dot = filename.rindex '.'
      if last_dot.nil?
         extension = ''
      else
         extension = filename[last_dot .. -1]
         filename  = filename[0 ... last_dot]
      end
      msg = "after split, filename is #{filename} and the extension is #{extension}"
      write_dbg_msg msg
      backup_dir = File.expand_path (options[:bak] or  @@backup_path), directory
      msg = "backups go to #{backup_dir}; options[:bak] is #{options[:bak]} "
      write_dbg_msg msg
      File.assure_directory(backup_dir)
      new_version, versions = self.name_the_next_version(backup_dir, filename, extension)
      # if there are too many backups, delete some before creating a new one
      if not (to_keep.nil? or to_keep > versions.length)
         number_to_delete = versions.length + 1 - to_keep
         versions[0 ... number_to_delete].each do | version |
            write_dbg_msg "removing backup #{version} of #{path}"
            File.delete(File.join backup_dir, version)
         end
      end
      new_path = File.join(backup_dir, new_version)
      if may_rename # don't save original, which will be truncated on opening for write
         File.rename path, new_path
      else   
         IO.copy_stream path, new_path
      end 
   end

   private
   def self.name_the_next_version(directory, filename, extension)
      write_dbg_msg "filename: #{filename}, ext: #{extension}", key: "next_version"
      regexp_src = '^' + Regexp.escape(filename) + "_0*([1-9][0-9]*)" + Regexp.escape(extension) +'$'
      matcher = Regexp.compile(regexp_src)
      versions = Dir.entries(directory).find_all {|entry| matcher.match(entry) != nil}
      write_dbg_msg "Saved versions:\n#{versions}", key: "next_version"
      if versions.length == 0
         new_version = filename+"_001"+extension
      else
         versions.sort! 
         last_version = Integer matcher.match(versions[-1]).captures[0]
         next_version = last_version + 1
         new_version = filename + "_#{'%.3d' % next_version}" + extension
      end
      [new_version, versions]
   end
end
