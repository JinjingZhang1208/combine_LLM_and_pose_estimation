import sys
from pathlib import Path
FILE = Path(__file__).absolute()
sys.path.append(FILE.parents[1].as_posix())  # add kapao/ to path
import pandas as pd
import torch
import yaml
from utils.torch_utils import select_device
from utils.general import check_img_size, scale_coords
from utils.datasets import LoadImages
from models.experimental import attempt_load
from val import run_nms, post_process_batch
import cv2
import os.path as osp
import sys
from pathlib import Path
import os
import glob
import time
import csv
import pandas as pd
import numpy as np
from scipy.spatial.distance import euclidean
n = 12  # Set this to the maximum number of point pairs you expect in one image

args = {
    'img_path': 'res/image.png',
    'bbox': True,
    'kp_bbox': False,
    'pose': True,
    'face': True,
    'color_pose': [255, 0, 255],
    'color_kp': [0, 255, 255],
    'line_thick': 2,
    'kp_size': 1,
    'kp_thick': 2,
    'data': '../data/coco-kp.yaml',
    'imgsz': 1280,
    'weights': '../data/scripts/kapao_l_coco.pt',
    'device': 'cpu',
    'conf_thres': 0.7,
    'iou_thres': 0.45,
    'no_kp_dets': True,
    'conf_thres_kp': 0.5,
    'conf_thres_kp_person': 0.2,
    'iou_thres_kp': 0.45,
    'overwrite_tol': 25,
    'scales': [1],
    'flips': [-1],
}

with open(args['data']) as f:
    data = yaml.safe_load(f)  # load data dict

# add inference settings to data dict
data['imgsz'] = args['imgsz']
data['conf_thres'] = args['conf_thres']
data['iou_thres'] = args['iou_thres']
data['use_kp_dets'] = not args['no_kp_dets']
data['conf_thres_kp'] = args['conf_thres_kp']
data['iou_thres_kp'] = args['iou_thres_kp']
data['conf_thres_kp_person'] = args['conf_thres_kp_person']
data['overwrite_tol'] = args['overwrite_tol']
data['scales'] = args['scales']
data['flips'] = [None if f == -1 else f for f in args['flips']]
data['count_fused'] = False

device = select_device(args['device'], batch_size=1)
print('Using device: {}'.format(device))

model = attempt_load(args['weights'], map_location=device)
stride = int(model.stride.max())  # model stride
imgsz = check_img_size(args['imgsz'], s=stride)  # check image size
image_files = glob.glob('scndata/*.png')
key=0
csv_path = 'pt_data.csv'


# for img_file in image_files:
#     points_list = []  # Reset the points list for the new image
#     if key & 0xFF == 27:  # Check for ESC key press
#         break
#     print(img_file, type(img_file))
#     args['img_path'] = img_file  # Set the image path to the current file
#     dataset = LoadImages(args['img_path'], img_size=imgsz, stride=stride, auto=True)
#     (_, img, im0, _) = next(iter(dataset))
#     img = torch.from_numpy(img).to(device)
#     img = img / 255.0  # 0 - 255 to 0.0 - 1.0
#     if len(img.shape) == 3:
#         img = img[None]  # expand for batch dim
#     out = model(img, augment=True, kp_flip=data['kp_flip'], scales=data['scales'], flips=data['flips'])[0]
#     person_dets, kp_dets = run_nms(data, out)
#     if args['bbox']:
#         try:
#             bboxes = scale_coords(img.shape[2:], person_dets[0][:, :4], im0.shape[:2]).round().cpu().numpy()
#             for x1, y1, x2, y2 in bboxes:
#                 cv2.rectangle(im0, (int(x1), int(y1)), (int(x2), int(y2)), args['color_pose'],
#                               thickness=args['line_thick'])
#         except:
#             print(1)
#     _, poses, _, _, _ = post_process_batch(data, img, [], [[im0.shape[:2]]], person_dets, kp_dets)
#
#     if args['pose']:
#         for i, pose in enumerate(poses):
#             if args['face']:
#                 for x, y, c in pose[data['kp_face']]:
#                     cv2.circle(im0, (int(x), int(y)), args['kp_size'], args['color_pose'], args['kp_thick'])
#             for seg in data['segments'].values():
#                 pt1 = (int(pose[seg[0], 0]), int(pose[seg[0], 1]))
#                 pt2 = (int(pose[seg[1], 0]), int(pose[seg[1], 1]))
#                 cv2.line(im0, pt1, pt2, args['color_pose'], args['line_thick'])
#                 print(pt1, pt2)
#                 points_list.extend([pt1[0], pt1[1], pt2[0], pt2[1]])
#
#             if data['use_kp_dets']:
#                 for x, y, c in pose:
#                     if c:
#                         cv2.circle(im0, (int(x), int(y)), args['kp_size'], args['color_kp'], args['kp_thick'])
#
#     if args['kp_bbox']:
#         bboxes = scale_coords(img.shape[2:], kp_dets[0][:, :4], im0.shape[:2]).round().cpu().numpy()
#         for x1, y1, x2, y2 in bboxes:
#             cv2.rectangle(im0, (int(x1), int(y1)), (int(x2), int(y2)), args['color_kp'],
#                           thickness=args['line_thick'])


