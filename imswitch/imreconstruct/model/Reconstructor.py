
import numpy as np
import cupy as cp
from cupyx.scipy import signal as cpsig
from numba import cuda

from imswitch.imcommon.model import dirtools, initLogger

mempool = cp.get_default_memory_pool()
pinned_mempool = cp.get_default_pinned_memory_pool()

""" Forward model """


@cuda.jit
def NNTransform(dataStack, sampleVol, transformMat, offset):
    """Retrieve the nearest neighbour value from the samplevolume and place in the datastack"""
    idz, idy, idx = cuda.grid(3)
    if idz < dataStack.shape[0] and idy < dataStack.shape[1] and idx < dataStack.shape[2]:
        sampleCoords_z = transformMat[0, 0] * idz + transformMat[0, 1] * idy + transformMat[0, 2] * idx
        sampleCoords_y = transformMat[1, 0] * idz + transformMat[1, 1] * idy + transformMat[1, 2] * idx
        sampleCoords_x = transformMat[2, 0] * idz + transformMat[2, 1] * idy + transformMat[2, 2] * idx

        # Round to nearest and cast to int
        sampleIndex_z = int(round(sampleCoords_z))
        sampleIndex_y = int(round(sampleCoords_y))
        sampleIndex_x = int(round(sampleCoords_x))

        if 0 <= sampleIndex_z < sampleVol.shape[0] and 0 <= sampleIndex_y < sampleVol.shape[
            1] and 0 <= sampleIndex_x < \
                sampleVol.shape[2]:
            value = sampleVol[sampleIndex_z, sampleIndex_y, sampleIndex_x] + offset
            dataStack[idz, idy, idx] = value
        cuda.syncthreads()


"""Inverse model"""


@cuda.jit
def invNNTransform(dataStack, sampleVol, transformMat, offset):
    """Distribute the values in the data stack back to the sample canvas in the nearest neighbour voxel"""
    idz, idy, idx = cuda.grid(3)
    if idz < dataStack.shape[0] and idy < dataStack.shape[1] and idx < dataStack.shape[2]:
        sampleCoords_z = transformMat[0, 0] * idz + transformMat[0, 1] * idy + transformMat[0, 2] * idx
        sampleCoords_y = transformMat[1, 0] * idz + transformMat[1, 1] * idy + transformMat[1, 2] * idx
        sampleCoords_x = transformMat[2, 0] * idz + transformMat[2, 1] * idy + transformMat[2, 2] * idx

        # Round to nearest and cast to int
        sampleIndex_z = int(round(sampleCoords_z))
        sampleIndex_y = int(round(sampleCoords_y))
        sampleIndex_x = int(round(sampleCoords_x))

        if 0 <= sampleIndex_z < sampleVol.shape[0] and 0 <= sampleIndex_y < sampleVol.shape[
            1] and 0 <= sampleIndex_x < \
                sampleVol.shape[2]:
            value = dataStack[idz, idy, idx] - offset
            cuda.atomic.add(sampleVol, (sampleIndex_z, sampleIndex_y, sampleIndex_x), value)
        cuda.syncthreads()

