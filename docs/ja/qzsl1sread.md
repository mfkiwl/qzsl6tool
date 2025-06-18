# qzsl1sread.py

このプログラムは、みちびきL1S形式データを標準入力またはファイルから読み取り、その内容を標準出力に出力します。

``--help``オプションで、受け付けるオプションを表示します。

```bash
$ qzsl1sread.py --help
usage: qzsl1sread.py [-h] [-c] [-t TRACE] [file ...]

Quasi-zenith satellite (QZS) L1S message read, QZS L6 Tool ver.x.x.x

positional arguments:
  file                  L1S file(s) obtained from the QZS archive, https://sys.qzss.go.jp/dod/archives/slas.html

options:
  -h, --help            show this help message and exit
  -c, --color           apply ANSI color escape sequences even for non-terminal.
  -t TRACE, --trace TRACE show display verbosely: 1=subtype detail, 2=subtype and bit image.
```

ファイル名が与えられなければ、標準入力から読み取ります。入力形式は、みちびき公式ページの[SLASアーカイブ](https://sys.qzss.go.jp/dod/en/archives/slas.html)と同様です。最初に、1バイト（8ビット）のPRN（pseudo random noise）番号の後、32バイト（250ビット、残りはゼロパディング）のデータが続きます。

端末出力に対しては、ANSIエスケープ・シーケンスによりカラー表示します。端末出力のリダイレクトを行うと、エスケープ・シーケンスを出力しません。リダイレクトを利用すれば、カラー表示をオフにできます（``qzsll1sread.py < qzss_file.l1s | cat``）。一方、``less``や``lv``などのページャー上でカラー表示するためには、``-c``オプションを利用します（``qzsl1sread.py -c < qzss_file.l1s | lv``）。

``-c``オプションを与えると、強制的にカラーにて状態表示します。デフォルトでは、出力先がターミナルであれば、状態表示はカラーにて表示されます。出力先がそれ以外であれば、カラー表示されません。

``-t``オプションを与えると、メッセージ内容の詳細が表示されます。このオプションは整数値とともに用います。数値1では詳細を、数値2ではそれに加えて、ビットイメージを表示します。

例えば、サンプルディレクトリにあるu-blox ZED-F9P受信機生データファイル``20230919-114418.ubx``を[ubxread.py](ubxread.md)にてL1S生データを抽出し、``qzsl1sread.py``にて内容表示します。

```bash
$ ubxread.py --l1s < sample/20230919-114418.ubx | qzsl1sread.py -t 2

PRN137: Long-term satellite error corrections
PRN186: DGPS correction (waiting for PRN mask, MT48)
PRN128: Fast corrections 2
PRN184: DGPS correction (waiting for PRN mask, MT48)
PRN137: Degradation parameters
PRN186: DCR: Marine (Normal) 09-19 08:40 UTC
PRN128: Fast corrections 1
PRN184: DCR: Marine (Normal) 09-19 08:40 UTC
...
PRN186: PRN mask: selected sats: G03 G04 G16 G18 G25 G26 G27 G28 G29 G31 G32 J02 J03 J04 J07 (15 sats, IODP=2)
...
PRN186: Data issue number: IODI=3 IODP=2
PRN IOD
G03 100
G04 184
G16   4
G18  50
G25  18
G26  20
G27   8
G28 112
G29  47
G31  27
G32 115
J02  13
J03  13
J04  13
J07  13
 (15 sats)
...
PRN186: DGPS correction: Sapporo
PRN PRC[m]
G16  -3.08
G26   1.28
G28   2.40
G29   1.36
G31   3.08
G32  -3.28
J02   3.56
J04  -4.00
J07  -1.28
 (9 sats)
 ```

データの読み方は次のページをご参照ください：[QZS L6 ToolのみちびきL1S信号対応](https://s-taka.org/qzsl6tool-20231111upd/)

また、[ubxread.py](ubxread.md)とRTKLIBの``str2str``を利用すると、リアルタイムストリームなども利用できます。
```bash
str2str -in ntrip://ntrip.phys.info.hiroshima-cu.ac.jp:80/F9PR 2> /dev/null | ubxread.py --l1s | qzsl1sread.py
```