df = pd.read_csv('pt_data.csv')
# Inside your loop

for img_file in image_files:
    points_list = []  # Reset the points list for the new image
    # ... rest of your code ...
    if key & 0xFF == 27:  # Check for ESC key press
        break
    print(img_file, type(img_file))
    args['img_path'] = img_file  # Set the image path to the current file
    dataset = LoadImages(args['img_path'], img_size=imgsz, stride=stride, auto=True)
    (_, img, im0, _) = next(iter(dataset))
    img = torch.from_numpy(img).to(device)
    img = img / 255.0  # 0 - 255 to 0.0 - 1.0
    if len(img.shape) == 3:
        img = img[None]  # expand for batch dim
    out = model(img, augment=True, kp_flip=data['kp_flip'], scales=data['scales'], flips=data['flips'])[0]
    person_dets, kp_dets = run_nms(data, out)
    if args['bbox']:
        try:
            bboxes = scale_coords(img.shape[2:], person_dets[0][:, :4], im0.shape[:2]).round().cpu().numpy()
            for x1, y1, x2, y2 in bboxes:
                cv2.rectangle(im0, (int(x1), int(y1)), (int(x2), int(y2)), args['color_pose'],
                              thickness=args['line_thick'])
        except:
            print("Not detect for this frame")
    _, poses, _, _, _ = post_process_batch(data, img, [], [[im0.shape[:2]]], person_dets, kp_dets)

    if args['pose']:
        for i, pose in enumerate(poses):
            if args['face']:
                for x, y, c in pose[data['kp_face']]:
                    cv2.circle(im0, (int(x), int(y)), args['kp_size'], args['color_pose'], args['kp_thick'])
            for seg in data['segments'].values():
                pt1 = (int(pose[seg[0], 0]), int(pose[seg[0], 1]))
                pt2 = (int(pose[seg[1], 0]), int(pose[seg[1], 1]))
                cv2.line(im0, pt1, pt2, args['color_pose'], args['line_thick'])
                points_list.append((pt1[0], pt1[1]))
                points_list.append((pt2[0], pt2[1]))

            if data['use_kp_dets']:
                for x, y, c in pose:
                    if c:
                        cv2.circle(im0, (int(x), int(y)), args['kp_size'], args['color_kp'], args['kp_thick'])

    if args['kp_bbox']:
        bboxes = scale_coords(img.shape[2:], kp_dets[0][:, :4], im0.shape[:2]).round().cpu().numpy()
        for x1, y1, x2, y2 in bboxes:
            cv2.rectangle(im0, (int(x1), int(y1)), (int(x2), int(y2)), args['color_kp'],
                          thickness=args['line_thick'])
    # ... rest of your code ...
    for idx, row in df.iterrows():
        # Extract the 12 pairs of points from the row
        row_points = [(row['pt1_x_{}'.format(i)], row['pt1_y_{}'.format(i)], row['pt2_x_{}'.format(i)], row['pt2_y_{}'.format(i)]) for i in range(12)]
        row_points = [point for pair in row_points for point in pair]
        try:
            row_points = [int(point) for point in row_points]
            row_points = [(row_points[i], row_points[i + 1]) for i in range(0, len(row_points), 2)]
            if any(map(lambda x: any(map(lambda y: np.isnan(y) or np.isinf(y), x)), points_list)):
                print(f"points_list contains NaN or inf values: {points_list}")
            if any(map(lambda x: any(map(lambda y: np.isnan(y) or np.isinf(y), x)), row_points)):
                print(f"row_points contains NaN or inf values: {row_points}")

            # Calculate the Euclidean distance between the image points and the row points
            dist = sum(euclidean(p1, p2) for p1, p2 in zip(points_list, row_points))

            # If the distance is 0, return the tag
            if dist == 0:
                print(f'\nMatch found with tag: {row["Poses"]}')
                break
        except:
            pass
        # Flatten row_points from list of tuples of tuples to list of tuples
        # row_points = [int(point) for pair in row_points for point in pair]
        # # Check for NaN or inf in points_list and row_points
        # if any(map(lambda x: any(map(lambda y: np.isnan(y) or np.isinf(y), x)), points_list)):
        #     print(f"points_list contains NaN or inf values: {points_list}")
        # if any(map(lambda x: any(map(lambda y: np.isnan(y) or np.isinf(y), x)), row_points)):
        #     print(f"row_points contains NaN or inf values: {row_points}")
        #
        # # Calculate the Euclidean distance between the image points and the row points
        # dist = sum(euclidean(p1, p2) for p1, p2 in zip(points_list, row_points))
        # print(dist)
        #
        # # If the distance is 0, return the tag
        # if dist == 0:
        #     print(f'Match found with tag: {row["Poses"]}')
        #     break
        cv2.imshow("show", im0)
        key = cv2.waitKey(500)

cv2.destroyWindow('show')  # close the window

