"""bebetter CLI - argparse 子命令分流到 actions.py 的核心邏輯

用法:
  uv run --directory cli python cli.py <subcommand> [args...]

子命令:
  natal, horary, bazi-compat, bazi-fortune,
  astro-natal, astro-compat, astro-transit,
  vedic-natal, vedic-transit, vedic-compat,
  geomancy, qizheng, qizheng-transit,
  mayan-natal, mayan-fortune, mayan-transit
"""
import argparse
import asyncio
import json
import sys

from actions import (
    natal, horary, bazi_compat, bazi_fortune,
    astro_compat, astro_transit, vedic_transit, vedic_compat,
    geomancy, qizheng, qizheng_transit,
    astro_natal, vedic_natal, vedic_reference,
    mayan_natal, mayan_fortune, mayan_transit,
)


def _run(coro):
    print(asyncio.run(coro))


def cmd_natal(a):
    _run(natal(a.year, a.month, a.day, a.hour, a.minute,
               a.lat, a.lng, a.address))


def cmd_horary(a):
    _run(horary(a.year, a.month, a.day, a.hour, a.minute,
                a.question, a.lat, a.lng, a.address))


def cmd_bazi_compat(a):
    _run(bazi_compat(a.pillars_a, a.pillars_b,
                     a.gender_a, a.gender_b,
                     a.birth_date_a, a.birth_date_b))


def cmd_bazi_fortune(a):
    _run(bazi_fortune(a.pillars, a.gender, a.birth_date,
                      a.target_year, a.forecast_years))


def cmd_astro_compat(a):
    _run(astro_compat(
        a.name_a, a.year_a, a.month_a, a.day_a, a.hour_a, a.minute_a,
        a.name_b, a.year_b, a.month_b, a.day_b, a.hour_b, a.minute_b,
        a.lat_a, a.lng_a, a.address_a,
        a.lat_b, a.lng_b, a.address_b,
        a.tz_a, a.tz_b,
    ))


def cmd_astro_transit(a):
    _run(astro_transit(a.year, a.month, a.day, a.hour, a.minute,
                       a.lat, a.lng, a.address, a.tz,
                       a.target_year, a.forecast_years))


def cmd_vedic_transit(a):
    _run(vedic_transit(a.year, a.month, a.day, a.hour, a.minute,
                       a.lat, a.lng, a.address, a.tz,
                       a.target_year, a.forecast_years,
                       a.profile_key, a.target_date))


def cmd_astro_natal(a):
    _run(astro_natal(a.year, a.month, a.day, a.hour, a.minute,
                     a.lat, a.lng, a.address))


def cmd_vedic_natal(a):
    _run(vedic_natal(a.year, a.month, a.day, a.hour, a.minute,
                     a.lat, a.lng, a.address))


def cmd_mayan_natal(a):
    _run(mayan_natal(a.year, a.month, a.day))


def cmd_mayan_fortune(a):
    _run(mayan_fortune(a.year, a.month, a.day,
                       a.target_year, a.forecast_years))


def cmd_mayan_transit(a):
    _run(mayan_transit(a.year, a.month, a.day, a.target_date))


def cmd_vedic_reference(a):
    _run(vedic_reference())


def cmd_vedic_compat(a):
    _run(vedic_compat(
        a.name_a, a.year_a, a.month_a, a.day_a, a.hour_a, a.minute_a,
        a.name_b, a.year_b, a.month_b, a.day_b, a.hour_b, a.minute_b,
        a.lat_a, a.lng_a, a.address_a,
        a.lat_b, a.lng_b, a.address_b,
        a.tz_a, a.tz_b,
    ))


def cmd_geomancy(a):
    mothers = json.loads(a.manual_mothers) if a.manual_mothers else None
    _run(geomancy(a.question, a.seed, mothers))


def cmd_qizheng(a):
    _run(qizheng(a.year, a.month, a.day, a.hour, a.minute,
                 a.lat, a.lng, a.address, a.tz))


def cmd_qizheng_transit(a):
    _run(qizheng_transit(a.year, a.month, a.day, a.hour, a.minute,
                         a.target_year, a.target_month,
                         a.lat, a.lng, a.address, a.tz))


def _add_birth(p, suffix=""):
    """加上一組出生時間參數。suffix 用 '-a' / '-b' 區分兩人,Python 端會自動轉成 year_a 等"""
    s = suffix
    p.add_argument(f"--year{s}", type=int, required=True)
    p.add_argument(f"--month{s}", type=int, required=True)
    p.add_argument(f"--day{s}", type=int, required=True)
    p.add_argument(f"--hour{s}", type=int, required=True)
    p.add_argument(f"--minute{s}", type=int, required=True)


def _add_location(p, suffix=""):
    """加上一組座標 / 地址 / 時區參數"""
    s = suffix
    p.add_argument(f"--lat{s}", type=float, default=None)
    p.add_argument(f"--lng{s}", type=float, default=None)
    p.add_argument(f"--address{s}", default=None)
    p.add_argument(f"--tz{s}", default="Asia/Taipei")


