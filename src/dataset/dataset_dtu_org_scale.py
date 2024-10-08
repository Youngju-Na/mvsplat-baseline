import json
import os
from dataclasses import dataclass
from functools import cached_property
from io import BytesIO
from pathlib import Path
from typing import Literal

import torch
import os, re
import numpy as np
import cv2
import torchvision.transforms as tf
from einops import rearrange, repeat
from jaxtyping import Float, UInt8
from PIL import Image
from torch import Tensor
from torch.utils.data import IterableDataset
from termcolor import colored

from ..geometry.projection import get_fov
from .dataset import DatasetCfgCommon
from .shims.augmentation_shim import apply_augmentation_shim
from .shims.crop_shim import apply_crop_shim
from .types import Stage
from .view_sampler import ViewSampler
import random

from .scene_transform import get_boundingbox
from torchvision.transforms.functional import resize
from torchvision.transforms.functional import pil_to_tensor
from torchvision.transforms import InterpolationMode
from torchvision import transforms as T


def read_pfm(filename):
    file = open(filename, 'rb')
    color = None
    width = None
    height = None
    scale = None
    endian = None

    header = file.readline().decode('utf-8').rstrip()
    if header == 'PF':
        color = True
    elif header == 'Pf':
        color = False
    else:
        raise Exception('Not a PFM file.')

    dim_match = re.match(r'^(\d+)\s(\d+)\s$', file.readline().decode('utf-8'))
    if dim_match:
        width, height = map(int, dim_match.groups())
    else:
        raise Exception('Malformed PFM header.')

    scale = float(file.readline().rstrip())
    if scale < 0:  # little-endian
        endian = '<'
        scale = -scale
    else:
        endian = '>'  # big-endian

    data = np.fromfile(file, endian + 'f')
    shape = (height, width, 3) if color else (height, width)

    data = np.reshape(data, shape)
    data = np.flipud(data)
    file.close()
    return data, scale


def load_K_Rt_from_P(filename, P=None):
    if P is None:
        lines = open(filename).read().splitlines()
        if len(lines) == 4:
            lines = lines[1:]
        lines = [[x[0], x[1], x[2], x[3]] for x in (x.split(" ") for x in lines)]
        P = np.asarray(lines).astype(np.float32).squeeze()

    out = cv2.decomposeProjectionMatrix(P)
    K = out[0]
    R = out[1]
    t = out[2]

    K = K / K[2, 2]
    intrinsics = np.eye(4)
    intrinsics[:3, :3] = K

    pose = np.eye(4, dtype=np.float32)
    pose[:3, :3] = R.transpose()
    pose[:3, 3] = (t[:3] / t[3])[:, 0]

    return intrinsics, pose


@dataclass
class DatasetDTUCfg(DatasetCfgCommon):
    name: Literal['dtu']
    roots: list[Path]
    baseline_epsilon: float
    max_fov: float
    make_baseline_1: bool
    augment: bool
    pair_filepath: str
    split_filepath: list[Path]
    n_views: int
    view_selection_type: Literal['random', 'best']
    test_ref_views: list[int]
    use_test_ref_views_as_src: bool


