import logging
import os
import re
import uuid

import gfx

VIEW_NAME_ALL = 'all'

class DbItem:
    def __init__(self, identity, filename, dirname, original_date, view_ids):
        self.identity = identity
        self.filename = filename
        self.dirname = dirname
        self.original_date = original_date
        self.view_ids = view_ids
        pass

    def get_full_path(self):
        return os.path.join(self.dirname, self.filename)

    def get_id(self):
        return self.identity
    
    def get_display_name(self):
        return self.filename
    
    def get_original_date(self):
        return self.original_date

    def get_view_ids(self):
        return self.view_ids

    def __str__(self):
        return self.get_display_name()

class ViewGroup:
    def __init__(self, group_name):
        self.id = uuid.uuid4()
        self.name = group_name
        pass

    def __str__(self):
        return self.name

    def get_id(self):
        return self.id

class ViewItem:
    @staticmethod
    def new_folder_view(view_group, path, newest_date=None, oldest_date=None):
        identity = path + str(view_group.get_id())
        viewname = os.path.split(path)[1]
        view = ViewItem(identity, viewname, path, view_group, newest_date, oldest_date)
        return view

    @staticmethod
    def new_tag_view(view_group, tag, newest_date=None, oldest_date=None):
        identity = tag + str(view_group.get_id())
        viewname = tag
        view = ViewItem(identity, viewname, None, view_group, newest_date, oldest_date)
        return view

    @staticmethod
    def new_all_view(view_group, identity, newest_date=None, oldest_date=None):
        viewname = VIEW_NAME_ALL
        view = ViewItem(identity, viewname, None, view_group, newest_date, oldest_date)
        return view

    def __init__(self, identity, viewname, path, view_group, newest_date=None, oldest_date=None):
        self.log = logging.getLogger('root')
        self.identity = identity
        self.viewname = viewname
        self.newest_date = newest_date
        self.oldest_date = oldest_date
        self.view_group = view_group
        self.items = []
        pass

    def add_item_id(self, item):
        self.items.append(item)
        pass

    def get_item_ids(self):
        return self.items

    def get_num_items(self):
        return len(self.items)

    def set_dates(self, oldest_date, newest_date):
        self.oldest_date = oldest_date
        self.newest_date = newest_date
        pass

    def add_date(self, date):
        if self.oldest_date is None:
            self.oldest_date = date
            pass
        elif date < self.oldest_date:
            self.oldest_date = date
            pass

        if self.newest_date is None:
            self.newest_date = date
            pass
        elif date > self.newest_date:
            self.newest_date = date
            pass
        
    def get_newest_date(self):
        return self.newest_date

    def get_oldest_date(self):
        return self.oldest_date

    def __str__(self):
        return self.viewname

    def get_id(self):
        return self.identity

    def get_group_id(self):
        return self.view_group.get_id()

class Db:
    ALL_VIEW_NAME = 'all'
    NONE_VIEW_NAME = 'none'

    def __init__(self, dir_list, file_pattern_list):
        self.dir_list = dir_list
        self.file_pattern_list = file_pattern_list
        self.log = logging.getLogger('root')
        self.item_dict = {}
        self.view_dict = {}
        self.view_group_dict = {}
        self.view_group_dict['folders'] = ViewGroup("Folders")
        self.view_group_dict['tags'] = ViewGroup("Tags")
        self.view_group_dict['misc'] = ViewGroup("Misc")
        self.all_view_id = self._get_new_id()
        self._init_view_dict()
        pass

    def _init_view_dict(self):
        view = ViewItem.new_all_view(self.view_group_dict['misc'], self.all_view_id)
        self.view_dict[self.all_view_id] = view
        pass

    def _get_all_view(self):
        return self.view_dict[self.all_view_id]

    def _get_folder_view(self, path):
        view = ViewItem.new_folder_view(self.view_group_dict['folders'], path)
        view_id = view.get_id()
        if view_id not in self.view_dict:
            self.view_dict[view_id] = view
            pass
        else:
            view = self.view_dict[view_id]
            pass
        return view

    def _get_tag_view(self, tag):
        view = ViewItem.new_tag_view(self.view_group_dict['tags'], tag)
        view_id = view.get_id()
        if view_id not in self.view_dict:
            self.view_dict[view_id] = view
            pass
        else:
            view = self.view_dict[view_id]
            pass
        return view

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
                        dir_view = self._get_folder_view(dirname)
                        included_file_count = included_file_count + 1
                        self.add_file(filename, dirname, dir_view)
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

    def _get_new_id(self):
        identity = uuid.uuid4()
        # Check unique
        while (identity in self.item_dict) or (identity in self.view_dict):
            identity = uuid.uuid4()
            pass
        return identity

    def add_file(self, filename, dirname, dir_view):
        item_id = self._get_new_id()
        path = os.path.join(dirname, filename)
        metadata = gfx.Util.get_exif_metadata(path)
        tags = gfx.Util.get_tags(metadata)
        original_date = gfx.Util.get_date_original(metadata)
        views = []
        views.append(self._get_all_view())
        views.append(dir_view)
        for t in tags:
            tag_view = self._get_tag_view(t)
            views.append(tag_view)
            pass

        view_ids = []
        for v in views:
            view_ids.append(v.get_id())
            pass
        
        item = DbItem(item_id, filename, dirname, original_date, view_ids)
        self.item_dict[item_id] = item
        self.log.spam('Adding file %s (id=%s, views=%s)',
                      os.path.join(dirname, filename),
                      item_id,
                      str(views))
        for v in views:
            v.add_item_id(item_id)
            v.add_date(original_date)
            pass
        pass

    def get_item_from_id(self, identifier):
        if identifier in self.item_dict:
            return self.item_dict[identifier]
        return None

    def get_view_from_id(self, identifier):
        if identifier in self.view_dict:
            return self.view_dict[identifier]
        return None

    def get_view_dict(self):
        return self.view_dict

    def get_views(self):
        return self.view_dict.values()

    def get_view_groups(self):
        return self.view_group_dict.values()

    def get_view_ids(self):
        return self.view_dict.keys()

    def get_view_item_identifiers(self, view_id):
        if view_id in self.view_dict:
            return self.view_dict[view_id].get_item_ids()
        return None

    def _match_list(self, name, regex_list):
        for regex in regex_list:
            if regex.match(name):
                return True
            pass
        return False
        
    