class Reconstructor:
    """ This class takes the raw data together with pre-set
    parameters and recontructs and stores the final images (for the different
    bases).
    """

    def __init__(self):
        self.__logger = initLogger(self)

    def simpleDeskew(self, data, cam_px_size, alpha_rad, dy_step_size, recon_vx_size):
        """Extracts the signal of the data according to given parameters.
        Output is a 4D matrix where first dimension is base and last three
        are frame and pixel coordinates."""
        try:
            camera_offset = 100

            permuted_axis = (1, 0, 2)
            data_correct_axes = np.transpose(data, axes=permuted_axis).astype(float)
            adjustedData = cp.array(data_correct_axes - camera_offset).clip(0)

            """Make coordiate transformation matrix such that sampleCoordinates = M * dataCoordinates"""
            transformation_mat = cp.array([[cam_px_size * np.sin(alpha_rad), 0, 0],
                                           [cam_px_size * np.cos(alpha_rad), dy_step_size, 0],
                                           [0, 0, cam_px_size]])
            voxelize_scale_mat = cp.array(
                [[1 / recon_vx_size, 0, 0], [0, 1 / recon_vx_size, 0], [0, 0, 1 / recon_vx_size]])

            M = cp.matmul(voxelize_scale_mat, transformation_mat)

            """Make reconstruction canvas"""
            size_data = cp.array(adjustedData.shape)
            size_data_host = cp.asnumpy(size_data)
            size_sample = cp.ceil(cp.matmul(M, size_data)).astype(int)
            invTransfOnes = cp.zeros(cp.asnumpy(size_sample))
            recon_canvas = cp.zeros(cp.asnumpy(size_sample))

            lateral_ratio = cam_px_size / recon_vx_size  # px size in vx
            axial_ratio = dy_step_size * np.tan(alpha_rad) / recon_vx_size  # distance between planes in vx
            z_halfsize = 2 * axial_ratio
            y_halfsize = 2 * lateral_ratio
            x_halfsize = 2 * lateral_ratio
            k_mesh = np.meshgrid(np.linspace(-z_halfsize, z_halfsize, int(np.ceil(2 * z_halfsize))),
                                 np.linspace(-y_halfsize, y_halfsize, int(np.ceil(2 * y_halfsize))),
                                 np.linspace(-x_halfsize, x_halfsize, int(np.ceil(2 * x_halfsize))), indexing='ij')

            k_prime_z = k_mesh[0]  # *np.cos(alpha) - k_mesh[1]*np.sin(alpha)
            k_prime_y = k_mesh[1]  # k_mesh[0]*np.sin(alpha) + k_mesh[1]*np.cos(alpha)
            k_prime_x = k_mesh[2]
            sigma_lat = lateral_ratio / 2.355
            sigma_ax = axial_ratio / 2.355

            kernel = np.exp(-(
                        k_prime_x ** 2 / (2 * sigma_lat ** 2) + k_prime_y ** 2 / (2 * sigma_lat ** 2) + k_prime_z ** 2 / (
                            2 * sigma_ax ** 2)))
            # kernel = (np.ones_like(k_prime_x) - np.sqrt(
            #     (k_prime_x / lateral_ratio) ** 2 + (k_prime_y / lateral_ratio) ** 2 + (k_prime_z / axial_ratio) ** 2)).clip(
            #     0)
            cupy_kernel = cp.array(kernel)
            """Reconstruct"""
            dataOnes = cp.ones_like(adjustedData)
            threadsperblock = 8
            blocks_per_grid_z = (size_data_host[0] + (threadsperblock - 1)) // threadsperblock
            blocks_per_grid_y = (size_data_host[1] + (threadsperblock - 1)) // threadsperblock
            blocks_per_grid_x = (size_data_host[2] + (threadsperblock - 1)) // threadsperblock
            invNNTransform[(blocks_per_grid_z, blocks_per_grid_y, blocks_per_grid_x),
                           (threadsperblock, threadsperblock, threadsperblock)](dataOnes, invTransfOnes, M, 0)

            invNNTransform[(blocks_per_grid_z, blocks_per_grid_y, blocks_per_grid_x),
                           (threadsperblock, threadsperblock, threadsperblock)](adjustedData, recon_canvas, M, 0)

            interpolatedData = cpsig.fftconvolve(recon_canvas, cupy_kernel, mode='same')
            interpolatedHtFromOnes = cpsig.fftconvolve(invTransfOnes, cupy_kernel, mode='same').clip(
                0.1)  # Avoid divide by zero
            reconstructed = cp.asnumpy(cp.divide(interpolatedData, interpolatedHtFromOnes))
        finally:
            mempool.free_all_blocks()

        return reconstructed


# Copyright (C) 2020-2021 ImSwitch developers
# This file is part of ImSwitch.
#
# ImSwitch is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ImSwitch is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
