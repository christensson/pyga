import json
import os
import logging

class Config:
  DEFAULT_CONFIG = {
    'open_image_cmd' : 'xdg-open',
    'thumb_width_min' : 32,
    'thumb_height_min' : 32,
    'thumb_width' : 128,
    'thumb_height' : 128,
    'thumb_size_step' : 32,
    'file_pattern_list' : ['.*\.JPG$', '.*\.jpg$'],
  }

  def __init__(self, config_file):
    self.config_file = config_file
    self.log = logging.getLogger('root')
    self.cfg = self._read_config_file()
    if None is self.cfg:
      self.log.info('No config file found, creating default config %s',
        self.config_file)
      self.cfg = self.DEFAULT_CONFIG
      self.save_config(self.cfg)
      pass
    pass

  def _read_config_file(self):
    cfg = None
    try:
      with open(self.config_file) as f:
        cfg = json.load(f)
        pass
      pass
    except IOError as e:
      self.log.warning('Unable to open config file %s: %s',
        self.config_file, str(e))
      pass
    return cfg

  def save_config(self, cfg=None):
    if cfg is None:
      cfg = self.cfg
      pass
    try:
      with open(self.config_file, 'w') as f:
        json.dump(cfg, f, indent=True)
        pass
      pass
    except IOError as e:
      self.log.error('Error saving config file %s: %s',
        self.config_file, str(e)) 
      pass  
    pass

  def get_option(self, key):
    if key in self.cfg:
      value = self.cfg[key]
      self.log.debug('Read config option: %s = %s',
        key, str(value))
      return value
    else:
      self.log.error('Config option "%s" not found', key)
      return None
