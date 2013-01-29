from gi.repository import Gtk, Gdk
import logging
import subprocess

import db
import ui
import config
import cmd

class Controller:
  def __init__(self, args):
    self.log = logging.getLogger('root')
    self.args = args
    self.cfg = config.Config(self.args.config_file)
    
    file_pattern_list = self.cfg.file_pattern_list
    self.dbase = db.Db(self.args.dir_list, file_pattern_list)
    self.dbase.build()

    self.view = ui.NavUi(self.cfg)

    self.view.add_folder_open_click_handler(
      self._on_folder_click_handler)
    self.view.add_image_open_click_handler(
      self._on_image_open_click_handler)
    self.view.add_exit_handler(
      self._on_exit_handler)
    pass

  def main(self):
    Gdk.threads_init()
    self._show_all_views()
    self.view.show()
    Gtk.main()
    pass

  def _show_all_views(self):
    self.view.clear_images()
    for view_group in self.dbase.get_view_groups():
      self.view.add_folder_group(view_group)
      pass
    for view_item in self.dbase.get_views():
      self.view.add_folder(view_item)
      pass
    pass

  def _add_image_item(self, item):
    self.view.add_image(
      item.get_id(),
      item.get_full_path(),
      item.get_display_name())
    pass        

  def _on_exit_handler(self):
    Gtk.main_quit()
    pass

  def _on_folder_click_handler(self, view_item):
    self.log.debug('Folder %s clicked (id=%s)', str(view_item), view_item.get_id())
    items = view_item.get_item_ids()
    if items is not None:
      self.view.clear_images()
      for item_id in items:
        item = self.dbase.get_item_from_id(item_id)
        self._add_image_item(item)
        pass
      pass
    else:
      self.log.warning('Folder %s clicked (id=%s), but not found!',
        str(view_item), view_item.get_id())
      pass
    pass

  def _on_image_open_click_handler(self, identifier, name):
    item = self.dbase.get_item_from_id(identifier)
    if None is not item:
      path = item.get_full_path()
      cmd = [self.cfg.open_image_cmd, path]
      self.log.info('Opening image %s (id=%s, path=%s) with command=%s',
        name, identifier, path, str(cmd))
      subprocess.call(cmd)
      pass
    else:
      self.log.warning('Image %s clicked but id=%s not found in db',
        name, identifier)
      pass
    pass

