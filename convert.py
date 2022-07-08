import base64
import io
import json
import math
import os
import requests
import uuid
from io import BytesIO
from PIL import ImageFilter, Image, ImageDraw, ExifTags
from utils import get_project_path, logger

root_path = get_project_path()


def read_model(model_path):
    """
    :param model_path: 模板文件路径
    :return:
    """
    with open(model_path, 'r') as model:
        try:
            _config = json.load(model)
        except:
            _config = {}
    return _config


def add_white_edge(in_img, aspect):
    width, height = in_img.size  # 获取原图像的水平方向尺寸和垂直方向尺寸。

    if (height / width) == aspect:
        return in_img
    elif height / width > aspect:
        out_width = math.ceil(height / aspect)
        out_height = height
        bg_img = Image.new("RGB", (out_width, out_height), (255, 255, 255))
        bg_img.paste(in_img, (round((out_width - width) / 2), 0))
        return bg_img
    elif height / width < aspect:
        out_width = width
        out_height = math.ceil(width * aspect)
        bg_img: Image.Image = Image.new("RGB", (out_width, out_height), (255, 255, 255))
        bg_img.paste(in_img, (0, round((out_height - height) / 2)))
        return bg_img


def resize(img, width, height):
    """
    缩放图片
    :param img: 源图片
    :param width: 宽度
    :param height: 高度
    :return:
    """
    img = img.convert("RGBA")
    # ANTIALIAS 高质量
    img = img.resize((width, height), Image.ANTIALIAS)
    return img


def circle_corner(img, radii):
    """
    给图片生成圆角，在resize之后调用
    :param img: 原图片
    :param radii: 弧度
    :return:
    """
    logger.debug(f"生成圆角，弧度为{radii}")
    circle = Image.new('L', (radii * 2, radii * 2), 0)  # 创建黑色方形
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, radii * 2, radii * 2), fill=255)  # 黑色方形内切白色圆形

    img = img.convert("RGBA")
    w, h = img.size

    # 创建一个alpha层，存放四个圆角，使用透明度切除圆角外的图片
    alpha = Image.new('L', img.size, 255)
    alpha.paste(circle.crop((0, 0, radii, radii)), (0, 0))  # 左上角
    alpha.paste(circle.crop((radii, 0, radii * 2, radii)), (w - radii, 0))  # 右上角
    alpha.paste(circle.crop((radii, radii, radii * 2, radii * 2)), (w - radii, h - radii))  # 右下角
    alpha.paste(circle.crop((0, radii, radii, radii * 2)), (0, h - radii))  # 左下角
    img.putalpha(alpha)  # 白色区域透明可见，黑色区域不可见

    return img


def make_border(img, box, color, width, corner, radii):
    """
    添加边框
    :param img:
    :param box: 位置
    :param color: 边框颜色
    :param width: 边框宽度
    :param corner: 是否有圆角
    :param radii: 边框弧度，要与corner的一致
    :return:
    """
    logger.debug(f"生成边框,位置{box},颜色{color},宽度{width}")
    draw = ImageDraw.Draw(img)
    if corner:
        draw.rounded_rectangle(box, outline=color, width=width, radius=radii)
    else:
        draw.rounded_rectangle(box, outline=color, width=width)


def make_shadow(img, box, position, iterations, border, offset, shadow_color, corner, radii):
    """
    生成阴影效果
    :param img: 背景图
    :param box: 素材图片大小
    :param position: 图片位置
    :param iterations: 阴影迭代次数
    :param border: 阴影距离图片的距离
    :param offset: x,y偏移量
    :param shadow_color: 阴影颜色
    :param corner: 是否圆角
    :param radii: 阴影弧度
    :return:
    """
    # 计算阴影大小
    full_width = box[0] + abs(offset[0]) + 2 * border
    full_height = box[1] + abs(offset[1]) + 2 * border
    # 生成阴影背景透明图
    shadow_background = Image.new(img.mode, (full_width, full_height), "#ffffff00")
    shadow_left = border + max(offset[0], 0)  # if <0, push the rest of the image right
    shadow_top = border + max(offset[1], 0)  # if <0, push the rest of the image down

    # 生成阴影并加上圆角
    shadow_sprite = Image.new(img.mode, (box[0], box[1]), shadow_color)
    if corner:
        shadow_sprite = circle_corner(shadow_sprite, radii)
    # 合成阴影图
    shadow_background.paste(shadow_sprite, [shadow_left, shadow_top, shadow_left + box[0], shadow_top + box[1]])
    # 使用BLUR滤镜达成阴影效果，次数越多阴影越模糊
    for i in range(iterations):
        shadow_background = shadow_background.filter(ImageFilter.BLUR)
    _r, _g, _b, _a = shadow_background.split()

    # 将阴影图粘贴到背景图上
    img_left = border - min(offset[0], 0)
    img_top = border - min(offset[1], 0)
    img.paste(shadow_background, (position[0] + img_left, position[1] + img_top), mask=_a)
    return img


