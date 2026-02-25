#!/usr/bin/env python3
"""
指定時間内のネットワーク通信量を差分から計測するスクリプト
"""
import psutil
import time
import threading
import matplotlib.pyplot as plt

# グローバル変数で最新の統計を保持
latest_stats = {}
stats_lock = threading.Lock()
running = True

def background_scanner():
    """バックグラウンドで全プロセスのIOを常にスキャンし続ける"""
    global latest_stats
    while running:
        temp_stats = {}
        for proc in psutil.process_iter(['name']):
            try:
                io = proc.io_counters()
                name = proc.info['name']
                total = io.read_bytes + io.write_bytes
                temp_stats[name] = temp_stats.get(name, 0) + total
            except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                continue
        with stats_lock:
            latest_stats = temp_stats
        time.sleep(0.1)  # CPU負荷を抑えるための微小な休憩

# --- 設定 ---
duration = 10
top_n = 5
time_axis = list(range(duration + 1))
history = {}

# スキャナースレッド開始
scanner_thread = threading.Thread(target=background_scanner, daemon=True)
scanner_thread.start()

print(f"{duration}秒間の計測を開始...")

# 初期データの準備（スキャナが最初のデータを取るまで少し待つ）
time.sleep(2) 
with stats_lock:
    last_snapshot = latest_stats.copy()

start_time = time.time()

for t in range(1, duration + 1):
    target_time = start_time + t
    
    # 待機
    sleep_time = target_time - time.time()
    if sleep_time > 0:
        time.sleep(sleep_time)
    
    # 最新の値をサンプリング（一瞬で終わる）
    with stats_lock:
        current_snapshot = latest_stats.copy()
    
    for name, total in current_snapshot.items():
        diff_bytes = total - last_snapshot.get(name, total)
        if diff_bytes < 0: diff_bytes = 0
        diff_mb = (diff_bytes * 8) / 1_000_000
        
        if name not in history:
            history[name] = [0.0] * (duration + 1)
        history[name][t] = diff_mb
        
    last_snapshot = current_snapshot
    print(f"{t}秒経過... (誤差: {time.time() - target_time:.4f}s)")

running = False # スキャナー停止
print("計測完了。グラフを表示します。")


# --- データ整形（集約とソート） ---
sorted_all = sorted(history.items(), key=lambda x: sum(x[1]), reverse=True)
top_apps_data = sorted_all[:top_n]
others_raw = sorted_all[top_n:]

others_values = [0.0] * (duration + 1)
for _, values in others_raw:
    for i, v in enumerate(values):
        others_values[i] += v

plot_labels = []
plot_values = []
for name, values in top_apps_data:
    if sum(values) > 0:
        plot_labels.append(name)
        plot_values.append(values)

if sum(others_values) > 0:
    plot_labels.append("Others")
    plot_values.append(others_values)

# --- グラフ作成 ---
fig, ax = plt.subplots(figsize=(12, 7))

# 単位を決定（最大値に応じて）
unit_label = "Mb/s"
if plot_values:
    max_value = max(max(values) for values in plot_values)
    
    if max_value < 1.0:
        # Mbpsで1未満 → kbpsに変換
        unit_label = "kb/s"
        plot_values = [[v * 1000 for v in values] for values in plot_values]

if plot_values:
    cmap = plt.get_cmap("tab20")
    ax.stackplot(time_axis, plot_values, labels=plot_labels, alpha=0.8, colors=cmap.colors)
    ax.legend(loc='upper left', title=f"Top {top_n} & Others", bbox_to_anchor=(1, 1))
else:
    ax.text(0.5, 0.5, "No traffic detected", ha='center')

ax.set_title("Network Traffic (Drift Corrected & Aggregated)")
ax.set_xlabel("Time (seconds)")
ax.set_ylabel(f"Traffic Volume ({unit_label})")
ax.set_xlim(1, duration)
ax.grid(True, linestyle='--', alpha=0.4)

plt.tight_layout()

# グラフをファイルに保存
output_file = "network_traffic.png"
plt.savefig(output_file, dpi=100, bbox_inches='tight')
print(f"グラフを保存しました: {output_file}")
