import logging
import os
import re
import uuid

import gfx

VIEW_NAME_ALL = 'all'

class DbItem:
    def __init__(self, identity, filename, dirname, view_ids):
        self.identity = identity
        self.dirname = dirname
        self.filename = filename
        self.view_ids = view_ids
        pass

    def get_full_path(self):
        return os.path.join(self.dirname, self.filename)

    def get_id(self):
        return self.identity
    
    def get_display_name(self):
        return self.filename

    def get_view_ids(self):
        return self.view_ids

class ViewItem:
    VIEW_TYPE_FOLDER = 0
    VIEW_TYPE_TAG = 1
    VIEW_TYPE_ALL = 2

    @staticmethod
    def new_folder_view(path, newest_date=None, oldest_date=None):
        view_type = ViewItem.VIEW_TYPE_FOLDER
        identity = path + str(view_type)
        viewname = os.path.split(path)[1]
        view = ViewItem(identity, viewname, path, view_type, newest_date, oldest_date)
        return view

    @staticmethod
    def new_tag_view(tag, newest_date=None, oldest_date=None):
        view_type = ViewItem.VIEW_TYPE_TAG
        identity = tag + str(view_type)
        viewname = '#' + tag
        view = ViewItem(identity, viewname, None, view_type, newest_date, oldest_date)
        return view

    @staticmethod
    def new_all_view(identity, newest_date=None, oldest_date=None):
        viewname = '*' + VIEW_NAME_ALL
        view = ViewItem(identity, viewname, None, ViewItem.VIEW_TYPE_ALL, newest_date, oldest_date)
        return view

    def __init__(self, identity, viewname, path, view_type, newest_date=None, oldest_date=None):
        self.log = logging.getLogger('root')
        self.identity = identity
        self.viewname = viewname
        self.newest_date = newest_date
        self.oldest_date = oldest_date
        self.type = view_type
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

    def __str__(self):
        return self.viewname

    def get_id(self):
        return self.identity

class Db:
    ALL_VIEW_NAME = 'all'

    def __init__(self, dir_list, file_pattern_list):
        self.dir_list = dir_list
        self.file_pattern_list = file_pattern_list
        self.log = logging.getLogger('root')
        self.item_dict = {}
        self.view_dict = {}
        self.all_view_id = self._get_new_id()
        self._init_view_dict()
        pass

    def _init_view_dict(self):
        view = ViewItem.new_all_view(self.all_view_id)
        self.view_dict[self.all_view_id] = view
        pass

    def _get_all_view(self):
        return self.view_dict[self.all_view_id]

    def _get_folder_view(self, path):
        view = ViewItem.new_folder_view(path)
        view_id = view.get_id()
        if view_id not in self.view_dict:
            self.view_dict[view_id] = view
            pass
        else:
            view = self.view_dict[view_id]
            pass
        return view

    def _get_tag_view(self, tag):
        view = ViewItem.new_tag_view(tag)
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
        
        item = DbItem(item_id, filename, dirname, view_ids)
        self.item_dict[item_id] = item
        self.log.spam('Adding file %s (id=%s, views=%s)',
                      os.path.join(dirname, filename),
                      item_id,
                      str(views))
        for v in views:
            v.add_item_id(item_id)
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
        
    
