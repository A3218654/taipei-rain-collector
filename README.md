# 臺北市水利處雨量站即時資料收集

每 10 分鐘由 GitHub Actions 呼叫臺北市水利處雨量站即時資料 API
（data.taipei「臺北市水利處雨量站即時資料」），把各站當日累積雨量附加到 `raw/YYYY-MM.csv`。

- `rain_collector.py`：抓取一次 API 並附加新紀錄（以站碼＋記錄時間去重）。
- `rain_hourly.py`：把累積雨量換算成逐時雨量，輸出 `站名_日期_逐時.csv`。

```
python rain_hourly.py 2026-10-21 太平國小 北投國小
```

資料來源：臺北市政府工務局水利處，臺北市資料大平臺（data.taipei）開放資料。
