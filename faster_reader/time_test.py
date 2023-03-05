import random
from copy import deepcopy

import numba as nb
import numpy as np
import torch as th
import taichi as ti
import taichi.math as tm
from line_profiler_pycharm import profile

ti.init(arch=ti.gpu)


@profile
def torch_way(CT_torch, L: int, W: int, index: int):
    torch_image = CT_torch[index, :, :].clone()
    torch_image = ((torch_image - int((L - W) / 2)) / W * 255)
    torch_image = torch_image.clamp(0, 255).type(th.uint8)
    return torch_image.numpy()


@profile
def torch_cuda_way(CT_torch_cuda, L: int, W: int, index: int):
    torch_cuda_image = CT_torch_cuda[index, :, :].clone()
    torch_cuda_image = ((torch_cuda_image - int((L - W)/2)) / W * 255)
    torch_cuda_image = torch_cuda_image.clamp(0, 255).type(th.uint8)
    return torch_cuda_image.cpu().numpy()


@profile
def numpy_way(CT_numpy: np.array, L: int, W: int, index: int):
    numpy_image = deepcopy(CT_numpy[index, :, :])
    numpy_image = ((numpy_image - int((L - W)/2)) / W * 255).astype(np.uint8)
    return np.clip(numpy_image, 0, 255)


@profile
def numba_way(CT_numpy: np.array, L: int, W: int, index: int):
    numpy_image = deepcopy(CT_numpy[index, :, :])
    return numpy_faster(numpy_image, L, W)


@nb.jit()
def numpy_faster(img: np.array, L: int, W: int):
    img = ((img - int((L - W)/2)) / W * 255).astype(np.uint8)
    return np.clip(img, 0, 255)


@profile
def pixel_wise_way(CT_numpy: np.array, L: int, W: int, index: int):
    numpy_image = deepcopy(CT_numpy[index, :, :])
    for pixel in np.nditer(numpy_image, op_flags=['readwrite']):
        pixel = int((pixel - int((L - W)/2)) / float(W) * 255)
        if pixel < 0:
            pixel = 0
        if pixel > 255:
            pixel = 255
    return numpy_image.astype(np.uint8)


@ti.kernel
def taichi_cuda_way(x: ti.template(), y: ti.types.ndarray(), L: int, W: int, index: int):
    # deepcopy
    for i, j in x:
        x[i, j] = y[index, i, j]
        x[i, j] = (x[i, j] - int((L - W)/2)) / W * 255
        x[i, j] = tm.clamp(x[i, j], 0, 255)


@ti.kernel
def taichi_way(x: ti.template(), y: ti.types.ndarray(), L: int, W: int, index: int):
    # deepcopy
    for i, j in x:
        x[i, j] = y[index, i, j]
        x[i, j] = (x[i, j] - int((L - W)/2)) / W * 255
        x[i, j] = tm.clamp(x[i, j], 0, 255)


@profile
def time_test():
    for _ in range(1):
        index = random.randint(0, 200)
        # torch_way(CT_torch, 127, 255, index)
        # torch_cuda_way(CT_torch_cuda, 127, 255, index)
        # numpy_way(CT_numpy, 127, 255, index)
        # numba_way(CT_numpy, 127, 255, index)
        taichi_cuda_way(taichi_field, CT_torch_cuda, 127, 255, index)
        taichi_cuda_out = taichi_field.to_numpy(dtype=np.uint8)
        # taichi_way(taichi_field, CT_numpy, 127, 255, index)
        # taichi_out = taichi_field.to_numpy(dtype=np.uint8)
        # pixel_wise_way(CT_numpy, 127, 255, index)


if __name__ == '__main__':
    CT_torch = th.load('../CT_data.pt').type(th.float32)
    CT_torch_cuda = CT_torch.cuda().type(th.float16)
    CT_numpy = CT_torch.numpy().astype(np.float32)
    taichi_field = ti.field(ti.f16, shape=(512, 512))
    time_test()
