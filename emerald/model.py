from keras.models import model_from_json
from keras.preprocessing.image import ImageDataGenerator
import cv2
import abc

import numpy as np
import sys, os

from importlib_resources import files


class MaskingModel(metaclass=abc.ABCMeta):
    '''abstract class to guarantee children will
    have predict_mask method'''
    @abc.abstractmethod
    def predict_mask(self, image):
        '''abstract method, to be implemented by child classes'''
        pass

class Unet(MaskingModel):
    '''Unet class to manage the loding of model and weights and
    predictive use'''

    def __init__(self):
        '''Class constructor get json model and h5 weigths and load model'''

        weight_path = str(files(f'{__package__}.weights').joinpath('emerald_weights.h5'))
        model_path = files(f'{__package__}.json_models').joinpath('emerald_model.json')

        json_model = model_path.read_text()

        self.unet_model = model_from_json(json_model)
        self.unet_model.load_weights(weight_path)

    def __getGenerator(self, image, bs=1):
        '''getGenerator Returns generator that will be used for
        prdicting, it takes a single 3D image and returns a generator
        of its slices'''

        # rescale data to its trained mode
        image_datagen = ImageDataGenerator(rescale=1./255)
        image_datagen.fit(image, augment = True)
        image_generator = image_datagen.flow(x = image, batch_size=bs,
                shuffle = False)

        return image_generator

    def predict_mask(self, image):
        '''predict_mask creates a prediction for a whole 3D image'''
        image_gen = self.__getGenerator(image)
        mask = self.unet_model.predict_generator(image_gen, steps=len(image))
        # only keep pixels with more than 0.5% probability of being brain
        mask[mask >= 0.5] = 1
        mask[mask < 0.5] = 0

        return mask
