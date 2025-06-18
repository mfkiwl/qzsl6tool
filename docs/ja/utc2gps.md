# utc2gps.py

UTC時刻をGPS時刻、GST（Galileo Standard Time）、BDT（BeiDou Standard Time）に変換します。

```bash
$ utc2gps.py
UTC to GNSS time conversion, QZS L6 Tool ver.x.x.x
Usage: /Users/sat/env/bin/utc2gps.py YYYY-MM-DD hh:mm:ss
Current GNSS time (week number, time of week):
GPS xxxx xxxxxx
GST xxxx xxxxxx
BDT xxxx xxxxxx
```

UTC時刻2022-11-30 12:52:37を与えた実行例は、次のとおりです。

```bash
utc2gps.py 2022-11-30 12:52:37

GPS 2238 305575
GST 1214 305570
BDT 882 305561
```

この結果は、

- GPS時刻では、週番号（WN: week number）が2238、週初めからの秒数（TOW: time of week）が305575、
- GSTでは、WNが1214、TOWが305570、
- BSTでは、WNが882、TOWが305561

であることを表しています。
