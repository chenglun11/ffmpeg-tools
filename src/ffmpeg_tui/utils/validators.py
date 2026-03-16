import re

def validate_resolution(value: str) -> tuple[bool, str]:
    """验证分辨率格式 (如 '1920x1080')"""
    match = re.match(r"^(\d+)x(\d+)$", value)
    if not match:
        return False, "分辨率格式应为 宽x高，如 1920x1080"
    w, h = int(match.group(1)), int(match.group(2))
    if w <= 0 or h <= 0:
        return False, "分辨率必须大于 0"
    if w > 7680 or h > 4320:
        return False, "分辨率超出合理范围"
    return True, ""

def validate_bitrate(value: str) -> tuple[bool, str]:
    """验证码率格式 (如 '4000k', '5M')"""
    match = re.match(r"^(\d+)(k|K|m|M)?$", value)
    if not match:
        return False, "码率格式应为数字+单位，如 4000k 或 5M"
    return True, ""

def validate_framerate(value: float) -> tuple[bool, str]:
    """验证帧率"""
    if value <= 0:
        return False, "帧率必须大于 0"
    if value > 120:
        return False, "帧率超出合理范围 (最大 120)"
    return True, ""
