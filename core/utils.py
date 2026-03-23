from datetime import date, timedelta

import numpy as np
import sxtwl

from core.constants import GAN, ZHI, JIEQI, LUNAR_MONTHS


def sanitize(obj):
    """numpy 型別轉 Python 原生，否則 JSON 序列化會炸"""
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize(v) for v in obj]
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


def solar_to_ganzhi(year: int, month: int, day: int, hour: int):
    """西曆轉干支、節氣、農曆月"""
    d = sxtwl.fromSolar(year, month, day)
    day_gz = GAN[d.getDayGZ().tg] + ZHI[d.getDayGZ().dz]

    hour_zhi_idx = ((hour + 1) // 2) % 12
    hour_tg_idx = (d.getDayGZ().tg * 2 + hour_zhi_idx) % 10
    hour_gz = GAN[hour_tg_idx] + ZHI[hour_zhi_idx]

    lunar_month_str = LUNAR_MONTHS[abs(d.getLunarMonth()) - 1]

    # 往前找最近的節氣（最多搜 45 天）
    jieqi = None
    base = date(year, month, day)
    for i in range(45):
        check_date = base - timedelta(days=i)
        check = sxtwl.fromSolar(check_date.year, check_date.month, check_date.day)
        if check.hasJieQi():
            jq_idx = check.getJieQi()
            if jq_idx < len(JIEQI):
                jieqi = JIEQI[jq_idx]
                break

    if not jieqi:
        raise ValueError("找不到對應節氣")

    return jieqi, lunar_month_str, day_gz, hour_gz
