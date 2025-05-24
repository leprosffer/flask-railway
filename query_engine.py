def filter_data(data, conditions):
    if not conditions:
        return data
    return [item for item in data if all(str(item.get(k)) == str(v) for k, v in conditions.items())]

def project_fields(data, fields):
    if not fields:
        return data
    return [{k: item.get(k) for k in fields} for item in data]

def sort_data(data, sort_key, reverse=False):
    if not sort_key:
        return data
    return sorted(data, key=lambda x: x.get(sort_key), reverse=reverse)

def paginate_data(data, page=1, page_size=10):
    start = (page - 1) * page_size
    end = start + page_size
    return data[start:end]
