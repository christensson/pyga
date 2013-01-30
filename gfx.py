from gi.repository import GdkPixbuf, GExiv2
from pprint import pprint
import logging
import datetime

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
    
    # 2012:10:21 16:21:29
    EXIF_DATE_FORMAT = '%Y:%m:%d %H:%M:%S'
  
    @staticmethod
    def new_pixbuf_orient_and_scale(filename, width, height, orient=True):
        pb = GdkPixbuf.Pixbuf.new_from_file(filename)
        if orient:
            pb = pb.apply_embedded_orientation()
            pass

        full_w = pb.get_width()
        full_h = pb.get_height()
        wf = full_w / width
        hf = full_h / height
        f = max(wf, hf)
        padding = 2
        scale_w = (full_w / f) - padding
        scale_h = (full_h / f) - padding

        scaled_pb = pb.scale_simple(
            scale_w, scale_h, GdkPixbuf.InterpType.BILINEAR)
        return scaled_pb

    @staticmethod
    def get_exif_metadata(filename):
        metadata = None
        try:
            metadata = GExiv2.Metadata(filename)
            pass
        except Exception as e:
            log = logging.getLogger('root')
            log.warning('Exception while reading metadata from file %s: %s',
                        filename, str(e))
            pass
        return metadata

    @staticmethod
    def get_tags(metadata):
        tag_keys = [
                    'Iptc.Application2.Keywords',
                    'Xmp.dc.subject',
                    'Xmp.digiKam.TagsList',
                    'Xmp.lr.hierarchicalSubject',
                    'Xmp.MicrosoftPhoto.LastKeywordXMP',
                    'Xmp.photoshop.SupplementalCategories',
                    'Xmp.digiKam.TagsList',
                    ]
        tags = []
        if metadata is not None:
            for key in tag_keys:
                value = metadata.get(key, None)
                if value is not None:
                    new_tags = value.split(',')
                    for t in new_tags:
                        tag = t.strip(' ')
                        if not tag in tags:
                            tags.append(tag)
                            pass
                        pass
                    pass
                pass
            pass
        return tags

    @staticmethod
    def get_date_original(metadata):
        date = None
        key = 'Exif.Photo.DateTimeOriginal'
        if metadata is not None:
            value = metadata.get(key, None)
            if value is not None:
                try:
                    date = datetime.datetime.strptime(value, Util.EXIF_DATE_FORMAT)
                    pass
                except:
                    log = logging.getLogger('root')
                    log.warning('Error reading date from photo metadata: value=%s', value)
                    pass
                pass
            pass
        return date
