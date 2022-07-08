import os
import sys
import zipfile

from loguru import logger

logger.remove()
handler_id = logger.add(sys.stderr, level="INFO")


def get_project_path():
    """得到项目路径"""
    project_path = os.path.join(
        os.path.dirname(__file__),
    )
    return project_path


def zip_file(path):
    logger.debug(f'zip file from:{path}')
    start_dir = path  # 要压缩的文件夹路径
    file_news = start_dir + 'zips' + '.zip'  # 压缩后文件夹的名字

    z = zipfile.ZipFile(file_news, 'w', zipfile.ZIP_DEFLATED)
    for dir_path, dir_names, file_names in os.walk(start_dir):
        f_path = dir_path.replace(start_dir, '')  # 这一句很重要，不replace的话，就从根目录开始复制
        f_path = f_path and f_path + os.sep or ''  # 实现当前文件夹以及包含的所有文件的压缩
        for filename in file_names:
            z.write(os.path.join(dir_path, filename), f_path + filename)
    z.close()
    return file_news


def unzip_file(zip_src, dst_dir):
    logger.debug(f'unzip file to:{dst_dir}')

    r = zipfile.is_zipfile(zip_src)
    if r:
        fz = zipfile.ZipFile(zip_src, 'r')
        for file in fz.namelist():
            fz.extract(file, dst_dir)
        return True
    else:
        logger.error('this is not zip')
        return False
