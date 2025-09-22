import subprocess
import shlex
import random
import string
import psutil
import os
import re
import sys
import hashlib
from celery.utils.log import get_task_logger
import colorlog
import logging
import dns.resolver
from tld import get_tld
from .conn import http_req as http_req, conn_db as conn_db
from .http import get_title as get_title, get_headers as get_headers
from .domain import (
    check_domain_black as check_domain_black,
    is_valid_domain as is_valid_domain,
    is_in_scope as is_in_scope,
    is_in_scopes as is_in_scopes,
    is_valid_fuzz_domain as is_valid_fuzz_domain,
)
from .ip import (
    is_vaild_ip_target as is_vaild_ip_target,
    not_in_black_ips as not_in_black_ips,
    get_ip_asn as get_ip_asn,
    get_ip_city as get_ip_city,
    get_ip_type as get_ip_type,
)
from .arl import arl_domain as arl_domain, get_asset_domain_by_id as get_asset_domain_by_id
from .time import curr_date as curr_date, time2date as time2date, curr_date_obj as curr_date_obj
from .url import (
    rm_similar_url as rm_similar_url,
    get_hostname as get_hostname,
    normal_url as normal_url,
    same_netloc as same_netloc,
    verify_cert as verify_cert,
    url_ext as url_ext,
)
from .cert import get_cert as get_cert
from .arlupdate import arl_update as arl_update
from .cdn import get_cdn_name_by_cname as get_cdn_name_by_cname, get_cdn_name_by_ip as get_cdn_name_by_ip
from .device import device_info as device_info
from .cron import check_cron as check_cron, check_cron_interval as check_cron_interval
from .query_loader import load_query_plugins as load_query_plugins

def load_file(path):
    with open(path, "r+", encoding="utf-8") as f:
        return f.readlines()


def exec_system(cmd, **kwargs):
    cmd = " ".join(cmd)
    timeout = 4 * 60 * 60

    if kwargs.get('timeout'):
        timeout = kwargs['timeout']
        kwargs.pop('timeout')

    completed = subprocess.run(shlex.split(cmd), timeout=timeout, check=False, close_fds=True, **kwargs)

    return completed


def check_output(cmd, **kwargs):
    cmd = " ".join(cmd)
    timeout = 4 * 60 * 60

    if kwargs.get('timeout'):
        timeout = kwargs.pop('timeout')

    if 'stdout' in kwargs:
        raise ValueError('stdout argument not allowed, it will be overridden.')

    output = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE, timeout=timeout, check=False,
               **kwargs).stdout
    return output


def random_choices(k=6):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=k))


def gen_md5(s):
    return hashlib.md5(s.encode()).hexdigest()


def init_logger():
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        fmt = '%(log_color)s[%(asctime)s] [%(levelname)s] '
              '[%(threadName)s] [%(filename)s:%(lineno)d] %(message)s', datefmt = "%Y-%m-%d %H:%M:%S"))

    logger = colorlog.getLogger('arlv2')

    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.propagate = False


def get_logger():
    if 'celery' in sys.argv[0]:
        task_logger = get_task_logger(__name__)
        return task_logger

    logger = logging.getLogger('arlv2')
    if not logger.handlers:
        init_logger()

    return logging.getLogger('arlv2')


def get_ip(domain, log_flag=True):
    domain = domain.strip()
    logger = get_logger()
    ips = []
    try:
        answers = dns.resolver.resolve(domain, 'A')
        for rdata in answers:
            if rdata.address == '0.0.0.1':
                continue
            ips.append(rdata.address)
    except dns.resolver.NXDOMAIN as e:
        if log_flag:
            logger.info(f"{domain} {e}")

    except Exception as e:
        if log_flag:
            logger.warning(f"{domain} {e}")

    return ips


def get_cname(domain, log_flag=True):
    logger = get_logger()
    cnames = []
    try:
        answers = dns.resolver.resolve(domain, 'CNAME')
        for rdata in answers:
            cnames.append(str(rdata.target).strip(".").lower())
    except dns.resolver.NoAnswer as e:
        if log_flag:
            logger.debug(e)
    except Exception as e:
        logger.warning(f"{domain} {e}")

    return cnames


def domain_parsed(domain, fail_silently=True):
    domain = domain.strip()
    try:
        res = get_tld(domain, fix_protocol=True,  as_object=True)
        item = {
            "subdomain": res.subdomain,
            "domain":res.domain,
            "fld": res.fld
        }
        return item
    except Exception as e:
        if not fail_silently:
            raise e


def get_fld(d):
    """获取域名的主域"""
    res = domain_parsed(d)
    if res:
        return res["fld"]


def gen_filename(site):
    filename = site.replace('://', '_')

    return re.sub(r'[^\w\-_\\. ]', '_', filename)


def build_ret(error, data):
    if isinstance(error, str):
        error = {
            "message": error,
            "code": 999,
        }

    ret = {}
    ret.update(error)
    ret["data"] = data
    msg = error["message"]

    if error["code"] != 200:
        for k in data:
            if k.endswith("id"):
                continue
            if not data[k]:
                continue
            if isinstance(data[k], str):
                msg += f" {k}:{data[k]}"

    ret["message"] = msg
    return ret


def kill_child_process(pid):
    logger = get_logger()
    parent = psutil.Process(pid)
    for child in parent.children(recursive=True):
        logger.info(f"kill child_process {child}")
        child.kill()


def exit_gracefully(signum, frame):
    logger = get_logger()
    logger.info(f'Receive signal {signum} frame {frame}')
    pid = os.getpid()
    kill_child_process(pid)
    parent = psutil.Process(pid)
    logger.info(f"kill self {parent}")
    parent.kill()


def truncate_string(s):
    if len(s) > 30:
        truncated_string = s[:30]
        return truncated_string + "..."
    else:
        return s


def is_valid_exclude_ports(exclude_ports):
    """
    检查 nmap 中的排除端口范围是否合法
    """
    port_pattern = r'(\d+(-\d+)?,?)+'

    match = re.fullmatch(port_pattern, exclude_ports)

    if match:
        parts = exclude_ports.split(',')
        for part in parts:
            if '-' in part:
                start, end = map(int, part.split('-'))
                if start > end or not (0 <= start <= 65535) or not (0 <= end <= 65535):
                    return False
            else:
                if not (0 <= int(part) <= 65535):
                    return False
        return True
    else:
        return False


from .user import user_login as user_login, user_login_header as user_login_header, auth as auth, user_logout as user_logout, change_pass as change_pass  # noqa: E402
from .push import message_push as message_push  # noqa: E402
from .fingerprint import parse_human_rule as parse_human_rule, transform_rule_map as transform_rule_map  # noqa: E402

