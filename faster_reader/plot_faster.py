from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from skimage import measure, morphology
import numpy as np
import torch as th
from line_profiler_pycharm import profile

plt.rcParams['font.sans-serif'] = 'SimHei'


# @profile
def plot_brain(verts, brain, CT_data, x, y, z):
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')
    # 绘制三个截取平面
    dx, dy, dz = [x - 1 for x in CT_data.shape]
    xx = np.linspace(0, dx, 10)
    yy = np.linspace(0, dy, 10)
    zz = np.linspace(0, dz, 10)
    xx2, yy2 = np.meshgrid(xx, yy)
    ax.plot_surface(xx2, yy2, np.full_like(xx2, z), color='green', alpha=0.5)
    ax.text(0, 0, z, '横断面', fontsize=15, color='black', bbox=dict(facecolor='green', alpha=0.7))
    yy2, zz2 = np.meshgrid(yy, zz)
    ax.plot_surface(np.full_like(yy2, x), yy2, zz2, color='blue', alpha=0.5)
    ax.text(x, dy, dz - 20, '冠状面', fontsize=15, color='black', bbox=dict(facecolor='blue', alpha=0.7))
    xx2, zz2 = np.meshgrid(xx, zz)
    ax.plot_surface(xx2, np.full_like(yy2, y), zz2, color='red', alpha=0.5)
    ax.text(dx / 2, y, dz - 20, '矢状面', fontsize=15, color='black', bbox=dict(facecolor='red', alpha=0.7))

    # Fancy indexing: `verts[faces]` to generate a collection of triangles
    mesh = Poly3DCollection(verts[brain], alpha=0.70)
    face_color = [0.45, 0.45, 0.75]
    mesh.set_facecolor(face_color)
    ax.add_collection3d(mesh)
    ax.set_xlim(0, CT_data.shape[0])
    ax.set_ylim(0, CT_data.shape[1])
    ax.set_zlim(0, CT_data.shape[2])

    plt.show()


# @profile
def simple_visual(CT_data, x, y, z, color='red'):
    # 长方体外框起点(x0,y0,z0)
    x0 = y0 = z0 = 0
    dx, dy, dz = [x - 1 for x in CT_data.shape]
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')
    xx = [x0, x0, x0 + dx, x0 + dx, x0]
    yy = [y0, y0 + dy, y0 + dy, y0, y0]
    kwargs1 = {'alpha': 1, 'color': color}
    ax.plot3D(xx, yy, [z0] * 5, **kwargs1)
    ax.plot3D(xx, yy, [z0 + dz] * 5, **kwargs1)
    ax.plot3D([x0, x0], [y0, y0], [z0, z0 + dz], **kwargs1)
    ax.plot3D([x0, x0], [y0 + dy, y0 + dy], [z0, z0 + dz], **kwargs1)
    ax.plot3D([x0 + dx, x0 + dx], [y0 + dy, y0 + dy], [z0, 2 + dz], **kwargs1)
    ax.plot3D([x0 + dx, x0 + dx], [y0, y0], [z0, z0 + dz], **kwargs1)
    # 绘制三个截取平面
    xx = np.linspace(0, dx, 10)
    yy = np.linspace(0, dy, 10)
    zz = np.linspace(0, dz, 10)
    xx2, yy2 = np.meshgrid(xx, yy)
    ax.plot_surface(xx2, yy2, np.full_like(xx2, z), color='green', alpha=0.5)
    ax.text(dx / 2, dy / 2, z, '横断面', fontsize=15,
            color='black', bbox=dict(facecolor='green', alpha=0.7))
    yy2, zz2 = np.meshgrid(yy, zz)
    ax.plot_surface(np.full_like(yy2, x), yy2, zz2, color='blue', alpha=0.5)
    ax.text(x, dy / 2, dz / 2, '冠状面', fontsize=15,
            color='black', bbox=dict(facecolor='blue', alpha=0.7))
    xx2, zz2 = np.meshgrid(xx, zz)
    ax.plot_surface(xx2, np.full_like(yy2, y), zz2, color='red', alpha=0.5)
    ax.text(dx / 2, y, dz / 2, '矢状面', fontsize=15,
            color='black', bbox=dict(facecolor='red', alpha=0.7))
    print(ax.get_children())
    ax.draw_artist()

    plt.show()


# @profile
def main():
    CT_data = th.load('../CT_data.pt').numpy()
    print('数据读取完毕, shape:{}'.format(CT_data.shape))
    # for _ in range(10):
    simple_visual(CT_data, 50, 450, 100)
    # CT_data = CT_data.transpose(1, 2, 0)
    # verts, brain, _, _ = measure.marching_cubes(CT_data, 500)
    # plot_brain(verts, brain, CT_data, 350, 250, 50)


if __name__ == '__main__':
    main()
