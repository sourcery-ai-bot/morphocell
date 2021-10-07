"""Implements utility functions that operate on 3D images."""

import numpy as np
from skimage.transform import rescale
from skimage.exposure import rescale_intensity

from typing import Tuple, Union, List, Dict, Sequence
import numpy.typing as npt

# image operations assume ZYX channel order


def image_stats(img: npt.ArrayLike, q: Tuple[float, float] = (0.1, 99.9)) -> Dict[str, float]:
    """Compute intensity image statistics (min, max, mean, percentiles)."""
    q_min, q_max = np.percentile(img, q=q)
    return {
        "min": np.min(img),
        "max": np.max(img),
        "mean": np.mean(img),
        "percentile_min": q_min,
        "precentile_max": q_max,
    }


def rescale_xy(img: npt.ArrayLike, factor: float = 1.0, anti_aliasing=True) -> np.ndarray:
    """Rescale image in XY."""
    return rescale(img, (1.0, factor, factor), preserve_range=False, anti_aliasing=anti_aliasing)


def rescale_isotropic(
    img: npt.ArrayLike,
    voxel_sizes: Union[Tuple[int, ...], Tuple[float, ...]],
    downscale_xy: bool = False,
    order: int = 3,
) -> np.ndarray:
    """Rescale image in XY to isotropic voxel size."""
    xz_ratio = voxel_sizes[1] / voxel_sizes[0]
    factors = (1.0, xz_ratio, xz_ratio) if downscale_xy else (1 / xz_ratio, 1.0, 1.0)
    return rescale(img, factors, order=order, preserve_range=True, anti_aliasing=downscale_xy)


def normalize_min_max(img: npt.ArrayLike, q: Tuple[float, float] = (0.1, 99.9)) -> np.ndarray:
    """Normalize image intensities between percentiles."""
    vmin, vmax = np.percentile(img, q=q)
    return rescale_intensity(img, in_range=(vmin, vmax), out_range=np.float32)


def max_project(img: npt.ArrayLike, axis: int = 0) -> np.ndarray:
    """Compute maximum intensity projection along the chosen axis."""
    return np.max(img, axis)


def img_mse(a, b) -> int:
    """Calculate pixel-wise MSE between two images."""
    assert len(a) == len(b)
    return np.square(a - b).mean()


def pad_image(
    img: npt.ArrayLike,
    pad_size: Union[int, Sequence[int]],
    axis: int = 0,
    mode: str = "reflect",
) -> np.ndarray:
    """Pad an image."""
    npad = np.asarray([(0, 0)] * img.ndim)
    npad[axis] = [pad_size] * 2 if isinstance(pad_size, int) else pad_size
    return np.pad(img, pad_width=npad, mode=mode)


def pad_image_to_cube(img: npt.ArrayLike, cube_size: int) -> np.ndarray:
    """Pad all image axis up to cubic shape."""
    for i, dim in enumerate(img.shape):
        if dim < cube_size:
            pad_size = (cube_size - dim) // 2
            img = pad_image(img, pad_size=pad_size, axis=i)

    #     assert img.shape[0] == img.shape[1] == img.shape[2] == cube_size
    return img


def crop_tl(img: npt.ArrayLike, crop_hw: Union[int, Tuple[int, int]]) -> np.ndarray:
    """Crop left top corner."""
    crop_h, crop_w = (crop_hw, crop_hw) if isinstance(crop_hw, int) else crop_hw
    return img[:, :crop_h, :crop_w]


def crop_bl(img: npt.ArrayLike, crop_hw: Union[int, Tuple[int, int]]) -> np.ndarray:
    """Crop left bottom corner."""
    crop_h, crop_w = (crop_hw, crop_hw) if isinstance(crop_hw, int) else crop_hw
    return img[:, -crop_h:, :crop_w]


def crop_tr(img: npt.ArrayLike, crop_hw: Union[int, Tuple[int, int]]) -> np.ndarray:
    """Crop right top corner."""
    crop_h, crop_w = (crop_hw, crop_hw) if isinstance(crop_hw, int) else crop_hw
    return img[:, :crop_h, -crop_w:]


def crop_br(img: npt.ArrayLike, crop_hw: Union[int, Tuple[int, int]]) -> np.ndarray:
    """Crop right bottom corner."""
    crop_h, crop_w = (crop_hw, crop_hw) if isinstance(crop_hw, int) else crop_hw
    return img[:, -crop_h:, -crop_w:]


def crop_center(img: npt.ArrayLike, crop_hw: Union[int, Tuple[int, int]]) -> np.ndarray:
    """Crop from the center of the image."""
    crop_h, crop_w = (crop_hw, crop_hw) if isinstance(crop_hw, int) else crop_hw

    center_h = img.shape[1] // 2
    center_w = img.shape[2] // 2
    half_crop_h = crop_h // 2
    half_crop_w = crop_w // 2

    y_min = center_h - half_crop_h
    y_max = center_h + half_crop_h + crop_h % 2
    x_min = center_w - half_crop_w
    x_max = center_w + half_crop_w + crop_w % 2

    return img[:, y_min:y_max, x_min:x_max]


def get_random_crop_coords(
    height: int,
    width: int,
    crop_height: int,
    crop_width: int,
    h_start: float,
    w_start: float,
) -> Tuple[int, int, int, int]:
    """Crop from a random location in the image."""
    y1 = int((height - crop_height) * h_start)
    y2 = y1 + crop_height
    x1 = int((width - crop_width) * w_start)
    x2 = x1 + crop_width
    return x1, y1, x2, y2


def random_crop(
    img: npt.ArrayLike,
    crop_hw: Union[int, Tuple[int, int]],
    return_coordinates: bool = False,
) -> np.ndarray:
    """Crop from a random location in the image."""
    crop_h, crop_w = (crop_hw, crop_hw) if isinstance(crop_hw, int) else crop_hw
    height, width = img.shape[1:]
    h_start, w_start = np.random.uniform(), np.random.uniform()
    x1, y1, x2, y2 = get_random_crop_coords(height, width, crop_h, crop_w, h_start, w_start)
    if return_coordinates:
        return (img[y1:y2, x1:x2], (y1, y2, x1, x2))
    else:
        return img[y1:y2, x1:x2]


def get_xy_block_coords(image_shape: npt.ArrayLike, crop_hw: Union[int, Tuple[int, int]]) -> npt.ArrayLike:
    """Compute coordinates of non-overlapping image blocks of specified shape."""
    crop_h, crop_w = (crop_hw, crop_hw) if isinstance(crop_hw, int) else crop_hw
    height, width = image_shape[1:]

    block_coords = []
    for y in np.arange(0, height // crop_h) * crop_h:
        for x in np.arange(0, width // crop_w) * crop_w:
            block_coords.append((y, y + crop_h, x, x + crop_w))

    return np.asarray(block_coords)


def get_xy_block(image: npt.ArrayLike, tile_coords: List[int]) -> npt.ArrayLike:
    """Slice subvolume of 3D image by XY coordinates."""
    return image[:, tile_coords[0] : tile_coords[1], tile_coords[2] : tile_coords[3]]
