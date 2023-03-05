# encoding: utf-8
"""
@author: Ljz
@file: main.py
@time: 2022/11/29 12:12
"""
import numpy as np
import SimpleITK as sitk
import os
import cv2
import warnings


def splitSuffix(directory):
    """
    Open files in the specific directory and
    Split the name and suffix of all files
    :param directory: str
    :return: names: list[str]
    :return: suffixs: list[str]
    """
    paths = os.listdir(directory)
    names = []
    suffixs = []
    for path in paths:
        name, suffix = os.path.splitext(path)
        names.append(name)
        suffixs.append(suffix)
    return names, suffixs


def str2int(string):
    """
    Convert a string(may include other symbols) to a number
    E.g. : '123asd456$%' -> 123456
    :param string: str
    :return: int
    """
    return int("".join(list(filter(str.isdigit, string))))


def list2arr(data, offset=None, dtype=None):
    """
    Convert a list of numpy arrays with the same size to a large numpy array.
    This is way more efficient than directly using numpy.array()
    :param data: [numpy.array]
    :param offset: array to be subtracted from the each array.
    :param dtype: data type
    :return: numpy.array
    """
    num = len(data)
    out_data = np.empty((num,) + data[0].shape, dtype=dtype if dtype else data[0].dtype)
    for i in range(num):
        out_data[i] = data[i] - offset if offset else data[i]
    return out_data


def dcm2arr(directory):
    """
    Open dcm files directory and convert the squeezes to a array.
    :param directory: str
    :return: numpy.array
    """
    reader = sitk.ImageSeriesReader()
    img_names = reader.GetGDCMSeriesFileNames(directory)
    reader.SetFileNames(img_names)
    image = reader.Execute()
    dcm_array = sitk.GetArrayFromImage(image)
    return dcm_array


def pic2arr(directory):
    """
    Open image files directory and convert the squeezes to a array.
    Supported image suffix: .jpg, .png, .tif
    :param directory: str
    :param compressed: when reading image, whether to reserve its original depth
    :return: numpy.array
    """
    names, suffixs = splitSuffix(directory)

    # str2int
    namesBag = [(str2int(ori_name), ori_name, suffix) for (ori_name, suffix) in zip(names, suffixs)]
    namesBag.sort()
    # int2str
    names = [ori_name + suffix for (name_index, ori_name, suffix) in namesBag]

    pic_list = []
    for name in names:
        pic_path = os.path.join(directory, name)
        pic = cv2.imread(pic_path, cv2.IMREAD_ANYDEPTH)
        # uint8 -> uint16
        if pic.dtype == 'uint8':
            pic = 257 * pic.astype(np.uint16)
        pic_list.append(pic)
    pic_array = list2arr(pic_list)
    return pic_array

