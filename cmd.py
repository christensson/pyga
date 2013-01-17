from gi.repository import Gtk, Gdk, GLib

class GtkCommand:
	LOW_PRIO = GLib.PRIORITY_LOW
	DEFAULT_PRIO = GLib.PRIORITY_DEFAULT_IDLE
	HIGH_PRIO = GLib.PRIORITY_HIGH

	def __init__(self, func, data, prio=HIGH_PRIO):
		self.func = func
		self.data = data
		self.prio = prio
		self.event_id = None
		pass

	def _queue(self):
		#self.event_id = Gdk.threads_add_idle(self.prio, self.func, self.data)
		self.event_id = GLib.idle_add(self.func, self.data)
		pass

	@staticmethod
	def dispatch(func, data, prio=HIGH_PRIO):
		command = GtkCommand(func, data, prio)
		command._queue()
		return command

