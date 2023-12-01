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

# Check if CSV file exists
if Path(csv_path).exists():
    # Read the existing CSV file and get the maximum tag value
    df = pd.read_csv(csv_path)
    df['tag'] = df['tag'].astype(int)
    tag = df['tag'].max() + 1  # Increment by 1 to serve as the starting point for the new tags
else:
    tag = 0

headers = ['tag'] + sum(
    [['pt1_x_' + str(i), 'pt1_y_' + str(i), 'pt2_x_' + str(i), 'pt2_y_' + str(i)] for i in range(n)], []) +['Poses']

with open('pt_data.csv', 'a', newline='') as csvfile:
    pt_writer = csv.writer(csvfile)
    if tag == 0:  # Write header only if the file is new
        pt_writer.writerow(headers)  # writing headers

    for img_file in image_files:
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
                print(1)
        _, poses, _, _, _ = post_process_batch(data, img, [], [[im0.shape[:2]]], person_dets, kp_dets)

        points_list = [tag]

        if args['pose']:
            for i, pose in enumerate(poses):
                if args['face']:
                    for x, y, c in pose[data['kp_face']]:
                        cv2.circle(im0, (int(x), int(y)), args['kp_size'], args['color_pose'], args['kp_thick'])
                for seg in data['segments'].values():
                    pt1 = (int(pose[seg[0], 0]), int(pose[seg[0], 1]))
                    pt2 = (int(pose[seg[1], 0]), int(pose[seg[1], 1]))
                    cv2.line(im0, pt1, pt2, args['color_pose'], args['line_thick'])
                    print(pt1, pt2)
                    points_list.extend([pt1[0], pt1[1], pt2[0], pt2[1]])

                if data['use_kp_dets']:
                    for x, y, c in pose:
                        if c:
                            cv2.circle(im0, (int(x), int(y)), args['kp_size'], args['color_kp'], args['kp_thick'])

        if args['kp_bbox']:
            bboxes = scale_coords(img.shape[2:], kp_dets[0][:, :4], im0.shape[:2]).round().cpu().numpy()
            for x1, y1, x2, y2 in bboxes:
                cv2.rectangle(im0, (int(x1), int(y1)), (int(x2), int(y2)), args['color_kp'],
                              thickness=args['line_thick'])
        cv2.imshow("show", im0)
        key = cv2.waitKey(500)
        pt_writer.writerow(points_list)  # Write the tag and all points to the CSV
        tag += 1  # Increment the tag value for the next image

    cv2.destroyWindow('show')  # close the window

