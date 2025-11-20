import re
from flask_restx import Resource, reqparse, fields
from bson.objectid import ObjectId
from bson.errors import InvalidId
from datetime import datetime
from urllib.parse import quote
from flask import make_response
import time

from app.utils import conn_db as conn

__all__ = [
    # re-export namespaces for external importers
    'task_ns', 'domain_ns', 'site_ns', 'ip_ns', 'url_ns', 'user_ns', 'image_ns', 'cert_ns',
    'service_ns', 'fileleak_ns', 'export_ns', 'asset_scope_ns', 'asset_domain_ns', 'asset_ip_ns',
    'asset_site_ns', 'scheduler_ns', 'poc_ns', 'vuln_ns', 'batch_export_ns', 'policy_ns',
    'npoc_service_ns', 'task_fofa_ns', 'console_ns', 'cip_ns', 'fingerprint_ns', 'stat_finger_ns',
    'github_task_ns', 'github_result_ns', 'github_monitor_result_ns', 'github_scheduler_ns',
    'task_schedule_ns', 'nuclei_result_ns', 'wih_ns', 'asset_wih_ns',
]

base_query_fields = {
    'page': fields.Integer(description="当前页数", example=1),
    'size': fields.Integer(description="页面大小", example=10),
    'order': fields.String(description="排序字段", example='_id'),
}

# 只能用等号进行mongo查询的字段
EQUAL_FIELDS = ["task_id", "task_tag", "ip_type", "scope_id", "type"]


class ARLResource(Resource):
    def get_parser(self, model, location='json'):
        parser = reqparse.RequestParser(bundle_errors=True)
        for name in model:
            curr_field = model[name]

            parser.add_argument(name,
                                required=curr_field.required,
                                type=curr_field.format,
                                help=curr_field.description,
                                location=location)
        return parser

    def parse_args(self, model, location='json'):
        parser = self.get_parser(model, location)
        args = parser.parse_args()
        return args

    def build_db_query(self, args):
        query_args = {}
        for key in args:
            if key in base_query_fields:
                continue

            if key == '_id':
                if args[key]:
                    try:
                        query_args[key] = ObjectId(args[key])
                    except InvalidId:
                        continue

                continue

            if args[key] is None:
                continue

            if key.endswith("__dgt"):
                real_key = key.split('__dgt')[0]
                raw_value = query_args.get(real_key, {})
                raw_value.update({
                    "$gt": datetime.strptime(args[key],
                                             "%Y-%m-%d %H:%M:%S")
                })
                query_args[real_key] = raw_value

            elif key.endswith("__dlt"):
                real_key = key.split('__dlt')[0]
                raw_value = query_args.get(real_key, {})
                raw_value.update({
                    "$lt": datetime.strptime(args[key],
                                             "%Y-%m-%d %H:%M:%S")
                })
                query_args[real_key] = raw_value

            elif key.endswith("__neq"):
                real_key = key.split('__neq')[0]
                raw_value = {
                    "$ne": args[key]
                }
                query_args[real_key] = raw_value

            elif key.endswith("__not"):
                real_key = key.split('__not')[0]
                raw_value = {
                    "$not": re.compile(re.escape(args[key]))
                }
                query_args[real_key] = raw_value

            elif key.endswith("__gt") and isinstance(args[key], int):
                real_key = key.split('__gt')[0]
                raw_value = {
                    "$gt": args[key]
                }
                query_args[real_key] = raw_value
            elif key.endswith("__lt") and isinstance(args[key], int):
                real_key = key.split('__lt')[0]
                raw_value = {
                    "$lt": args[key]
                }
                query_args[real_key] = raw_value
            elif isinstance(args[key], str):
                if key in EQUAL_FIELDS:
                    query_args[key] = args[key]
                else:
                    query_args[key] = {
                        "$regex": re.escape(args[key]),
                        '$options': "i"
                    }
            else:
                query_args[key] = args[key]

        return query_args

    def build_return_items(self, data):
        items = []

        special_keys = ["_id", "save_date", "update_date"]

        for item in data:
            for key in item:
                if key in special_keys:
                    item[key] = str(item[key])

            items.append(item)

        return items

    def build_data(self, args=None, collection=None):

        default_field = self.get_default_field(args)
        page = default_field.get("page", 1)
        size = default_field.get("size", 10)
        orderby_list = default_field.get('order', [("_id", -1)])
        query = self.build_db_query(args)
        result = conn(collection).find(query).sort(orderby_list).skip(size * (page - 1)).limit(size)
        count = conn(collection).count_documents(query)
        items = self.build_return_items(result)

        special_keys = ["_id", "save_date", "update_date"]
        for key in query:
            if key in special_keys:
                query[key] = str(query[key])

            raw_value = query[key]
            if isinstance(raw_value, dict):
                if "$not" in raw_value:
                    if isinstance(raw_value["$not"], type(re.compile(""))):
                        raw_value["$not"] = raw_value["$not"].pattern

        data = {
            "page": page,
            "size": size,
            "total": count,
            "items": items,
            "query": query,
            "code": 200
        }
        return data

    '''
    取默认字段的值，并且删除
    '''

    def get_default_field(self, args):
        default_field_map = {
            "page": 1,
            "size": 10,
            "order": "-_id"
        }

        ret = default_field_map.copy()

        for x in default_field_map:
            if x in args and args[x]:
                ret[x] = args.pop(x)
                if x == "size":
                    if ret[x] <= 0:
                        ret[x] = 10
                    if ret[x] >= 100000:
                        ret[x] = 100000

                if x == "page":
                    if ret[x] <= 0:
                        ret[x] = 1

        orderby_list = []
        orderby_field = ret.get("order", "-_id")
        for field in orderby_field.split(","):
            field = field.strip()
            if field.startswith("-"):
                orderby_list.append((field.split("-")[1], -1))
            elif field.startswith("+"):
                orderby_list.append((field.split("+")[1], 1))
            else:
                orderby_list.append((field, 1))

        ret['order'] = orderby_list
        return ret

    def send_export_file(self, args, _type):
        _type_map_field_name = {
            "site": "site",
            "domain": "domain",
            "ip": "ip",
            "asset_site": "site",
            "asset_domain": "domain",
            "asset_ip": "ip",
            "asset_wih": "content",
            "url": "url",
            "cip": "cidr_ip",
            "wih": "content",
        }
        data = self.build_data(args=args, collection=_type)["items"]
        items_set = set()
        for item in data:
            filed_name = _type_map_field_name.get(_type, "")
            if filed_name and filed_name in item:
                if filed_name == "ip":
                    curr_ip = item[filed_name]
                    for port_info in item.get("port_info", []):
                        items_set.add(f"{curr_ip}:{port_info['port_id']}")
                else:
                    items_set.add(item[filed_name])

        return self.send_file(items_set, _type)

    # 表示从 给定集合中 导出相应的字段来
    def send_export_file_attr(self, args, collection, field):
        data = self.build_data(args=args, collection=collection)["items"]
        items_set = set()
        for item in data:
            if field in item:
                value = item[field]
                if isinstance(value, list):
                    items_set |= set(value)
                else:
                    items_set.add(value)

        return self.send_file(items_set, f"{collection}_{field}")

    def send_batch_export_file(self, task_id_list, _type):
        _type_map_field_name = {
            "site": "site",
            "domain": "domain",
            "ip": "ip",
            "url": "url",
            "cip": "cidr_ip",
            "wih": "content",
        }
        items_set = set()
        filed_name = _type_map_field_name.get(_type, "")

        for task_id in task_id_list:
            if not filed_name:
                continue
            if not task_id:
                continue
            query = {"task_id": task_id}
            items = conn(_type).distinct(filed_name, query)
            items_set |= set(items)

        return self.send_file(items_set, _type)

    def send_scope_batch_export_file(self, scope_id_list, _type):
        _type_map_field_name = {
            "asset_site": "site",
            "asset_domain": "domain",
            "asset_ip": "ip",
            "asset_wih": "content"
        }

        items_set = set()
        filed_name = _type_map_field_name.get(_type, "")

        for scope_id in scope_id_list:
            if not filed_name:
                continue
            if not scope_id:
                continue
            query = {"scope_id": scope_id}
            items = conn(_type).distinct(filed_name, query)
            items_set |= set(items)

        return self.send_file(items_set, _type)

    def send_file(self, items_set, _type):
        response = make_response("\r\n".join(items_set))
        filename = f"{_type}_{len(items_set)}_{int(time.time())}.txt"
        response.headers['Content-Type'] = 'application/octet-stream'
        response.headers["Access-Control-Expose-Headers"] = "Content-Disposition"
        response.headers["Content-Disposition"] = f"attachment; filename={quote(filename)}"
        return response


