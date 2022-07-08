from tornado_swagger.setup import setup_swagger
from tornado import web, ioloop

import config
from handler.template_file_handler import TemplateFileHandler
from handler.template_handler import TemplatesHandler, TemplatesDetailHandler
from handler.images_handler import ImagesHandler

from utils import logger, get_project_path

root_path = get_project_path()
urlpatterns = [
    # 静态文件访问
    web.url(r'/templates/(.*)/(.*)', TemplateFileHandler, {"path": root_path + "/templates"}),
    # 获取model信息
    web.url(r'/templates/(.*)', TemplatesDetailHandler),
    web.url(r'/images', ImagesHandler),
    web.url(r'/templates', TemplatesHandler),
]
settings = dict(
    debug=True,
)

port = config.port
host = config.host


def start_server():
    setup_swagger(urlpatterns)
    app = web.Application(urlpatterns, **settings)
    app.listen(port)
    logger.info('Start forward proxy server on port {}'.format(port))
    logger.info(f'swagger doc url:http://127.0.0.1:{port}/api/doc#/')
    ioloop.IOLoop.current().start()
