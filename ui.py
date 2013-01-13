from gi.repository import Gtk, GdkPixbuf, Gdk, GExiv2
import logging
import os
import gfx

class NavUi:
  (THUMB_LIST_COL_ID,
   THUMB_LIST_COL_PATH,
   THUMB_LIST_COL_DISPLAY_NAME,
   THUMB_LIST_COL_PIXBUF,
   THUMB_LIST_NUM_COLS) = range(5)

  (FOLDER_NAV_COL_ID,
   FOLDER_NAV_COL_NAME,
   FOLDER_NAV_COL_SELECT_HANDLER,
   FOLDER_NAV_NUM_COLS) = range(4)

  (METADATA_LIST_COL_KEY,
   METADATA_LIST_COL_VALUE,
   METADATA_LIST_NUM_COLS) = range(3)

  NAV_UI_FILE = 'nav_ui.glade'

  def __init__(self, cfg):
    self.cfg = cfg
    self.log = logging.getLogger('root')

    self.on_image_open_click_handler = None
    self.preview_file = None

    # Read config options
    self.thumb_width_min = self.cfg.get_option('thumb_width_min')
    self.thumb_height_min = self.cfg.get_option('thumb_height_min')
    self.thumb_width = self.cfg.get_option('thumb_width')
    self.thumb_height = self.cfg.get_option('thumb_height')
    self.thumb_size_step = self.cfg.get_option('thumb_size_step')

    self._createUi()
    pass

  def _createUi(self):
    self.builder = Gtk.Builder()
    self.builder.add_from_file(self.NAV_UI_FILE)

    self.nav_window = self.builder.get_object('nav_window')

    # Folder navigation tree
    self.folder_nav_store = Gtk.ListStore(str, str, object)
    self.folder_nav_store.append(["", "None", None])

    folder_nav_tree = self.builder.get_object('folder_nav_tree')
    folder_nav_tree.set_model(self.folder_nav_store)
    folder_nav_tree.set_search_column(self.FOLDER_NAV_COL_NAME)
    folder_nav_tree_renderer = Gtk.CellRendererText()
    folder_nav_tree_column = Gtk.TreeViewColumn(
      "Views", folder_nav_tree_renderer, text=self.FOLDER_NAV_COL_NAME)
    folder_nav_tree.append_column(folder_nav_tree_column)

    # Thumbnails view
    self.thumb_liststore = Gtk.ListStore(
        object, str, str, GdkPixbuf.Pixbuf)
    self.thumb_liststore.set_default_sort_func(self._sort_thumb_liststore)
    self.thumb_liststore.set_sort_column_id(-1, Gtk.SortType.ASCENDING)
    thumb_iconview = self.builder.get_object('thumb_iconview')
    thumb_iconview.set_model(self.thumb_liststore)
    thumb_iconview.set_pixbuf_column(self.THUMB_LIST_COL_PIXBUF)
    thumb_iconview.set_text_column(self.THUMB_LIST_COL_DISPLAY_NAME)

    # Preview
    self.preview_scroll = self.builder.get_object('preview_scroll')
    self.preview_img = self.builder.get_object('preview_img')

    # Metadata
    self.metadata_liststore = Gtk.ListStore(str, str)
    metadata_tree = self.builder.get_object('metadata_tree')
    metadata_tree.set_model(self.metadata_liststore)
    metadata_tree_renderer = Gtk.CellRendererText()
    metadata_key_col = Gtk.TreeViewColumn(
      "Key", metadata_tree_renderer, text=self.METADATA_LIST_COL_KEY)
    metadata_tree.append_column(metadata_key_col)
    metadata_value_col = Gtk.TreeViewColumn(
      "Value", metadata_tree_renderer, text=self.METADATA_LIST_COL_VALUE)
    metadata_tree.append_column(metadata_value_col)

    # left_paned
    self.left_paned = self.builder.get_object('left_paned')
    self.left_paned_pos_last_visible = self.left_paned.get_position()

    # Auto orientation
    self.auto_orientation_toggleaction = self.builder.get_object('auto_orientation_toggleaction')

    handlers = {
      'on_nav_window_destroy' : self._exit_handler,
      'quit_action_activate_handler' : self._exit_handler,
      'on_show_preview_toggleaction_toggled' : self._show_preview_toggled_handler,
      'on_auto_orientation_toggleaction_toggled' : self._auto_orientation_toggled_handler,
      'on_folder_nav_treeview-selection_changed' : self._folder_nav_tree_selection_changed_handler,
      'on_thumb_iconview_item_activated' : self._thumb_item_activated_handler,
      'on_thumb_iconview_selection_changed' : self._thumb_item_selection_changed_handler,
      'on_inc_thumb_size_action_activate' : self._inc_thumb_size_action_activate_handler,
      'on_dec_thumb_size_action_activate' : self._dec_thumb_size_action_activate_handler,
    }
    self.builder.connect_signals(handlers)
    pass

  def _sort_thumb_liststore(self, store, a_iter, b_iter, user_data):
    (a_name) = store.get(a_iter, self.THUMB_LIST_COL_DISPLAY_NAME)
    (b_name) = store.get(b_iter, self.THUMB_LIST_COL_DISPLAY_NAME)

    if a_name is None:
      a_name = ''
    if b_name is None:
      b_name = ''

    if a_name > b_name:
      return 1
    elif a_name < b_name:
      return -1
    else:
      return 0
    pass

  def _exit_handler(self, widget):
    self.log.info("User exit requested!")
    Gtk.main_quit()
    pass

  def _show_preview_toggled_handler(self, toggleaction):
    is_preview_enabled = toggleaction.get_active()
    left_paned_max_pos = self.left_paned.get_property('max-position')
    left_paned_curr_pos = self.left_paned.get_position()

    if not is_preview_enabled:
      # Hide of preview requested, save position and move pane
      self.left_paned_pos_last_visible = left_paned_curr_pos
      self.left_paned.set_position(left_paned_max_pos)
      pass
    else:
      # Only restore position if not adjusted by user
      if left_paned_max_pos == left_paned_curr_pos:
        self.left_paned.set_position(self.left_paned_pos_last_visible)
        pass
      pass
    self.log.debug("Show preview toggled, new state=%i, "
      "left_paned_max_pos=%i, left_paned_curr_pos=%i, "
      "self.left_paned_pos_last_visible=%i",
      is_preview_enabled,
      left_paned_max_pos,
      left_paned_curr_pos,
      self.left_paned_pos_last_visible)
    pass

  def _auto_orientation_toggled_handler(self, toggleaction):
    self._reload_preview_image()
    pass

  def _inc_thumb_size_action_activate_handler(self, action):
    self.thumb_width = self.thumb_width + self.thumb_size_step
    self.thumb_height = self.thumb_height + self.thumb_size_step
    self.log.info("Increased thumbnail with increment %d to %dx%d",
      self.thumb_size_step, self.thumb_width, self.thumb_height)
    self._reload_thumbs()
    pass

  def _dec_thumb_size_action_activate_handler(self, action):
    self.thumb_width = self.thumb_width - self.thumb_size_step
    self.thumb_height = self.thumb_height - self.thumb_size_step
    self.thumb_width = max(self.thumb_width, self.thumb_width_min)
    self.thumb_height = max(self.thumb_height, self.thumb_height_min)
    self.log.info("Decreased thumbnail with decrement %d to %dx%d",
      self.thumb_size_step, self.thumb_width, self.thumb_height)
    self._reload_thumbs()
    pass

  def _folder_nav_tree_selection_changed_handler(self, selection):
    (model, tree_iter) = selection.get_selected()
    if tree_iter is not None:
      (identifier, name, on_click_handler) = model[tree_iter]
      if on_click_handler is not None:
        on_click_handler(identifier, name)
        pass
      else:
        self.log.warning('Folder %s selected, but has no handler!', name)
        pass
      pass
    else:
      self.log.warning('No tree_iter!')
      pass
    pass

  def _thumb_item_activated_handler(self, icon_view, tree_path):
    iter_ = self.thumb_liststore.get_iter(tree_path)
    (identifier, name) = self.thumb_liststore.get(
      iter_,
      self.THUMB_LIST_COL_ID,
      self.THUMB_LIST_COL_DISPLAY_NAME)
    if self.on_image_open_click_handler is not None:
      self.on_image_open_click_handler(identifier, name)
      pass
    else:
      self.log.warning('Icon %s clicked, but has no handler!', name)
      pass
    pass
  
  def _get_current_preview_size(self):
    widget = self.preview_scroll
    width = widget.get_allocated_width()
    height = widget.get_allocated_height()
    return (width, height)

  def _reload_preview_image(self):
    if self.preview_file is not None:
      (avail_w, avail_h) = self._get_current_preview_size()
      pb = gfx.Util.new_pixbuf_orient_and_scale(
        self.preview_file, avail_w, avail_h,
        orient=self.auto_orientation_toggleaction.get_active())
      self.preview_img.set_from_pixbuf(pb)
      pass
    pass

  def _reload_metadata(self):
    if self.preview_file is not None:
      self.metadata_liststore.clear()
      metadata = GExiv2.Metadata(self.preview_file)
      for tag in metadata.get_tags():
        val = metadata.get(tag, '')
        self.metadata_liststore.append([tag, val])
      pass
    pass

  def _thumb_item_selection_changed_handler(self, icon_view):
    selection = icon_view.get_selected_items()
    if len(selection) == 1:
      iter_ = self.thumb_liststore.get_iter(selection[0])
      (identifier, filename, name) = self.thumb_liststore.get(
        iter_,
        self.THUMB_LIST_COL_ID,
        self.THUMB_LIST_COL_PATH,
        self.THUMB_LIST_COL_DISPLAY_NAME)
      self.preview_file = filename
      self._reload_preview_image()
      self._reload_metadata()
      self.log.debug(
        "Item selected, preview set to %s (id=%s, path=%s)",
        name, identifier, filename)
      pass
    else:
      self.log.debug("No preview available when selecting multiple items")
      pass
    pass

  def _load_thumb(self, filename):
    pb = GdkPixbuf.Pixbuf.new_from_file_at_size(
      filename, self.thumb_width, self.thumb_height)
    if self.auto_orientation_toggleaction.get_active():
      oriented_pb = pb.apply_embedded_orientation()
      pass
    else:
      oriented_pb = pb
      pass
    return oriented_pb

  def _reload_thumbs(self):
    for item in self.thumb_liststore:
      filename = item[self.THUMB_LIST_COL_PATH]
      pb = self._load_thumb(filename)
      item[self.THUMB_LIST_COL_PIXBUF] = pb
      pass
    pass

  def add_image_open_click_handler(self, on_image_open_click_handler):
    self.on_image_open_click_handler = on_image_open_click_handler
    pass

  def add_image(self, identifier, filename, displayname):
    pb = self._load_thumb(filename)
    self.thumb_liststore.append(
      [identifier, filename, displayname, pb])
    pass

  def add_folder(self, identifier, name, on_open_handler):
    self.folder_nav_store.append([identifier, name, on_open_handler])
    pass

  def clear_images(self):
    self.thumb_liststore.clear()
    pass

  def main(self):
    self.nav_window.show_all()
    Gtk.main()
    pass


