"""通用 file-based cache — JSON 檔存 cache/ 目錄。

快取策略：
  - L1（永久）：本命盤 + 17 張分盤 + nakshatra + dasha + chara_dasha
                key = 出生資料 hash，永不過期
  - L2（年度）：流年行運，key = 本命 hash + target_year，一年有效

目錄結構：
  cache/vedic/
    natal/    {profile_key}_{hash}.json  或  {hash}.json
    transit/  {profile_key}_{hash}_{year}.json  或  {hash}_{year}.json

profile_key 是人類可讀的識別（main / friend-alice），純 hash 是後備格式。
"""

import hashlib
import json
import logging
import os
import re

import numpy as np

logger = logging.getLogger(__name__)

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(_PROJECT_ROOT, "cache", "vedic")
NATAL_DIR = os.path.join(CACHE_DIR, "natal")
TRANSIT_DIR = os.path.join(CACHE_DIR, "transit")

_SAFE_KEY = re.compile(r"[^a-zA-Z0-9_-]")


class _NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def _safe(profile_key: str | None) -> str:
    """把 profile_key 變成檔案系統安全字串（只允許英數和 _-），空值回空字串。"""
    if not profile_key:
        return ""
    return _SAFE_KEY.sub("-", profile_key.strip())[:32]


def _ensure(path: str):
    os.makedirs(path, exist_ok=True)


def natal_cache_key(year: int, month: int, day: int,
                    hour: int, minute: int,
                    lat: float, lng: float) -> str:
    """本命盤快取 key — 同一人的盤永遠一樣。"""
    raw = f"vedic-natal:{year}-{month}-{day}-{hour}-{minute}-{lat:.4f}-{lng:.4f}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def transit_cache_key(natal_key: str, target_year: int,
                      forecast_years: int) -> str:
    """流年快取 key — 同一人 + 同一年的行運。"""
    raw = f"vedic-transit:{natal_key}:{target_year}:{forecast_years}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def _natal_path(key: str, profile_key: str | None) -> str:
    """主對話傳了 profile_key 就帶人名前綴，沒有就退回純 hash。"""
    pk = _safe(profile_key)
    name = f"{pk}_{key}.json" if pk else f"{key}.json"
    return os.path.join(NATAL_DIR, name)


def _transit_path(key: str, profile_key: str | None,
                  target_year: int) -> str:
    pk = _safe(profile_key)
    name = f"{pk}_{key}_{target_year}.json" if pk else f"{key}_{target_year}.json"
    return os.path.join(TRANSIT_DIR, name)


def get_natal(key: str, profile_key: str | None = None) -> dict | None:
    """讀取本命盤快取。無快取或讀取失敗回傳 None。"""
    path = _natal_path(key, profile_key)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info("vedic cache HIT %s", os.path.basename(path))
        return data
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("vedic cache read error %s: %s", path, e)
        return None


def set_natal(key: str, data: dict, profile_key: str | None = None) -> None:
    """寫入本命盤快取（永久）。"""
    _ensure(NATAL_DIR)
    path = _natal_path(key, profile_key)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, cls=_NpEncoder)
        size = os.path.getsize(path)
        logger.info("vedic cache SET %s (%d bytes)", os.path.basename(path), size)
    except OSError as e:
        logger.warning("vedic cache write error %s: %s", path, e)


def get_transit(key: str, target_year: int,
                profile_key: str | None = None) -> dict | None:
    """讀取流年快取。無快取或讀取失敗回傳 None。"""
    path = _transit_path(key, profile_key, target_year)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info("vedic cache HIT %s", os.path.basename(path))
        return data
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("vedic cache read error %s: %s", path, e)
        return None


def set_transit(key: str, target_year: int, data: dict,
                profile_key: str | None = None) -> None:
    """寫入流年快取。"""
    _ensure(TRANSIT_DIR)
    path = _transit_path(key, profile_key, target_year)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, cls=_NpEncoder)
        size = os.path.getsize(path)
        logger.info("vedic cache SET %s (%d bytes)", os.path.basename(path), size)
    except OSError as e:
        logger.warning("vedic cache write error %s: %s", path, e)
