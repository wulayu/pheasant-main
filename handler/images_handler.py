import json

from tornado_swagger.model import register_swagger_model
from convert import convert
from handler.base_handler import BaseRequestHandler


class ImagesHandler(BaseRequestHandler):

    async def post(self):
        """
        ---
        tags:
        - POST
        description: 应用模板生成图片
        summary: 生成图片
        produces:
        - application/json
        parameters:
        -   name: template_id
            type: string
        -   name: sprites
            type: array

        responses:
            201:
                description: 生成成功
                schema:
                    properties:
                        code:
                            type: string
                            default: 201
                        data:
                            type: string
                            default: base64
        """

        raw_info = self.request.body.decode('utf-8')
        info = json.loads(raw_info)
        template_id = info['template_id']
        model = self.load_template(template_id)
        if not model:
            return
        urls = info["sprites"]

        result = convert(model, None, urls)
        self.write({'code': result[0], 'data': str(result[1])})


