from django import template
import re

register = template.Library()

@register.filter
def split_first(value, delimiter='-'):
    """
    将字符串按指定分隔符分割，并返回第一部分
    用于从策略名称中移除ID部分
    
    例如:
    "针锋相对 (Tit for Tat)-1749125402448" -> "针锋相对 (Tit for Tat)"
    """
    if not value:
        return value
    
    # 检查是否包含类似"-1234567890"格式的ID
    match = re.search(r'(-\d{10,})', value)
    if match:
        # 返回ID之前的部分
        return value[:match.start()]
    
    # 如果没有找到ID格式，则按指定分隔符分割
    parts = value.split(delimiter, 1)
    if len(parts) > 0:
        return parts[0].strip()
    return value 