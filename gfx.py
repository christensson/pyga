from gi.repository import GdkPixbuf
import logging


class Util:
	ROTATE_CLOCKWISE = 90
	ROTATE_UPSIDEDOWN = 180
	ROTATE_COUNTERCLOCKWISE = 270

	EXIF_ORIENTATION_NONE = '1'
	EXIF_ORIENTATION_FLIP_HORIZ = '2'
	EXIF_ORIENTATION_ROTATE_180 = '3'
	EXIF_ORIENTATION_FLIP_VERT = '4'
	EXIF_ORIENTATION_TRANSPOSE = '5'
	EXIF_ORIENTATION_ROTATE_90 = '6'
	EXIF_ORIENTATION_TRANSVERSE = '7'
	EXIF_ORIENTATION_ROTATE_270 = '8'
	
	@staticmethod
	def pixbuf_transform_using_orientation(pb):
		log = logging.getLogger('root')
		w, h = pb.get_width(), pb.get_height()
		exif_orientation = pb.get_option('orientation')
		log.info("Image w=%d, h=%d, exif_orientation=%s",
			w, h, exif_orientation)
		newpb = pb.apply_embedded_orientation()
		return newpb


