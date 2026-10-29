# coding: utf-8
# Mục đích: đọc ảnh chữ số chụp từ camera, đưa về 28x28, rồi xuất ra file .v
#           để nạp sẵn ảnh vào bộ nhớ, phục vụ mô phỏng testbench trên FPGA.
# Người thực hiện: Phan Kế Vĩnh Hưng

import os
import glob
import math
import argparse

import numpy as np
import cv2


def convert_to_binary(float_val, precision, only_dot=0):
    """Đổi một số thực sang chuỗi nhị phân dạng Qm.n.

    float_val: số thực cần đổi
    precision: số bit dành cho phần thập phân (phần sau dấu chấm)
    only_dot:  nếu khác 0 thì chỉ trả về phần thập phân
    """
    up = math.floor(float_val)
    down = float_val - up
    up_binary_str = "{:b}".format(up)

    # Nhân đôi liên tục để lấy lần lượt từng bit của phần thập phân
    p = precision
    start = down
    down_binary_str = ''
    while p > 0:
        if start * 2 >= 1:
            down_binary_str += '1'
            start = start * 2 - 1
        else:
            down_binary_str += '0'
            start = start * 2
        p -= 1

    if only_dot == 0:
        return up_binary_str + '.' + down_binary_str
    return down_binary_str


def convert_to_normalized_form(value, reduction=10, precision=12):
    """Chuẩn hoá giá trị về dạng dấu phẩy tĩnh, tách riêng dấu và phần nhị phân."""
    sign = 0
    ret = value
    if ret < 0:
        sign = 1
        ret = abs(ret)

    dec = ret / reduction
    bin = convert_to_binary(dec, precision, 1)
    return sign, dec, bin


def generate_test_image_memory_verilog(image, answer, precision, out_file, type):
    """Ghi từng pixel của ảnh ra file Verilog dưới dạng gán vào mảng storage."""
    out = open(out_file, "w")
    out.write("// Precision: {}\n".format(precision))
    out.write("// Image size: {}x{}\n".format(image.shape[0], image.shape[1]))
    out.write("// Answer: {}\n\n".format(answer))

    out.write("initial\n")
    out.write("begin\n")
    total = 0
    for i in range(image.shape[0]):
        for j in range(image.shape[1]):
            sign, dec, bin1 = convert_to_normalized_form(image[i][j].copy(), 1, precision - 1)
            # Ký tự dấu: '-' nếu âm, ngược lại để khoảng trắng
            sgn = '-' if sign == 1 else ' '
            if type == 'hex':
                hx = hex(int(bin1, 2))[2:].upper()
                out.write("\tstorage[{}] = {}{}'h{}; // {}\n".format(total, sgn, precision - 1, hx, image[i][j]))
            else:
                out.write("\tstorage[{}] = {}{}'b{}; // {}\n".format(total, sgn, precision - 1, bin1, image[i][j]))
            total += 1
    out.write("end\n")
    out.close()


def prepare_image(im_path):
    """Đọc ảnh, lấy phần trung tâm, chuyển sang ảnh xám rồi thu nhỏ về 28x28."""
    img = cv2.imread(im_path)

    # Lấy vùng trung tâm 224x224 của ảnh
    img = img[8:-8, 48:-48]

    # Chuyển sang ảnh xám theo công thức trọng số (ảnh OpenCV theo thứ tự BGR).
    # Mẫu số là 16 để phép chia dễ cài đặt trên FPGA bằng dịch bit.
    gray = np.zeros(img.shape[:2], dtype=np.uint16)
    gray[...] = (3 * img[:, :, 0].astype(np.uint16)
                 + 8 * img[:, :, 1].astype(np.uint16)
                 + 5 * img[:, :, 2].astype(np.uint16))
    gray //= 16

    # Thu nhỏ về 28x28: mỗi pixel mới là trung bình của một khối 8x8 pixel cũ
    output_image = np.zeros((28, 28), dtype=np.uint8)
    for i in range(28):
        for j in range(28):
            output_image[i, j] = int(gray[i * 8:(i + 1) * 8, j * 8:(j + 1) * 8].mean())

    return output_image


def get_image_set(path):
    """Đọc toàn bộ ảnh test, trả về danh sách ảnh đã chuẩn hoá và nhãn tương ứng."""
    expected_answ = []
    image_list = []
    files = glob.glob(path + 'dataset/test/*/*.png')
    for f in files:
        # Tên thư mục chứa ảnh chính là nhãn của ảnh đó
        answ = int(os.path.basename(os.path.dirname(f)))
        expected_answ.append(answ)
        image_list.append(prepare_image(f))

    image_list = np.expand_dims(image_list, axis=3)
    image_list = np.array(image_list, dtype=np.float32) / 256.
    return image_list, expected_answ


def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--use_image', type=int, default=0, help='Number of image from test set')
    parser.add_argument('--bp', type=int, default=10, help='Bit precision')
    opt = parser.parse_args()
    return opt


if __name__ == '__main__':
    args = parse_opt()

    ROOT_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + '/'
    images, answers = get_image_set(ROOT_PATH)

    # Kiểm tra và giới hạn lại chỉ số ảnh cho hợp lệ
    use_image = args.use_image
    if use_image < 0:
        use_image = 0
    if use_image >= len(answers):
        use_image = len(answers) - 1

    # Giới hạn số bit độ chính xác trong khoảng [4, 32]
    bp = args.bp
    if bp < 4:
        bp = 4
    if bp > 32:
        bp = 32

    print('Total images read: {}. Image number for testbench: {}'.format(len(images), use_image))
    print('Bit precision: {} (with sign: {})'.format(bp, bp + 1))

    out_path = ROOT_PATH + "verilog/initial_image_bitdepth_{}_img_number_{}_answ_{}.v".format(
        bp + 1, use_image, answers[use_image])
    generate_test_image_memory_verilog(images[use_image], answers[use_image], bp + 1, out_path, 'bin')
    print('Verilog generated in {}'.format(out_path))
