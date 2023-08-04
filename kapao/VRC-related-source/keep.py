import sys
from pathlib import Path

FILE = Path(__file__).absolute()
sys.path.append(FILE.parents[1].as_posix())  # add kapao/ to path
import cv2
import numpy as np
from mss import mss
import pygetwindow as gw
import torch
from pathlib import Path
import yaml
from utils.torch_utils import select_device
from utils.general import check_img_size, scale_coords
from utils.datasets import LoadImages
from models.experimental import attempt_load
from val import run_nms, post_process_batch
import time
from multiprocessing import Process, Queue
import os
import datetime
import glob
# Get the window
window = gw.getWindowsWithTitle('VRChat')[0]

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
# Other settings...

device = select_device(args['device'], batch_size=1)
model = attempt_load(args['weights'], map_location=device)
stride = int(model.stride.max())  # model stride
imgsz = check_img_size(args['imgsz'], s=stride)  # check image size
# Create a queue for the buffer
buffer = Queue(maxsize=10)  # Set maxsize to your desired buffer size
image_files = glob.glob('scnwdata/*.png')

def capture_screenshots(buffer_img, buffer_original_img):
    # This function runs in a separate process and constantly captures screenshots
    sct = mss()
    monitor = {"top": window.top, "left": window.left, "width": window.width, "height": window.height}
    count = 0
    while True:
        # Capture the defined part of the screen
        time.sleep(1 / 60)  # Add a delay of 0.1 seconds
        screenshot = sct.grab(monitor)
        # Convert the screenshot to a numpy array
        img1 = np.array(screenshot)

        # Create a unique filename using the current timestamp
        # Save the image to the defined directory
        # Convert the screenshot to a numpy array and reshape to fit model input
        im0 = np.array(screenshot)
        img = cv2.cvtColor(im0, cv2.COLOR_RGBA2RGB)  # Change color format to RGB
        img = cv2.resize(img, (imgsz, imgsz))  # Resize image to fit model input
        img = img.transpose((2, 0, 1))  # Change shape from (height, width, channel) to (channel, height, width)
        img = torch.from_numpy(img).float().to(device)  # Convert to torch tensor and move to device
        img /= 255.0  # Normalize pixel values (0-255 to 0-1)
        if len(img.shape) == 3:
            img = img[None]  # expand for batch dim
        # img = img.unsqueeze(0)  # Add a dimension to fit model input (BxCxHxW)
        # img = torch.from_numpy(img).to(device)
        if not buffer_img.full():
            if count == 240:
                count = 0
            if count == 0:
                buffer_img.put(img)
                count += 1
                filename = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
                directory = "./scnwdata"
                # Save the image to the defined directory
                cv2.imwrite(os.path.join(directory, filename + '.png'), img1)
        else:
            print("Buffer for img is full, dropping frame.")

        if not buffer_original_img.full():
            buffer_original_img.put(im0)  # im0 is the original screenshot, you also add it to the buffer
        else:
            print("Buffer for original_img is full, dropping frame.")

        count += 1


