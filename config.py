import json
import os
import logging

class Config:
	DEFAULT_CONFIG = {
		'open_image_cmd' : 'xdg-open',
		'thumb_width' : 96,
		'thumb_height' : 96,
	}

	def __init__(self, config_file):
		self.config_file = config_file
		self.log = logging.getLogger('root')
		self.cfg = self._read_config_file()
		if None is self.cfg:
			self.log.info('No config file found, creating %s',
				self.config_file)
			self.cfg = self.DEFAULT_CONFIG
			self.save_config(self.DEFAULT_CONFIG)
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
			self.log.warning('Error opening config file found %s: %s',
				self.config_file, str(e))
			pass
		return cfg

	def save_config(self, cfg=None):
		if cfg is None:
			cfg = self.cfg
			pass
		try:
			with open(self.config_file, 'w') as f:
				json.dump(cfg, f)
				pass
			pass
		except IOError as e:
			self.log.info('Error saving config file %s: %s',
				self.config_file, str(e))	
			pass	
		pass

	def get_option(self, key):
		if key in self.cfg:
			return self.cfg[key]
		else:
			return None
