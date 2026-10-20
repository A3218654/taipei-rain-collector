"""把 raw/ 收集到的當日累積雨量換算成逐時雨量，輸出成和 CODiS 檔案相同的格式。

用法：
    python rain_hourly.py 2026-10-20                 # 所有雨量站
    python rain_hourly.py 2026-10-20 太平國小 北投國小  # 指定站名

輸出到上一層資料夾（降雨資料分析），檔名「站名_日期_逐時.csv」。
第 h 時（01–24）的雨量 = h:00 的累積值 − (h−1):00 的累積值；00:00 視為 0。
整點前 10 分鐘內沒有紀錄、或差值為負時，該小時標 "--"（缺測）。
"""
import csv
import datetime
import pathlib
import sys

BASE = pathlib.Path(__file__).resolve().parent
RAW = BASE / "raw"
OUT = BASE.parent
TOLERANCE = datetime.timedelta(minutes=10)


def load(day):
    """回傳 {站名: [(記錄時間, 累積雨量), ...]}，只取 day 當天與隔天 00:00 的紀錄。"""
    series = {}
    for path in sorted(RAW.glob("*.csv")):
        with open(path, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                t = datetime.datetime.strptime(r["recTime"], "%Y%m%d%H%M")
                if day <= t.date() <= day + datetime.timedelta(days=1):
                    series.setdefault(r["stationName"], {})[t] = float(r["rain"])
    return {k: sorted(v.items()) for k, v in series.items()}


def acc_at(points, end, day_start):
    """end 時刻的累積雨量：取 [end−10分, end] 內最後一筆；end 為當日 00:00 時為 0。"""
    if end == day_start:
        return 0.0
    cand = [(t, v) for t, v in points if end - TOLERANCE <= t <= end]
    if not cand:
        return None
    if end.date() != day_start.date():
        # 隔日 00:00：若該筆已歸零（小於前一日最後一筆），改用前一日最後一筆
        same = [v for t, v in cand if t.date() == day_start.date()]
        nxt = [v for t, v in cand if t.date() != day_start.date()]
        if nxt and (not same or nxt[-1] >= same[-1]):
            return nxt[-1]
        return same[-1] if same else None
    return cand[-1][1]


def hourly(points, day):
    start = datetime.datetime.combine(day, datetime.time(0, 0))
    rows = []
    for h in range(1, 25):
        a0 = acc_at(points, start + datetime.timedelta(hours=h - 1), start)
        a1 = acc_at(points, start + datetime.timedelta(hours=h), start)
        if a0 is None or a1 is None or a1 < a0:
            rows.append((f"{h:02d}", "--"))
        else:
            rows.append((f"{h:02d}", f"{a1 - a0:.1f}"))
    return rows


def main(argv):
    day = datetime.date.fromisoformat(argv[1])
    wanted = set(argv[2:])
    for name, points in load(day).items():
        if wanted and name not in wanted:
            continue
        lines = [["測站", "觀測時間(hour)", "降水量(mm)"], ["測站", "ObsTime", "Precp"]]
        lines += [[name, h, v] for h, v in hourly(points, day)]
        text = "\n".join(",".join(f'"{x}"' for x in line) for line in lines)
        out = OUT / f"{name}_{day}_逐時.csv"
        out.write_bytes(("﻿" + text).encode("utf-8"))
        missing = sum(1 for line in lines[2:] if line[2] == "--")
        print(f"{out.name}  缺測 {missing}/24 小時")


if __name__ == "__main__":
    main(sys.argv)
