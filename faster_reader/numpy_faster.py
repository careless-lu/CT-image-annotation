import random
from copy import deepcopy

import numpy as np
import torch as th
from line_profiler_pycharm import profile


@profile
def numpy_way_1(CT_numpy: np.array, L: int, W: int, index: int):
    numpy_image = deepcopy(CT_numpy[index, :, :])
    numpy_image = ((numpy_image - int((L - W) / 2)) / W * 255).astype(np.uint8)
    return np.clip(numpy_image, 0, 255)


@profile
def numpy_way_2(CT_numpy: np.array, L: int, W: int, index: int):
    numpy_image = deepcopy(CT_numpy[index, :, :])
    numpy_image = np.clip(numpy_image, int((L - W) / 2), int((L + W) / 2))
    return ((numpy_image - int((L - W) / 2)) / W * 255).astype(np.uint8)


@profile
def time_test():
    CT_torch = th.load('../CT_data.pt').type(th.float32)
    CT_numpy = CT_torch.numpy().astype(np.float32)

    for _ in range(100):
        index = random.randint(0, 200)
        numpy_way_1(CT_numpy, 127, 255, index)
        numpy_way_2(CT_numpy, 127, 255, index)


if __name__ == '__main__':
    time_test()
