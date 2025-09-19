from app import utils
from collections import Counter
from pymongo import UpdateOne

def update_domain_prefix_counts_bulk(domains: list):
    """
    从域名列表中批量提取前缀并更新计数
    """
    prefix_list = []
    for domain in domains:
        if not isinstance(domain, str):
            continue

        parts = domain.split('.')
        if len(parts) > 2:
            prefix = ".".join(parts[:-2])
            if prefix:
                prefix_list.append(prefix)

    if not prefix_list:
        return

    prefix_counts = Counter(prefix_list)

    operations = [
        UpdateOne({"prefix": prefix}, {"$inc": {"count": count}}, upsert=True)
        for prefix, count in prefix_counts.items()
    ]

    if operations:
        utils.conn_db('domain_prefix_stat').bulk_write(operations, ordered=False)