class DatasetDTU(IterableDataset):
    cfg: DatasetDTUCfg
    stage: Stage
    view_sampler: ViewSampler

    to_tensor: tf.ToTensor 
    chunks: list[Path] #* List of paths to chunks.
    near: float = 0.1
    far: float = 1000.0

    def __init__(
        self,
        cfg: DatasetDTUCfg,
        stage: Stage,
        view_sampler: ViewSampler,
    ) -> None:
        super().__init__()
        self.cfg = cfg
        self.stage = stage
        self.view_sampler = view_sampler
        self.to_tensor = tf.ToTensor()

        self.pair_filepath = self.cfg.pair_filepath
        self.split_filepath = self.cfg.split_filepath
        self.num_all_imgs = 49
        
        
        print(colored("loading all scenes together", 'red'))
        for splitpath in self.cfg.split_filepath:
                # Load the root's index.
                with (splitpath / self.data_stage).with_suffix('.txt').open("r") as f:
                    self.scans = [line.rstrip() for line in f.readlines()]
                    
        if self.cfg.overfit_to_scene is not None:
            self.scans = [self.cfg.overfit_to_scene]
        
        
        self.all_intrinsics = []  # the cam info of the whole scene
        self.all_extrinsics = []
        self.all_near_fars = []
        
        self.chunks, self.ref_src_pairs = self.build_metas()  # load ref-srcs view pairs info of the scene
        
        
        self.allview_ids = [i for i in range(self.num_all_imgs)]
        self.load_cam_info()
        self.build_remap()
        self.define_transforms()
        self.to_tensor = tf.ToTensor()

    
    def shuffle(self, lst: list) -> list:
        indices = torch.randperm(len(lst))
        return [lst[x] for x in indices]

    def __iter__(self):
        # Chunks must be shuffled here (not inside __init__) for validation to show
        # random chunks.
        if self.stage in ("train", "val"):
            self.chunks = self.shuffle(self.chunks)

        # When testing, the data loaders alternate chunks.
        worker_info = torch.utils.data.get_worker_info()
        if self.stage == "test" and worker_info is not None:
            self.chunks = [
                chunk
                for chunk_index, chunk in enumerate(self.chunks)
                if chunk_index % worker_info.num_workers == worker_info.id
            ]

        #* iterate over all chunks
        for idx, meta in enumerate(self.chunks):
            # Load the chunk.
            scan, light_idx, ref_view, src_views = meta
            
            if self.stage == 'train':
                view_ids = [ref_view] + src_views[:self.cfg.n_views - 1]
            else:
                view_ids = [ref_view] + src_views[:self.cfg.n_views]
                
            w2c_ref = self.all_extrinsics[self.remap[ref_view]]
            w2c_ref_inv = np.linalg.inv(w2c_ref)

            imgs, depths_h, depths_mvs_h = [], [], []
            intrinsics, w2cs, near_fars = [], [], []
            
            #* each scene
            proj_matrices = []
            for i, vid in enumerate(view_ids):
                # NOTE that the id in image file names is from 1 to 49 (not 0~48)
                img_filename = os.path.join(str(self.cfg.roots[0]),
                                            f'Rectified/{scan}_train/rect_{vid + 1:03d}_{light_idx}_r5000.png')
                depth_filename = os.path.join(str(self.cfg.roots[0]),
                                            f'Depths_raw/{scan}/depth_map_{vid:04d}.pfm')
                
                img = Image.open(img_filename) 
                img = self.transform(img)
                imgs += [img]
                
                index_mat = self.remap[vid]
                near_fars.append(self.all_near_fars[index_mat])
                intrinsics.append(self.all_intrinsics[index_mat])
                w2cs.append(self.all_extrinsics[index_mat]) # @ w2c_ref_inv) #* reference view to source view
                # w2cs.append(self.all_extrinsics[index_mat])
                
                if os.path.exists(depth_filename):
                    depth_h = self.read_depth(depth_filename)
                    depths_h += [depth_h]
                    

            # scale_mat, scale_factor = self.cal_scale_mat(img_hw=[self.cfg.image_shape[0], self.cfg.image_shape[1]],
            #                                          intrinsics=intrinsics, extrinsics=w2cs,
            #                                          near_fars=near_fars, factor=1.1)
            # new_near_fars = []
            # new_w2cs = []
            # new_c2ws = []
            # new_depths_h = []

            # for i, (intrinsic, extrinsic, depth) in enumerate(zip(intrinsics, w2cs, depths_h)):
            
            #     P = intrinsic @ extrinsic @ scale_mat # perspective matrix scaled by scale_mat
            #     P = P[:3, :4]
            #     c2w = load_K_Rt_from_P(None, P)[1] #* camera to world

            #     w2c = np.linalg.inv(c2w)
            #     new_w2cs.append(w2c)
            #     new_c2ws.append(c2w)
                
            #     camera_o = c2w[:3, 3] #* camera origin
            #     dist = np.sqrt(np.sum(camera_o ** 2))
            #     near = dist - 1 if dist > 1 else 0.1
            #     far = dist + 1
            #     new_near_fars.append([0.95 * near, 1.05 * far])
            #     new_depths_h.append(depth * scale_factor)
            
            imgs = torch.stack(imgs)
            depths_h = np.stack(depths_h)
            
            
            intrinsics, w2cs, near_fars = np.stack(intrinsics), np.stack(w2cs), np.stack(near_fars)
            start_idx = 0
            
            # to tensor
            intrinsics = torch.from_numpy(intrinsics.astype(np.float32)).float()
            w2cs = torch.from_numpy(w2cs.astype(np.float32)).float()
            # c2ws = torch.from_numpy(c2ws.astype(np.float32)).float()
            c2ws = w2cs.inverse()
            near_fars = torch.from_numpy(near_fars.astype(np.float32)).float()
            depths_h = torch.from_numpy(depths_h.astype(np.float32)).float()
            
            
            # context_indices, target_indices = np.array([i for i in range(len(src_views))]), np.array([0]) 
            context_indices, target_indices = np.array([i for i in range(self.cfg.view_sampler.num_context_views)]), np.array([i for i in range(self.cfg.view_sampler.num_context_views, len(view_ids))])
            context_images, target_images = imgs[context_indices], imgs[target_indices]
            
            # Skip the example if the images don't have the right shape.
            context_image_invalid = context_images.shape[1:] != (3, self.cfg.image_shape[0], self.cfg.image_shape[1])
            target_image_invalid = target_images.shape[1:] != (3, self.cfg.image_shape[0], self.cfg.image_shape[1])
            if context_image_invalid or target_image_invalid:
                print(
                    f"Skipped bad example {scan}. Context shape was "
                    f"{context_images.shape} and target shape was "
                    f"{target_images.shape}."
                )
                continue
            
            # Resize the world to make the baseline 1.
            context_extrinsics = c2ws[context_indices]
            if context_extrinsics.shape[0] == 2 and self.cfg.make_baseline_1:
                a, b = context_extrinsics[:, :3, 3]
                scale = (a - b).norm()
                if scale < self.cfg.baseline_epsilon:
                    print(
                        f"Skipped {scan} because of insufficient baseline "
                        f"{scale:.6f}"
                    )
                    continue
                c2ws[:, :3, 3] /= scale
            else:
                scale = 1

            example = {
                "context": {
                    "extrinsics": c2ws[context_indices], #* B x 4 x 4
                    "intrinsics": intrinsics[context_indices][..., :3, :3], #* B x 3 x 3
                    "image": context_images, #* B x 3 x H x W
                    "depth": depths_h[context_indices], #* B x H x W
                    # "near": self.get_bound("near", len(context_indices)) / scale,
                    # "far": self.get_bound("far", len(context_indices)) / scale,
                    "near": near_fars[context_indices][:, 0], #* B
                    "far": near_fars[context_indices][:, 1], #* B
                    "index": context_indices,
                },
                "target": {
                    "extrinsics": c2ws[target_indices],
                    "intrinsics": intrinsics[target_indices][..., :3, :3],
                    "image": target_images,
                    "depth": depths_h[target_indices],
                    # "near": self.get_bound("near", len(target_indices)) / scale,
                    # "far": self.get_bound("far", len(target_indices)) / scale,
                    "near": near_fars[target_indices][:, 0],
                    "far": near_fars[target_indices][:, 1],
                    "index": target_indices,
                },
                "scene": scan, #* string for scene name
                "context_indices": context_indices, #* indices of the context views
                "target_indices": target_indices, #* indices of the target views
                "view_ids": view_ids, #* indices of the views
            }
            if self.stage == "train" and self.cfg.augment:
                example = apply_augmentation_shim(example)
            yield apply_crop_shim(example, tuple(self.cfg.image_shape))

    
    def convert_poses(
        self,
        poses: Float[Tensor, "batch 18"],
    ) -> tuple[
        Float[Tensor, "batch 4 4"],  # extrinsics
        Float[Tensor, "batch 3 3"],  # intrinsics
    ]:
        b, _ = poses.shape

        # Convert the intrinsics to a 3x3 normalized K matrix.
        intrinsics = torch.eye(3, dtype=torch.float32)
        intrinsics = repeat(intrinsics, "h w -> b h w", b=b).clone()
        fx, fy, cx, cy = poses[:, :4].T
        intrinsics[:, 0, 0] = fx
        intrinsics[:, 1, 1] = fy
        intrinsics[:, 0, 2] = cx
        intrinsics[:, 1, 2] = cy

        # Convert the extrinsics to a 4x4 OpenCV-style W2C matrix.
        w2c = repeat(torch.eye(4, dtype=torch.float32), "h w -> b h w", b=b).clone()
        w2c[:, :3] = rearrange(poses[:, 6:], "b (h w) -> b h w", h=3, w=4)
        return w2c.inverse(), intrinsics

    def convert_images(
        self,
        images: list[UInt8[Tensor, "..."]],
    ) -> Float[Tensor, "batch 3 height width"]:
        torch_images = []
        for image in images:
            image = Image.open(BytesIO(image.numpy().tobytes()))
            torch_images.append(self.to_tensor(image))
        return torch.stack(torch_images)

    def get_bound(
        self,
        bound: Literal["near", "far"],
        num_views: int,
    ) -> Float[Tensor, " view"]:
        value = torch.tensor(getattr(self, bound), dtype=torch.float32)
        return repeat(value, "-> v", v=num_views)

    @property
    def data_stage(self) -> Stage:
        if self.cfg.overfit_to_scene is not None:
            return "test"
        if self.stage == "val":
            return "test"
        return self.stage

    @cached_property
    def index(self) -> dict[str, Path]:
        merged_index = {}
        data_stages = [self.data_stage]
        if self.cfg.overfit_to_scene is not None:
            data_stages = ("test", "train")
        for data_stage in data_stages:
            for root in self.cfg.roots:
                # Load the root's index.
                with (root / data_stage / "index.json").open("r") as f:
                    index = json.load(f)
                index = {k: Path(root / data_stage / v) for k, v in index.items()}

                # The constituent datasets should have unique keys.
                assert not (set(merged_index.keys()) & set(index.keys()))

                # Merge the root's index into the main index.
                merged_index = {**merged_index, **index}
        return merged_index
    
    def build_metas(self):
        """
        This function build metas 
        Returns:
            _type_:
        """
        
        metas = []
        ref_src_pairs = {} # referece view와 source view의 pair를 만든다.
        light_idxs = [3] if 'train' not in self.stage else range(7)

        with open(self.pair_filepath) as f:
            num_viewpoint = int(f.readline())
            # viewpoints (49)
            for _ in range(num_viewpoint):
                ref_view = int(f.readline().rstrip())
                src_views = [int(x) for x in f.readline().rstrip().split()[1::2]]

                ref_src_pairs[ref_view] = src_views

        for light_idx in light_idxs:
            for scan in self.scans:
                with open(self.pair_filepath) as f:
                    num_viewpoint = int(f.readline())
                    # viewpoints (49)
                    for _ in range(num_viewpoint):
                        ref_view = int(f.readline().rstrip())
                        src_views = [int(x) for x in f.readline().rstrip().split()[1::2]]
                        #* implement random pair selection
                        if self.cfg.view_selection_type == 'random':
                            indices = [i for i in range(49) if i != ref_view]
                            src_views = random.sample(indices, self.cfg.n_views-1)
                        elif self.cfg.view_selection_type == 'best':
                            pass
                        else:
                            raise NotImplementedError
                        
                        # ! only for validation
                        if self.stage != 'train' and len(self.cfg.test_ref_views) > 0:
                            if ref_view not in self.cfg.test_ref_views:
                                continue
                            
                            if self.cfg.use_test_ref_views_as_src: #* use the test_ref_views as src views without ref_view
                                src_views = [ x for x in self.cfg.test_ref_views if x != ref_view]
                                    
                        metas += [(scan, light_idx, ref_view, src_views)] # scan, light_idx, ref_view, src_views

        return metas, ref_src_pairs

    def load_cam_info(self):
        for vid in range(self.num_all_imgs):
            proj_mat_filename = os.path.join(str(self.cfg.roots[0]),
                                             f'Cameras/train/{vid:08d}_cam.txt')
            intrinsic, extrinsic, near_far = self.read_cam_file(proj_mat_filename)
            
            if self.cfg.image_shape[0] == 512 and self.cfg.image_shape[1] == 640:
                intrinsic[:2] *= 4
            # intrinsic[:2] *= 4  # * the provided intrinsics is 4x downsampled, now keep the same scale with image
            
            #TODO: normalize intrinsic by dividing first row with image width and second row with image height
            
            scale_x = self.cfg.image_shape[1] / self.cfg.original_image_shape[1]
            scale_y = self.cfg.image_shape[0] / self.cfg.original_image_shape[0]
            
            intrinsic[0, 0] *= scale_x
            intrinsic[1, 1] *= scale_y
            
            intrinsic[:1] /= self.cfg.image_shape[1]  #* the width of the image
            intrinsic[1:2] /= self.cfg.image_shape[0]   #* the height of the image
            
            # near far values should be scaled according to the intrinsic values
            # near_far[0] /= np.max(self.cfg.image_shape)
            # near_far[1] /= np.max(self.cfg.image_shape)
            
            #TODO: manually change near to 2.125 and far to 4.525 which has the shape []
            near_far[0] = 2.125
            near_far[1] = 4.525
            
            #TODO: manually change the extrinsic values to have the shape 
            scale_factor = 1.0 / 200
            extrinsic[:3, 3] *= scale_factor
            
            self.all_intrinsics.append(intrinsic)
            self.all_extrinsics.append(extrinsic)
            self.all_near_fars.append(near_far)
        
        self.all_intrinsics_debug = self.all_intrinsics.copy()
        self.all_extrinsics_debug = self.all_extrinsics.copy()
    
    
    def read_cam_file(self, filename):
        """
        Load camera file e.g., 00000000_cam.txt
        """
        with open(filename) as f:
            lines = [line.rstrip() for line in f.readlines()]
        
        # extrinsics: line [1,5), 4x4 matrix
        extrinsics = np.fromstring(' '.join(lines[1:5]), dtype=np.float32, sep=' ')
        extrinsics = extrinsics.reshape((4, 4))
        
        # TODO: check the validity of the camera space
        
        # intrinsics: line [7-10), 3x3 matrix
        intrinsics = np.fromstring(' '.join(lines[7:10]), dtype=np.float32, sep=' ')
        intrinsics = intrinsics.reshape((3, 3))
        # depth_min & depth_interval: line 11
        depth_min = float(lines[11].split()[0])
        depth_max = depth_min + float(lines[11].split()[1]) * 192
        
        self.depth_min = depth_min
        self.depth_interval = float(lines[11].split()[1]) * 1.06
        intrinsics_ = np.float32(np.diag([1, 1, 1, 1]))
        intrinsics_[:3, :3] = intrinsics

        return intrinsics_, extrinsics, [depth_min, depth_max]
    
    def read_depth(self, filename):
        depth_h = np.array(read_pfm(filename)[0], dtype=np.float32)  # (1200, 1600)
        depth_h = cv2.resize(depth_h, None, fx=0.5, fy=0.5,
                             interpolation=cv2.INTER_NEAREST)  # (600, 800)
        depth_h = depth_h[44:556, 80:720]  # (512, 640)
        
        # scale down 4x
        depth_h = cv2.resize(depth_h, None, fx=0.25, fy=0.25, interpolation=cv2.INTER_NEAREST) # (128, 160)
        
        return depth_h
    
    def cal_scale_mat(self, img_hw, intrinsics, extrinsics, near_fars, factor=1.):
        center, radius, _ = get_boundingbox(img_hw, intrinsics, extrinsics, near_fars)

        radius = radius * factor
        scale_mat = np.diag([radius, radius, radius, 1.0])
        scale_mat[:3, 3] = center.cpu().numpy()
        scale_mat = scale_mat.astype(np.float32)

        return scale_mat, 1. / radius.cpu().numpy()
    
    def build_remap(self):
        self.remap = np.zeros(np.max(self.allview_ids) + 1).astype('int')
        for i, item in enumerate(self.allview_ids):
            self.remap[item] = i
            
    def define_transforms(self):
        self.transform = T.Compose([T.ToTensor(), T.Resize((self.cfg.image_shape[0], self.cfg.image_shape[1]))])        
    
    
    def __len__(self) -> int:
        # return len(self.index.keys())
        return len(self.chunks)
