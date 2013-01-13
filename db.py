import logging
import os
import re
import uuid

VIEW_NAME_ALL = 'all'

class DbItem:
    def __init__(self, identity, filename, dirname):
        self.identity = identity
        self.filename = filename
        self.dirname = dirname
        pass

    def get_full_path(self):
        return os.path.join(self.dirname, self.filename)

    def get_id(self):
        return self.identity
    
    def get_display_name(self):
        return self.filename

    def get_view_names(self):
        view_names = []
        view_names.append(VIEW_NAME_ALL)
        last_dir = os.path.split(self.dirname)[1]
        view_names.append(last_dir)
        return view_names

class Db:
    def __init__(self, dir_list, file_pattern_list):
        self.dir_list = dir_list
        self.file_pattern_list = file_pattern_list
        self.log = logging.getLogger('root')
        self.item_dict = {}
        self.view_dict = {}
        pass

    def build(self):
        # Compile file regex
        file_regex_list = []
        for pattern in self.file_pattern_list:
            file_regex_list.append(re.compile(pattern))
            pass
        # Search for files
        for dir in self.dir_list:
            included_file_count = 0
            total_file_count = 0
            self.log.debug('Searching dir %s', dir)
            for dirname, dirnames, filenames in os.walk(dir):
                for filename in filenames:
                    total_file_count = total_file_count + 1
                    if self._match_list(filename, file_regex_list):
                        included_file_count = included_file_count + 1
                        self.add_file(filename, dirname)
                        pass
                    else:
                        self.log.spam('File %s ignored',
                                      os.path.join(dirname, filename))
                        pass
                    pass
                pass
            self.log.info('Found %d files in dir %s (total %d)',
                          included_file_count, dir, total_file_count)
            pass

        self.log.info('Db contains %d files sorted into %d views',
                      len(self.item_dict), len(self.view_dict))
        pass

    def add_file(self, filename, dirname):
        identity = uuid.uuid4()
        # Make sure that id is unique
        while identity in self.item_dict:
            identity = uuid.uuid4()
            pass
        item = DbItem(identity, filename, dirname)
        self.item_dict[identity] = item
        views = item.get_view_names()
        self.log.spam('Adding file %s (id=%s, views=%s)',
                      os.path.join(dirname, filename),
                      identity,
                      str(views))
        for v in views:
            # Create list of view members if view doesn't exist
            if v not in self.view_dict:
                self.view_dict[v] = []
                self.log.spam('Creating view "%s"', v)
                pass
            # Add
            self.view_dict[v].append(identity)
            pass
        pass

    def get_item_from_id(self, identifier):
        if identifier in self.item_dict:
            return self.item_dict[identifier]
        return None

    def get_view_dict(self):
        return self.view_dict

    def get_view_names(self):
        return self.view_dict.keys()

    def get_view_item_identifiers(self, identifier):
        if identifier in self.view_dict:
            return self.view_dict[identifier]
        return None

    def _match_list(self, name, regex_list):
        for regex in regex_list:
            if regex.match(name):
                return True
            pass
        return False
        
    
