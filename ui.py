from gi.repository import Gtk, GdkPixbuf, Gdk
import logging
import os
import gfx

class NavUi:
  (ICON_VIEW_COL_ID,
   ICON_VIEW_COL_PATH,
   ICON_VIEW_COL_DISPLAY_NAME,
   ICON_VIEW_COL_PIXBUF,
   ICON_VIEW_NUM_COLS) = range(5)

  (FOLDER_NAV_COL_ID,
   FOLDER_NAV_NAME,
   FOLDER_NAV_SELECT_HANDLER,
   FOLDER_NAV_NUM_VOLS) = range(4)

  NAV_UI_FILE = 'nav_ui.glade'

  def __init__(self, cfg):
    self.cfg = cfg
    self.log = logging.getLogger('root')
    self.thumb_width = self.cfg.get_option('thumb_width')
    self.thumb_height = self.cfg.get_option('thumb_height')
    self.on_image_open_click_handler = None
    self.preview_file = None

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
    folder_nav_tree.set_search_column(self.FOLDER_NAV_NAME)
    folder_nav_tree_renderer = Gtk.CellRendererText()
    folder_nav_tree_column = Gtk.TreeViewColumn(
      "Views", folder_nav_tree_renderer, text=self.FOLDER_NAV_NAME)
    folder_nav_tree.append_column(folder_nav_tree_column)

    # Thumbnails view
    self.thumb_liststore = Gtk.ListStore(
        object, str, str, GdkPixbuf.Pixbuf)
    self.thumb_liststore.set_default_sort_func(self._sort_thumb_liststore)
    self.thumb_liststore.set_sort_column_id(-1, Gtk.SortType.ASCENDING)
    thumb_iconview = self.builder.get_object('thumb_iconview')
    thumb_iconview.set_model(self.thumb_liststore)
    thumb_iconview.set_pixbuf_column(self.ICON_VIEW_COL_PIXBUF)
    thumb_iconview.set_text_column(self.ICON_VIEW_COL_DISPLAY_NAME)

    # Preview
    self.preview_scroll = self.builder.get_object('preview_scroll')
    self.preview_img = self.builder.get_object('preview_img')

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
    }
    self.builder.connect_signals(handlers)
    pass

  def _sort_thumb_liststore(self, store, a_iter, b_iter, user_data):
    (a_name) = store.get(a_iter, self.ICON_VIEW_COL_DISPLAY_NAME)
    (b_name) = store.get(b_iter, self.ICON_VIEW_COL_DISPLAY_NAME)

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
      self.ICON_VIEW_COL_ID,
      self.ICON_VIEW_COL_DISPLAY_NAME)
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
      pb = GdkPixbuf.Pixbuf.new_from_file(self.preview_file)
      if self.auto_orientation_toggleaction.get_active():
        oriented_pb = pb.apply_embedded_orientation()
        pass
      else:
        oriented_pb = pb
        pass

      (avail_w, avail_h) = self._get_current_preview_size()
      full_w = oriented_pb.get_width()
      full_h = oriented_pb.get_height()
      wf = full_w / avail_w
      hf = full_h / avail_h
      f = max(wf, hf)
      padding = 2
      scale_w = (full_w / f) - padding
      scale_h = (full_h / f) - padding
      scaled_pb = oriented_pb.scale_simple(
        scale_w, scale_h, GdkPixbuf.InterpType.BILINEAR)
      self.preview_img.set_from_pixbuf(scaled_pb)
      pass
    pass

  def _thumb_item_selection_changed_handler(self, icon_view):
    selection = icon_view.get_selected_items()
    if len(selection) == 1:
      iter_ = self.thumb_liststore.get_iter(selection[0])
      (identifier, filename, name) = self.thumb_liststore.get(
        iter_,
        self.ICON_VIEW_COL_ID,
        self.ICON_VIEW_COL_PATH,
        self.ICON_VIEW_COL_DISPLAY_NAME)
      self.preview_file = filename
      self._reload_preview_image()
      self.log.debug(
        "Item selected, preview set to %s (id=%s, path=%s)",
        name, identifier, filename)
      pass
    else:
      self.log.debug("No preview available when selecting multiple items")
      pass
    pass

  def add_image_open_click_handler(self, on_image_open_click_handler):
    self.on_image_open_click_handler = on_image_open_click_handler
    pass

  def add_image(self, identifier, filename, displayname):
    pb = GdkPixbuf.Pixbuf.new_from_file_at_size(
      filename, self.thumb_width, self.thumb_height)
    if self.auto_orientation_toggleaction.get_active():
      oriented_pb = pb.apply_embedded_orientation()
      pass
    else:
      oriented_pb = pb
      pass
    self.thumb_liststore.append(
      [identifier, filename, displayname, oriented_pb])
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