def open_seaweed_img(path):
    """
    从seaweed打开图片
    :param path:
    :return:
    """
    data = requests.get(path)
    tmp = BytesIO(data.content)
    img = Image.open(tmp)
    return img


def save_to_seaweed(img):
    """
    先保存到临时文件夹，上传完成之后删除
    :param img:
    :return:
    """
    img_uuid = str(uuid.uuid1()).replace('-', '')
    img_url = f"http://192.168.200.71:8888/pheasant/{img_uuid}.jpg"
    img_path = f'{root_path}/temp/{img_uuid}.png'
    img.save(img_path)

    files = [
        ('', (f'{img_uuid}.jpg', open(img_path, 'rb'), 'image/jpg'))
    ]
    try:
        response = requests.request("POST", img_url, headers={}, data={}, files=files)
        if response.status_code == 201:
            logger.info(f"生成图片:{img_url}")
            return [200, img_url]
    except:
        return [500, 'save to seaweed failed']
    finally:
        os.remove(img_path)


def convert(config, byte_file_list, urls):
    """
    合成具体图片
    :param urls: seaweed url
    :param config:
    :param byte_file_list: 字节图片
    :return: [status_code, msg]
    """
    # bg一般指background sp指sprite

    logger.debug("读取模板文件")
    bg_conf = config['background']  # background配置
    bg_path = root_path + '/' + bg_conf['path']  # bg图片路径
    bg_width = bg_conf['width']  # bg宽度
    bg_height = bg_conf['height']  # bg高度
    sp_conf = config['sprites']  # sprite配置
    count = sp_conf['count']  # sprite数量
    if count != len(urls):
        return [500, 'invalid sprites']

    # background = open_seaweed_img(bg_path)
    background = Image.open(bg_path)
    background = resize(background, bg_width, bg_height)

    for index, f in enumerate(sp_conf['list']):
        logger.debug(f"加载第{index + 1}张sprite")
        sprite = open_seaweed_img(urls[index]) if urls else Image.open(
            io.BytesIO(byte_file_list[f'sprite_{index + 1}'][0]['body']))
        sp_radii = f['radii']
        sp_width = f['width']
        sp_height = f['height']
        sp_border = f['border']['enable']
        sp_border_width = f['border']['width']
        sp_border_color = f['border']['color']
        sp_corner = f['corner']['enable']
        sp_shadow = f['shadow']['enable']
        sp_shadow_color = f['shadow']['shadow_color']
        sp_shadow_iterations = f['shadow']['iterations']
        sp_shadow_border = f['shadow']['border']
        sp_shadow_offset_x = f['shadow']['offset_x']
        sp_shadow_offset_y = f['shadow']['offset_y']
        sp_position = tuple(f['position'])

        hw_ratio = round(sp_height / sp_width, 2)
        # 根据模板调整图片大小
        sprite = add_white_edge(sprite, hw_ratio)
        resized_sprite = resize(sprite, sp_width, sp_height)
        if sp_shadow:
            background = make_shadow(background, [sp_width, sp_height], sp_position, sp_shadow_iterations,
                                     sp_shadow_border, [sp_shadow_offset_x, sp_shadow_offset_y],
                                     sp_shadow_color, sp_corner, sp_radii)

        # 生成圆角
        if sp_corner:
            cropped_sprite = circle_corner(resized_sprite, sp_radii)
            # 直接paste会把corner生成的透明部分覆盖掉背景图，使用alpha控制透明
            # 不过这样做会丢掉边框，所以要在paste之后再进行加边框的操作
            r, g, b, a = cropped_sprite.split()
            background.paste(resized_sprite, sp_position, mask=a)
        else:
            background.paste(resized_sprite, sp_position)

        if sp_border:
            make_border(background, sp_position, sp_border_color, sp_border_width, sp_corner, sp_radii)
    background = background.convert('RGB')
    # background.show()
    img_buffer = BytesIO()
    background.save(img_buffer, format='JPEG')
    byte_data = img_buffer.getvalue()
    base64_bytes = base64.b64encode(byte_data).decode('ascii')
    return [201, base64_bytes]
