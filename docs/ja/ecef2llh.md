# ecef2llh.py

ECEF（earth-centered earth-fix）座標から緯度・経度・楕円体高（LLH: latitude, longitude, and ellipsoidal height）に変換します。

```bash
$ ecef2llh.py
ECEF to LLH conversion, QZS L6 Tool ver.x.x.x
Usage: /Users/sat/bin/ecef2llh.py x y z
```

例えば、ECEF座標 x=-3551876.829, y=3887786.860, z=3586946.387を変換すると、北緯34.4401061度、東経132.4147804度、楕円体高233.362メートルになります。

```bash
$ ecef2llh.py -3551876.829 3887786.860 3586946.387

34.4401061 132.4147804 233.362
```
