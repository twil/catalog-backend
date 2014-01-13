# coding: utf-8
"""
Helper functions to work with images

"""
import os
#from PIL import Image

# To guess extension from mime-type
# Note: may save JPEG like .jpe
import mimetypes
mimetypes.init()


'''
def average_color(img):
    """
    Calculate average pixel color
    
    Based on http://www.elysium3d.com/?p=250
    
    """
 
    ###Grab width, height, and build a list of each pixel in the image.
    width, height = img.size
    pixels = img.load()
    data = []
    for x in range(width):
        for y in range(height):
            cpixel = pixels[x, y]
            data.append(cpixel)
 
    ###Setup our R, G, and B variables for some math!
    r = 0
    g = 0
    b = 0
    avg_count = 0
 
    ###Run through every single pixel in the image, grab the r, g, and b value.
    ###Then test if the image has an alpha. If so, only average pixels with an
    ###alpha value of 200 or greater (out of 255).
    for x in range(len(data)):
        try:
            weight = float(data[x][3]) / float(255)
            r += data[x][0] * weight
            g += data[x][1] * weight
            b += data[x][2] * weight
        except:
            r += data[x][0]
            g += data[x][1]
            b += data[x][2]
 
        avg_count += 1
 
    ###Get the averages, and return!
    r_avg = r/avg_count
    g_avg = g/avg_count
    b_avg = b/avg_count
 
    return (r_avg, g_avg, b_avg)


def create_thumb(file_name, sizes, suffix):
    """
    Create icon for specified image with specified size
    
    """
    
    file_name_wo_ext, ext = os.path.splitext(file_name)
    
    im = Image.open(file_name)
    avg_color = average_color(im)
    width, height = im.size
    
    # check aspect ratio to determine if cut needed
    dst_ratio = float(sizes[0]) / sizes[1]
    src_ratio = float(width) / height
    ratio_difference = (src_ratio - dst_ratio) / max(src_ratio, dst_ratio)
    # if difference less than threshold - cut!
    if abs(ratio_difference) < 0.2 and abs(ratio_difference) > 0.001:
        if ratio_difference > 0:
            new_width = int(height * dst_ratio)
            left_offset = (width - new_width) / 2
            crop_box = (left_offset, 0, left_offset + new_width, height)
        else:
            new_height = int(width / dst_ratio)
            top_offset = (height - new_height) / 2
            crop_box = (0, top_offset, width, top_offset + new_height)
            
        im = im.crop(crop_box)
        im.load()
    
    im.thumbnail(sizes, Image.ANTIALIAS)
    
    # calc location to past
    width, height = im.size
    paste_loc = (sizes[0] - width) / 2, (sizes[1] - height) / 2
       
    im_base = Image.new('RGB', sizes, avg_color)
    im_base.paste(im, paste_loc)
    result_file_name = file_name_wo_ext + suffix + '.jpg'
    im_base.save(result_file_name, "JPEG")
    return result_file_name
'''

def save_img(filepath_wo_ext, img):
    """Save image
    
    filepath_wo_ext is file path w/o extension
    image is tuple from to_image_data()
    
    """
    
    ext = '.unknown'
    try:
        ext = mimetypes.guess_extension(img[0])
    except:
        pass
    fullpath = u'{}{}'.format(filepath_wo_ext, ext)
    f = open(fullpath, 'wb')
    f.write(img[1])
    f.close()
    
    return fullpath
