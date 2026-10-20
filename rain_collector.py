"""抓取臺北市水利處雨量站即時資料，附加到 raw/YYYY-MM.csv。

建議每 10 分鐘執行一次（工作排程器）。API 只提供「目前」的當日累積雨量，
沒抓到的時段事後無法補回。
"""
import csv
import datetime
import json
import pathlib
import urllib.request

URL = "https://wic.gov.taipei/OpenData/API/Rain/Get?stationNo=&loginId=open_rain&dataKey=85452C1D"
BASE = pathlib.Path(__file__).resolve().parent
RAW = BASE / "raw"
FIELDS = ["fetchTime", "stationNo", "stationName", "recTime", "rain"]
TW = datetime.timezone(datetime.timedelta(hours=8))  # 臺灣時間；在 UTC 的雲端主機上執行也一致


def log(msg):
    print(msg)
    with open(BASE / "collector.log", "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now(TW):%Y-%m-%d %H:%M:%S} {msg}\n")


def main():
    now = datetime.datetime.now(TW)
    try:
        with urllib.request.urlopen(URL, timeout=60) as r:
            data = json.loads(r.read().decode("utf-8-sig"))["data"]
    except Exception as e:  # 網路或 API 異常時記錄後結束，下次排程再抓
        log(f"ERROR {e!r}")
        return 1

    RAW.mkdir(exist_ok=True)
    path = RAW / f"{now:%Y-%m}.csv"
    seen = set()
    if path.exists():
        with open(path, encoding="utf-8-sig", newline="") as f:
            seen = {(r["stationNo"], r["recTime"]) for r in csv.DictReader(f)}

    new = [d for d in data if (d["stationNo"], d["recTime"]) not in seen]
    write_header = not path.exists()
    with open(path, "a", encoding="utf-8-sig" if write_header else "utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if write_header:
            w.writeheader()
        for d in new:
            w.writerow({"fetchTime": f"{now:%Y%m%d%H%M}", "stationNo": d["stationNo"],
                        "stationName": d["stationName"], "recTime": d["recTime"], "rain": d["rain"]})
    log(f"OK {len(data)} stations, {len(new)} new rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
