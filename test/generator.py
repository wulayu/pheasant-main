import json
import os
import time
from PIL import Image
from decimal import Decimal

source = '/Users/longen/jinanlongen/Hamster/output/rembg/'
base_source = '../templates/881/images/'
box_source = '../templates/881/'
out_path = '../output/'
box_a = ()
box_b = ()
source_dir = os.listdir(source)
source_dir.remove('.idea')
source_dir.sort()
total_time = 0
if not os.path.isdir(out_path):
    os.mkdir(out_path)

for index, file_name in enumerate(source_dir):
    time_start = time.time()
    base_img = Image.open(os.path.join(base_source, 'background.jpg'))

    with open(os.path.join(box_source, 'model.json'), 'r') as model:
        try:
            box_json = json.load(model)
        except:
            box_json = {}
    box_a = box_json['sprites']['list'][0]['position']
    box_b = box_json['sprites']['list'][1]['position']

    input_path_a = file_name
    x_a = input_path_a.rsplit(".", 1)
    if index + 1 == len(source_dir):
        input_path_b = input_path_a
    else:
        input_path_b = source_dir[index + 1]
    x_b = input_path_b.rsplit(".", 1)
    output_path = 'output_' + str(index) + '.png'

    tmp_img_a = Image.open(os.path.join(source, input_path_a))
    region_a = tmp_img_a
    region_a = region_a.resize((box_a[2] - box_a[0], box_a[3] - box_a[1]))
    r, g, b, a = region_a.split()
    base_img.paste(region_a, box_a, mask=a)

    tmp_img_b = Image.open(os.path.join(source, input_path_b))
    region_b = tmp_img_b
    region_b = region_b.resize((box_b[2] - box_b[0], box_b[3] - box_b[1]))
    r_b, g_b, b_b, a_b = region_b.split()
    base_img.paste(region_b, box_b, mask=a_b)

    base_img.save(os.path.join(out_path, output_path), format='png')
    # base_img.show()
    time_end = time.time()
    print(input_path_a)
    print(input_path_b)
    print(output_path)
    print(str(index + 1) + '/' + str(len(source_dir)))
    print(index + 1, ' time cost', Decimal(time_end - time_start).quantize(Decimal("0.00")), ' s', '\n')
    total_time += time_end - time_start
