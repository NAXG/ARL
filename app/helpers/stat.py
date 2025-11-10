from collections import Counter

from app import utils
from pymongo import UpdateOne


def extract_domain_prefixes(domains: list) -> list:
    """从域名中提取前缀部分，例如 api.dev.example.com -> api.dev"""
    prefixes = []
    for domain in domains:
        if not isinstance(domain, str):
            continue

        parts = domain.split('.')
        if len(parts) > 2:
            prefix = ".".join(parts[:-2])
            if prefix:
                prefixes.append(prefix)

    return prefixes


def update_domain_prefix_counts_bulk(domains: list):
    """批量提取前缀并为每条域名计数+1"""
    prefix_list = extract_domain_prefixes(domains)
    if not prefix_list:
        return

    operations = [
        UpdateOne({"prefix": prefix}, {"$inc": {"count": 1}}, upsert=True)
        for prefix in prefix_list
    ]

    # a redundant safety check.
    utils.conn_db('domain_prefix_stat').bulk_write(operations, ordered=False)


def bulk_update_domain_prefix_counts(prefix_counter: Counter):
    """根据前缀->次数的 Counter 更新统计表"""
    if not prefix_counter:
        return

    operations = [
        UpdateOne({"prefix": prefix}, {"$inc": {"count": count}}, upsert=True)
        for prefix, count in prefix_counter.items()
    ]

    utils.conn_db('domain_prefix_stat').bulk_write(operations, ordered=False)
