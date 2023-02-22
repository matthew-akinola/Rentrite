import os
import random
import string
from datetime import datetime

def get_passport_path(request, filename):
    original_filename = filename
    nowTime = datetime.now().strftime('%Y_%m_%d_%H:%M:%S_')
    filename = "%s%s%s" % ('IMG_', nowTime, original_filename)

    return os.path.join('passport/', filename)

def get_attachment_path(request, filename):
    original_filename = filename
    nowTime = datetime.now().strftime('%Y_%m_%d_%H:%M:%S_')
    filename = "%s%s%s" % ('RentRite_', nowTime, original_filename)
    return os.path.join('message/attachments/', filename)

def get_blogs_image_path(request, filename):
    original_filename = filename
    nowTime = datetime.now().strftime('%Y_%m_%d_%H:%M:%S_')
    filename = "%s%s%s" % ('RentRite_', nowTime, original_filename)

    return os.path.join('blogs/images/', filename)

def reg_number_generator (length = 10, chars = string.digits):
    return ''.join(random.choice(chars) for _ in range(length))

