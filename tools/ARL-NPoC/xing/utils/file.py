def load_file(path):
    with open(path, "r+", encoding="utf-8") as f:
        return f.readlines()


def append_file(path, msgs):
    with open(path, "a", encoding="utf-8") as f:
        for msg in msgs:
            f.write(f"{str(msg).strip()}\n")


def clear_empty(buf):
    """对数组删除空白符"""
    return [item.strip() for item in buf if item.strip()]
