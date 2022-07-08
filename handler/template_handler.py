from tornado_swagger.model import register_swagger_model
from tornado_swagger.parameter import register_swagger_parameter

from config import host, port
from convert import read_model

import os

import aiofiles
from loguru import logger

from handler.base_handler import BaseRequestHandler
from utils import zip_file, unzip_file


class TemplatesHandler(BaseRequestHandler):
    async def get(self):
        """
        ---
        tags:
        - GET
        description: 获取模板列表信息
        summary: 获取模板列表信息
        produces:
        - application/json
        parameters:
        -   in: page
            name: page
            type: integer
            required: true
        -   in: page_size
            name: page_size
            type: integer
            required: true
        responses:
            200:
              schema:
                $ref: '#/definitions/TemplatesGetModel'
        """
        all_file_list = self.get_file_list()

        page = int(self.get_query_argument('page', "1"))
        page_size = int(self.get_query_argument('page_size', "10"))
        start_index = (page - 1) * page_size
        end_index = page * page_size

        file_list = all_file_list[start_index: end_index]
        data = {
            "total": len(self.get_file_list()),
            "hits": len(file_list),
            "brief": []
        }

        for file in file_list:
            model = read_model(f'templates/{file}/model.json')
            brief = {
                "id": file,
                "thumbnail": f'http://{host}:{port}/' + model['thumbnail'],
                "background": {
                    "height": model['background']['height'],
                    "width": model['background']['width'],
                    "path": f'http://{host}:{port}/' + model['background']['path']}
            }
            data['brief'].append(brief)
        self.write({'code': 200, 'message': 'success', 'data': data})

    async def post(self):
        """
        ---
        tags:
        - POST
        description: 上传模板zip包
        summary: 上传模板
        produces:
        - application/json
        parameters:
        -   in: fromData
            name: zip
            type: file
        responses:
            201:
                schema:
                    $ref: '#/definitions/UploadModel'
            500:
                description: empty file
            501:
                description: not zip
        """

        files_meta = self.request.files
        if not files_meta:
            self.err_result(500, 'empty file')
        else:
            received = []
            rejected = []
            file_list = list(files_meta.keys())
            for file in file_list:
                filename = files_meta[file][0]["filename"]
                # 判断是否已存在
                file_list = os.listdir(f'{self.root_path}/templates')
                if file in file_list:
                    rejected.append(file)
                    continue
                # 压缩包存放路径
                zip_path = f"{self.root_path}/templates/zips/{filename}"

                # 根据id解压
                async with aiofiles.open(zip_path, "wb") as f:
                    await f.write(files_meta[file][0]["body"])
                    dst_dir = f"{self.root_path}/templates/"
                    result = unzip_file(zip_path, dst_dir)
                    if result:
                        # 删除zip包
                        os.remove(zip_path)
                        received.append(file)
                        self.write({'code': 200, 'message': 'success'})
                    else:
                        self.err_result(501, 'not zip')
                        return


class TemplatesDetailHandler(BaseRequestHandler):

    async def get(self, template_id):
        """
        ---
        tags:
        - GET
        description: 获取模板详细信息
        summary: 获取模板详细信息
        produces:
        - application/json
        parameters:
        -   in: type
            name: type
            type: string
            required: true
            description: brief返回摘要信息，zip返回压缩包
        responses:
            200:
                schema:
                    properties:
                        code:
                            type: integer
                            format: int64
                            default: 200
                        message:
                            type: string
                            default: 成功
                        data:
                            type: object
        """
        all_file_list = self.get_file_list()
        _type = self.get_query_argument('type')

        if template_id not in all_file_list:
            self.write({'code': 404, 'message': 'templates not found'})

        if _type == 'brief':

            for file in all_file_list:
                if file == template_id:
                    model = read_model(f'templates/{file}/model.json')
                    model['thumbnail'] = f'http://{host}:{port}/' + model['thumbnail']
                    model['background']['path'] = f'http://{host}:{port}/' + model['background']['path']
                    self.write({'code': 200, 'message': 'success', 'data': model})

        elif _type == 'zip':
            local_path = f'{self.root_path}/templates/{template_id}'
            file_list = os.listdir(f'{self.root_path}/templates')
            if template_id not in file_list:
                self.err_result(404, 'no such a templates')
            zip_path = zip_file(local_path)

            self.set_header('Content-Type', 'application/octet-stream')
            self.set_header('Content-Disposition', f'attachment; filename={template_id}.zip')
            with open(zip_path, 'rb') as f:
                while True:
                    data = f.read(4096)
                    if not data:
                        break
                    self.write(data)
            # 下载完成后删除
            os.remove(zip_path)
            logger.info(f'download {template_id}')
            self.write({'code': 200})


@register_swagger_model
class TemplatesGetModel:
    """
    ---
    type: object
    description: Post model representation
    properties:
        code:
            type: integer
            format: int64
            default: 200
        message:
            type: string
            default: 成功
        data:
            type: array
            description: 详见BriefModel
            items:
                $ref: '#/definitions/BriefModel'
    """


@register_swagger_model
class UploadModel:
    """
    ---
    type: object
    description: Post model representation
    properties:
        code:
            type: integer
            format: int64
            default: 200
        message:
            type: string
            default: 成功
        data:
            type: object
            description: 参考UploadResultModel
            items:
                $ref: '#/definitions/UploadResultModel'
    """


@register_swagger_model
class UploadResultModel:
    """
    ---
    type: object
    description: Post model representation
    properties:
        rejected:
            type: array
            description: 失败的
        received:
            type: array
            description: 成功的
    """


@register_swagger_model
class BriefModel:
    """
    ---
    type: object
    description: Post model representation
    properties:
        id:
            type: string
            format: int64
            description: 模板id
            default: flower_1
        thumbnail:
            type: string
            format: int64
            description: 缩略图
            default: http://192.168.200.71:8888/pheasant/thumbnail.jpg
        background:
            type: string
            format: int64
            description: 背景图
            default: http://192.168.200.71:8888/pheasant/background.jpg
    """


@register_swagger_parameter
class TemplateId:
    """
    ---
    name: template_id
    description: 模板id
    required: true
    type: string
    """
