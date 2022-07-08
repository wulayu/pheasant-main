import json
import os
import urllib.parse
from typing import Optional, Awaitable
from tornado import web
from utils import logger, get_project_path


class BaseRequestHandler(web.RequestHandler):
    root_path = get_project_path()

    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    def err_result(self, status_code, msg):
        logger.error({'code': status_code, 'msg': msg})
        self.set_status(status_code)
        self.finish({'code': status_code, 'msg': msg})

    def load_template(self, template_id):
        try:
            template_id = urllib.parse.unquote(template_id)
            local_path = f'{self.root_path}/templates/{template_id}/model.json'
            with open(local_path, 'r') as model:
                _config = json.load(model)
                return _config
        except:
            config = None
            self.err_result(500, 'invalid template_id')
            return config

    def get_file_list(self):
        file_list = os.listdir(f'{self.root_path}/templates')
        if 'zips' in file_list:
            file_list.remove('zips')
        if '.DS_Store' in file_list:
            file_list.remove('.DS_Store')
        file_list.sort()
        return file_list