def process_images(buffer_img, result_queue):
    # This function runs in a separate process and gets screenshots from the buffer to process
    while True:
        # if not buffer_img.empty():
        #     img = buffer_img.get()  # you get the original image as well
        #
        #     # Print out the shape of img
        #     # Transpose and transform img
        #     # Squeeze to remove the batch dimension and then transpose
        #     # img_np = img.squeeze(0).cpu().numpy().transpose((1, 2, 0))
        #     # im0 = np.array(img_np)
        #     im0=img
        #     # Run the model on the screenshot...
        #     out = model(img, augment=True, kp_flip=data['kp_flip'], scales=data['scales'], flips=data['flips'])[0]
        #     person_dets, kp_dets = run_nms(data, out)
        #     print(person_dets[0],kp_dets)
        #     # bboxes, poses, _, _, _ = post_process_batch(data, img, [], [[im0.shape[:2]]], person_dets, kp_dets)
        #     if args['bbox']:
        #         if person_dets[0].shape[0] > 0:  # if there are any detections
        #             bboxes = scale_coords(img.shape[2:], person_dets[0][:, :4], im0.shape[:2]).round().cpu().numpy()
        #         else:
        #             print("No objects detected in the image.")
        #             bboxes = np.array([])  # or however you want to handle this case
        #             for x1, y1, x2, y2 in bboxes:
        #                 cv2.rectangle(im0, (int(x1), int(y1)), (int(x2), int(y2)), args['color_pose'],
        #                               thickness=args['line_thick'])
        #                 print(int(x1), int(y1)), (int(x2), int(y2))
        #
        #
        #     _, poses, _, _, _ = post_process_batch(data, img, [], [[im0.shape[:2]]], person_dets, kp_dets)
        #
        #     if args['pose']:
        #         for pose in poses:
        #             if args['face']:
        #                 for x, y, c in pose[data['kp_face']]:
        #                     cv2.circle(im0, (int(x), int(y)), args['kp_size'], args['color_pose'], args['kp_thick'])
        #             for seg in data['segments'].values():
        #                 pt1 = (int(pose[seg[0], 0]), int(pose[seg[0], 1]))
        #                 pt2 = (int(pose[seg[1], 0]), int(pose[seg[1], 1]))
        #                 cv2.line(im0, pt1, pt2, args['color_pose'], args['line_thick'])
        #                 print(pt1, pt2)
        #             if data['use_kp_dets']:
        #                 for x, y, c in pose:
        #                     if c:
        #                         cv2.circle(im0, (int(x), int(y)), args['kp_size'], args['color_kp'], args['kp_thick'])
        #
        #     if args['kp_bbox']:
        #         try:
        #             bboxes = scale_coords(img.shape[2:], kp_dets[0][:, :4], im0.shape[:2]).round().cpu().numpy()
        #             for x1, y1, x2, y2 in bboxes:
        #                 cv2.rectangle(im0, (int(x1), int(y1)), (int(x2), int(y2)), args['color_kp'],
        #                               thickness=args['line_thick'])
        #                 print(int(x1), int(y1)), (int(x2), int(y2))
        #
        #         except:
        #             print(1)
        for img_file in image_files:
            print(img_file, type(img_file))
            args['img_path'] = img_file  # Set the image path to the current file

            # Avoid being too fast, might not capture image changes

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
                        print(int(x1), int(y1)), (int(x2), int(y2))
                except:
                    print(1)

            _, poses, _, _, _ = post_process_batch(data, img, [], [[im0.shape[:2]]], person_dets, kp_dets)

            if args['pose']:
                for pose in poses:
                    if args['face']:
                        for x, y, c in pose[data['kp_face']]:
                            cv2.circle(im0, (int(x), int(y)), args['kp_size'], args['color_pose'], args['kp_thick'])
                    for seg in data['segments'].values():
                        pt1 = (int(pose[seg[0], 0]), int(pose[seg[0], 1]))
                        pt2 = (int(pose[seg[1], 0]), int(pose[seg[1], 1]))
                        cv2.line(im0, pt1, pt2, args['color_pose'], args['line_thick'])
                        print(pt1, pt2)
                    if data['use_kp_dets']:
                        for x, y, c in pose:
                            if c:
                                cv2.circle(im0, (int(x), int(y)), args['kp_size'], args['color_kp'], args['kp_thick'])

            if args['kp_bbox']:
                bboxes = scale_coords(img.shape[2:], kp_dets[0][:, :4], im0.shape[:2]).round().cpu().numpy()
                for x1, y1, x2, y2 in bboxes:
                    cv2.rectangle(im0, (int(x1), int(y1)), (int(x2), int(y2)), args['color_kp'],
                                  thickness=args['line_thick'])
                    print(int(x1), int(y1)), (int(x2), int(y2))
            result_queue.put((im0))  # put the processed image and the original image into the queue

        # if not buffer_original_img.empty():
        #     original_img = buffer_original_img.get()  # you get the original image as well
        #     # Display the output
        #     # original_img_np = original_img.squeeze(0).cpu().numpy().transpose((1, 2, 0))
        #     # original_img0 = np.array(original_img_np)
        #     resultOrg_queue.put((original_img))
        #
        #
        #     # rest of your code that processes the model output and displays it...
        #     # Display the output
        # Continue with your existing code that processes the output and displays it...


def process_original_images(buffer_original_img, resultOrg_queue):
    # This function runs in a separate process and gets original screenshots from the buffer to process
    while True:
        if not buffer_original_img.empty():
            original_img = buffer_original_img.get()  # you get the original image as well

            # Rest of your code that processes the original image and displays it...
            # Continue with your existing code that processes the original image and displays it...
            resultOrg_queue.put((original_img))


if __name__ == '__main__':
    buffer_img = Queue(maxsize=10)  # Buffer for img
    buffer_original_img = Queue(maxsize=10)  # Buffer for original_img

    result_queue = Queue()
    resultOrg_queue = Queue()

    capture_process = Process(target=capture_screenshots, args=(buffer_img, buffer_original_img))
    # To this
    process_process = Process(target=process_images, args=(buffer_img, result_queue))
    process_original_process = Process(target=process_original_images, args=(buffer_original_img, resultOrg_queue))

    capture_process.start()
    process_process.start()
    process_original_process.start()
    key = 0
    while key & 0xFF != 27:
        if not result_queue.empty():
            im0 = result_queue.get()
            original_img = cv2.resize(im0, (int(original_img.shape[1]), int(original_img.shape[0])))  # scales down the image by 50%
            cv2.imshow('Output', original_img)

        if cv2.waitKey(25) & 0xFF == 27:
            cv2.destroyAllWindows()
            break

        if not resultOrg_queue.empty():
            original_img = resultOrg_queue.get()
            original_img = cv2.resize(original_img, (int(original_img.shape[1] * 0.5), int(original_img.shape[0] * 0.5)))  # scales down the image by 50%
            cv2.imshow('Original', original_img)  # showing the original image
            # im0 = (im0 * 255).astype(np.uint8)
            # print(im0)
            # img = buffer.get()
            # print(img)
            # cv2.imshow('Output', im0)
        if cv2.waitKey(25) & 0xFF == 27:
            cv2.destroyAllWindows()
            break
    capture_process.join()
    process_process.join()
    process_original_process.join()
