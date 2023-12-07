from pathlib import Path
from typing import Optional, List, Tuple

import cv2
import numpy as np
import numpy.typing as npt
from medpy.io import load, save
from skimage.measure import label
from skimage.morphology import binary_closing, binary_dilation, cube

from emerald.model import Unet


def getImageData(fname):

    '''Returns the image data, image matrix and header of
    a particular file'''
    data, hdr = load(fname)
    # axes have to be switched from (256,256,x) to (x,256,256)
    data = np.moveaxis(data, -1, 0)

    norm_data = []
    # normalize each image slice
    for i in range(data.shape[0]):
        img_slice = data[i,:,:]
        norm_data.append(__normalize0_255(img_slice))

    # remake 3D representation of the image
    data = np.array(norm_data, dtype=np.float32)

    data = data[..., np.newaxis]
    return data, hdr

def __resizeData(image, target=(256, 256)):
    image = np.squeeze(image)
    resized_img = []
    for i in range(image.shape[0]):
        img_slice = cv2.resize(image[i,:,:], target)
        resized_img.append(img_slice)

    image = np.array(resized_img, dtype=np.float32)

    return image[..., np.newaxis]

def __normalize0_255(img_slice):
    '''Normalizes the image to be in the range of 0-255
    it round up negative values to 0 and caps the top values at the
    97% value as to avoid outliers'''
    img_slice[img_slice < 0] = 0
    flat_sorted = np.sort(img_slice.flatten())

    #dont consider values greater than 97% of the values
    top_3_limit = int(len(flat_sorted) * 0.97)
    limit = flat_sorted[top_3_limit]

    img_slice[img_slice > limit] = limit

    rows, cols = img_slice.shape
    #create new empty image
    new_img = np.zeros((rows, cols))
    max_val = np.max(img_slice)
    if max_val == 0:
        return new_img

    #normalize all values
    for i in range(rows):
        for j in range(cols):
            new_img[i,j] = int((
                float(img_slice[i,j])/float(max_val)) * 255)

    return new_img

def __postProcessing(mask, no_dilation, footprint):

    mask = np.squeeze(mask)
    x , y , z = np.shape(mask)
    dilated_mask = np.zeros((x,y,z))

    #Binary dilation
    if no_dilation :
        for slice in range(y):
            t = mask[:,slice,:]
            slice_dilated = binary_dilation(t,footprint)*1
            dilated_mask[:,slice,:] = slice_dilated
    else: 
        dilated_mask = mask

    #Binary closing
    pred_mask = binary_closing(np.squeeze(dilated_mask), cube(2))

    try:
        labels = label(pred_mask)
        pred_mask = (labels == np.argmax(np.bincount(labels.flat)[1:])+1).astype(np.float32)
    except:
        pred_mask = pred_mask

    return pred_mask


def emerald(model: Unet, input_path: str, mask_path: Optional[Path], brain_paths: List[Tuple[float, Path]],
            post_processing: bool, footprint: Optional[npt.NDArray]):
    img_path = str(input_path)

    img_original, hdr = getImageData(img_path)
    img_resized = img_original
    resizeNeeded = False

    if img_original.shape[1] != 256 or img_original.shape[2] != 256:
        original_shape = (img_original.shape[2], img_original.shape[1])
        img_resized = __resizeData(img_original)
        resizeNeeded = True

    res = model.predict_mask(img_resized)

    if post_processing:
        res = __postProcessing(res, no_dilation=(footprint is not None), footprint=footprint)

    if resizeNeeded:
        # jennings to sofia: why np.float32 instead of uint8?
        res = __resizeData(res.astype(np.float32), target = original_shape)

    #remove extra dimension
    res = np.squeeze(res)

    #return result into shape (256,256,X)
    res = np.moveaxis(res, 0, -1)

    #save result
    if mask_path:
        save(res.astype(np.float32), str(mask_path), hdr)

    if brain_paths:
        # for whatever reason, img.shape=(38, 256, 256, 1).
        if len(img_original.shape) == 4 and img_original.shape[3] == 1:
            img_original = np.squeeze(img_original)
            img_original = np.moveaxis(img_original, 0, -1)

    # apply res mask to img
    for mult, brain_path in brain_paths:
        overlayed_data = np.clip(res, mult, 1.0) * img_original
        save(overlayed_data, str(brain_path), hdr)
