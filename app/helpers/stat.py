from app import utils

def update_domain_prefix_count(domain):
    """
    从域名中提取前缀并更新计数
    """
    parts = domain.split('.')
    # 域名由超过2部分组成时，才认为有前缀
    # 例如 a.com 没有前缀, www.a.com 有前缀 www
    if len(parts) > 2:
        prefix = ".".join(parts[:-2])
        # 使用 update_one 和 $inc 实现原子更新，如果前缀不存在则创建
        query = {"prefix": prefix}
        update = {"$inc": {"count": 1}}
        utils.conn_db('domain_prefix_stat').update_one(query, update, upsert=True)
