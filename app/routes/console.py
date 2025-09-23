from flask_restx import Namespace
from app.utils import get_logger, auth
from app import utils
from app.modules import ErrorMsg
from . import ARLResource

ns = Namespace('console', description="控制台信息")

logger = get_logger()


@ns.route('/info')
class ARLConsole(ARLResource):

    @auth
    def get(self):
        """
        控制台信息查看
        """

        data = {
            "device_info": utils.device_info()   # 包含 CPU 内存和磁盘信息
        }

        return utils.build_ret(ErrorMsg.Success, data)



