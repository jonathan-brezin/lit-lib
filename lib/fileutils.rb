
require 'open3'
class File 
   def self.split_a_path_list(string)
      string.split(PATH_SEPARATOR)
   end

   def self.now4filename(extension=nil, show: :both)
      name = case show
             when :both then Time.now.strftime "%y%m%d_%H%M%S"
             when :date then Time.now.strftime "%y%m%d"
             when :time then Time.now.strftime "%H%M%S"
             end
      if extension.nil?
         name 
      elsif extension[0]=='.' 
         name+extension
      else 
         name+'.'+extension
      end
   end

   def self.assure_directory(path, permissions: '0740', all: false)
      path = expand_path path  # make sure leading "~" is translated
      if exists? path
         if not directory? path
            raise IOError.new "'#{path}' exists, but is not a directory"
         end
         return self
      end
      if permissions.is_a? Integer
         permissions = permissions.to_s 8
      end
      recurse = if all then '-p ' else '' end
      exit_status = '?'
      cmd = "mkdir -m #{permissions} #{recurse} #{path}"
      stdin, stdout_stderr, wait_thr = Open3.popen2e(cmd) 
      exit_status = wait_thr.value
      puts exit_status
      if exit_status != 0
         puts "assure_directory failed #{exit_status}: #{stdout_stderr.read}", file=STDERR
      end
   end
   def self.normalized_path(parent=Dir.getwd, child: nil, alternate: nil)
      if alternate.nil? or alternate.length == 0
         if child.nil? or child.length == 0
            raise ArgumentError.new "Either an alternate path or a child must be supplied"
         else
            expand_path child, parent
         end
      else
         expand_path alternate, parent
      end
   end
   def self.parent_directory path
      dirname expand_path(path)
   end
end

