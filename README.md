# process-network-monitor

指定時間内のプロセス別I/O活動量を差分から計測するスクリプト

## 説明

このプロジェクトは、10秒間のプロセス別I/O活動量（`read_bytes + write_bytes` の差分）を測定し、結果をスタックグラフで可視化します。

> v1.0では、指標としてプロセスI/O差分を採用しています。厳密な「プロセス別ネットワーク送受信量」への拡張は v2.0 で対応予定です。

**特徴：**
- バックグラウンドで継続的にプロセスのIO統計をスキャン
- 時間ごとの差分I/O量（Mb/s相当）を計測
- トップ5プロセスと「その他」を分類して表示
- 定時サンプリングによる精密な計測

## セットアップと実行

### 1. 必要なライブラリをインストール

```bash
pip install psutil matplotlib
```

### 2. スクリプトを実行

```bash
python3 monitor_network.py
```

約12秒で計測完了後、ネットワークトラフィックのグラフが表示されます。

### 3. 再現モード（No traffic表示の確認）

`No traffic detected` の表示を確実に確認したい場合は、再現モードで実行できます。

```bash
FORCE_NO_TRAFFIC=1 python3 monitor_network.py
```

このモードでは通信データを描画対象から除外し、データなし時の表示を検証できます。

## 完了基準（DoD）

開発の現在地と完了判定は `docs/definition-of-done.md` を参照してください。

## 長時間実行時のメモリ確認（Issue #11向け）

スキャナの長時間挙動を確認する場合は、以下のように複数回実行してピークRSSの傾向を見ます。

```bash
python3 - <<'PY'
import subprocess
import psutil

for i in range(1, 21):
	proc = subprocess.Popen(["python3", "monitor_network.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	p = psutil.Process(proc.pid)
	peak = 0
	while proc.poll() is None:
		try:
			rss = p.memory_info().rss
			if rss > peak:
				peak = rss
		except psutil.Error:
			break
	print(f"run={i} peak_rss_kb={peak // 1024}")
PY
```

確認ポイント:
- 実行回数に対してRSSが単調増加し続けないこと
- 極端な増加が発生しないこと

## カスタマイズ

`monitor_network.py` の設定部分で以下をカスタマイズできます：

```python
duration = 10  # 計測時間（秒）
top_n = 5      # 表示するトップアプリケーション数
```