def build_parser():
    p = argparse.ArgumentParser(prog="bebetter")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("natal", help="全系統本命排盤")
    _add_birth(sp)
    sp.add_argument("--lat", type=float, default=None)
    sp.add_argument("--lng", type=float, default=None)
    sp.add_argument("--address", default=None)
    sp.set_defaults(func=cmd_natal)

    sp = sub.add_parser("horary", help="全系統問事")
    _add_birth(sp)
    sp.add_argument("--question", default=None)
    sp.add_argument("--lat", type=float, default=None)
    sp.add_argument("--lng", type=float, default=None)
    sp.add_argument("--address", default=None)
    sp.set_defaults(func=cmd_horary)

    sp = sub.add_parser("bazi-compat", help="八字合盤")
    sp.add_argument("--pillars-a", required=True)
    sp.add_argument("--pillars-b", required=True)
    sp.add_argument("--gender-a", default="男")
    sp.add_argument("--gender-b", default="男")
    sp.add_argument("--birth-date-a", default="")
    sp.add_argument("--birth-date-b", default="")
    sp.set_defaults(func=cmd_bazi_compat)

    sp = sub.add_parser("bazi-fortune", help="八字大運流年")
    sp.add_argument("--pillars", required=True)
    sp.add_argument("--gender", default="男")
    sp.add_argument("--birth-date", default="")
    sp.add_argument("--target-year", type=int, default=None)
    sp.add_argument("--forecast-years", type=int, default=10)
    sp.set_defaults(func=cmd_bazi_fortune)

    sp = sub.add_parser("astro-compat", help="西洋占星合盤")
    sp.add_argument("--name-a", required=True)
    sp.add_argument("--name-b", required=True)
    _add_birth(sp, "-a")
    _add_birth(sp, "-b")
    _add_location(sp, "-a")
    _add_location(sp, "-b")
    sp.set_defaults(func=cmd_astro_compat)

    sp = sub.add_parser("astro-transit", help="西洋占星流年")
    _add_birth(sp)
    _add_location(sp)
    sp.add_argument("--target-year", type=int, default=None)
    sp.add_argument("--forecast-years", type=int, default=1)
    sp.set_defaults(func=cmd_astro_transit)

    sp = sub.add_parser("vedic-transit", help="印度占星流年")
    _add_birth(sp)
    _add_location(sp)
    sp.add_argument("--target-year", type=int, default=None)
    sp.add_argument("--forecast-years", type=int, default=1)
    sp.add_argument("--profile-key", default=None,
                    help="快取檔肉眼識別字串(如 main / friend-alice)")
    sp.add_argument("--target-date", default=None,
                    help="YYYY-MM-DD,給了就走流日模式(忽略 target-year)")
    sp.set_defaults(func=cmd_vedic_transit)

    sp = sub.add_parser("astro-natal", help="西洋占星本命盤")
    _add_birth(sp)
    sp.add_argument("--lat", type=float, default=None)
    sp.add_argument("--lng", type=float, default=None)
    sp.add_argument("--address", default=None)
    sp.set_defaults(func=cmd_astro_natal)

    sp = sub.add_parser("vedic-natal", help="印度占星本命盤")
    _add_birth(sp)
    sp.add_argument("--lat", type=float, default=None)
    sp.add_argument("--lng", type=float, default=None)
    sp.add_argument("--address", default=None)
    sp.set_defaults(func=cmd_vedic_natal)

    sp = sub.add_parser("mayan-natal", help="瑪雅曆本命盤")
    sp.add_argument("--year", type=int, required=True)
    sp.add_argument("--month", type=int, required=True)
    sp.add_argument("--day", type=int, required=True)
    sp.set_defaults(func=cmd_mayan_natal)

    sp = sub.add_parser("mayan-fortune", help="瑪雅曆運勢")
    sp.add_argument("--year", type=int, required=True)
    sp.add_argument("--month", type=int, required=True)
    sp.add_argument("--day", type=int, required=True)
    sp.add_argument("--target-year", type=int, default=None)
    sp.add_argument("--forecast-years", type=int, default=10)
    sp.set_defaults(func=cmd_mayan_fortune)

    sp = sub.add_parser("mayan-transit", help="瑪雅曆當下能量")
    sp.add_argument("--year", type=int, required=True)
    sp.add_argument("--month", type=int, required=True)
    sp.add_argument("--day", type=int, required=True)
    sp.add_argument("--target-date", default=None, help="YYYY-MM-DD,預設今天")
    sp.set_defaults(func=cmd_mayan_transit)

    sp = sub.add_parser("vedic-reference", help="印度占星對照表(行星/星座/nakshatra 等)")
    sp.set_defaults(func=cmd_vedic_reference)

    sp = sub.add_parser("vedic-compat", help="印度占星婚配")
    sp.add_argument("--name-a", required=True)
    sp.add_argument("--name-b", required=True)
    _add_birth(sp, "-a")
    _add_birth(sp, "-b")
    _add_location(sp, "-a")
    _add_location(sp, "-b")
    sp.set_defaults(func=cmd_vedic_compat)

    sp = sub.add_parser("geomancy", help="地占問事")
    sp.add_argument("--question", default="")
    sp.add_argument("--seed", default=None)
    sp.add_argument("--manual-mothers", default=None,
                    help='JSON 字串,如 [[1,2,1,2],[2,1,2,1],...]')
    sp.set_defaults(func=cmd_geomancy)

    sp = sub.add_parser("qizheng", help="七政四餘本命盤")
    _add_birth(sp)
    _add_location(sp)
    sp.set_defaults(func=cmd_qizheng)

    sp = sub.add_parser("qizheng-transit", help="七政四餘流運盤")
    _add_birth(sp)
    sp.add_argument("--target-year", type=int, required=True)
    sp.add_argument("--target-month", type=int, default=None)
    _add_location(sp)
    sp.set_defaults(func=cmd_qizheng_transit)

    return p


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
