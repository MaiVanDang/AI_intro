import re

def get_str_from_order_dict(order_dict: dict):
    result = ", ".join([f"{int(value)} {key}" for key, value in order_dict.items()])
    return result

def extract_session_id(session_str: str):
    match = re.search(r"/sessions/(.*?)/contexts/", session_str)
    if match:
        return match.group(1)
    return ""