def get_arl_parser(model, location='args'):
    r = ARLResource()
    return r.get_parser(model, location)


from .task import ns as task_ns  # noqa: E402
from .domain import ns as domain_ns  # noqa: E402
from .site import ns as site_ns  # noqa: E402
from .ip import ns as ip_ns  # noqa: E402
from .url import ns as url_ns  # noqa: E402
from .user import ns as user_ns  # noqa: E402
from .image import ns as image_ns  # noqa: E402
from .cert import ns as cert_ns  # noqa: E402
from .service import ns as service_ns  # noqa: E402
from .fileleak import ns as fileleak_ns  # noqa: E402
from .export import ns as export_ns  # noqa: E402
from .assetScope import ns as asset_scope_ns  # noqa: E402
from .assetDomain import ns as asset_domain_ns  # noqa: E402
from .assetIP import ns as asset_ip_ns  # noqa: E402
from .assetSite import ns as asset_site_ns  # noqa: E402
from .scheduler import ns as scheduler_ns  # noqa: E402
from .poc import ns as poc_ns  # noqa: E402
from .vuln import ns as vuln_ns  # noqa: E402
from .batchExport import ns as batch_export_ns  # noqa: E402
from .policy import ns as policy_ns  # noqa: E402
from .npoc_service import ns as npoc_service_ns  # noqa: E402
from .taskFofa import ns as task_fofa_ns  # noqa: E402
from .console import ns as console_ns  # noqa: E402
from .cip import ns as cip_ns  # noqa: E402
from .fingerprint import ns as fingerprint_ns  # noqa: E402
from .stat_finger import ns as stat_finger_ns  # noqa: E402
from .github_task import ns as github_task_ns  # noqa: E402
from .github_result import ns as github_result_ns  # noqa: E402
from .github_monitor_result import ns as github_monitor_result_ns  # noqa: E402
from .github_scheduler import ns as github_scheduler_ns  # noqa: E402
from .task_schedule import ns as task_schedule_ns  # noqa: E402
from .nuclei_result import ns as nuclei_result_ns  # noqa: E402
from .wih import ns as wih_ns  # noqa: E402
from .assetWih import ns as asset_wih_ns  # noqa: E402
