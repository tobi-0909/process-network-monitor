#!/usr/bin/env python3
"""
指定時間内のネットワーク通信量を差分から計測するスクリプト
"""
import queue
import sys
import psutil
import time
import threading
import os
import traceback
import matplotlib.pyplot as plt

class ScannerThreadError(RuntimeError):
    """バックグラウンドスレッドの致命的エラーを表す例外。"""


def collect_process_io_totals():
    """PID単位で短命な参照を使ってプロセス別IO合計を収集する。"""
    totals_by_name = {}

    for pid in psutil.pids():
        try:
            proc = psutil.Process(pid)
            with proc.oneshot():
                io = proc.io_counters()
                name = proc.name()

            total = io.read_bytes + io.write_bytes
            totals_by_name[name] = totals_by_name.get(name, 0) + total
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, AttributeError, OSError):
            continue

    return totals_by_name


def background_scanner(latest_stats, stats_lock, stop_event, scanner_errors):
    """バックグラウンドで全プロセスのIOを常にスキャンし続ける。"""
    try:
        while not stop_event.is_set():
            temp_stats = collect_process_io_totals()

            with stats_lock:
                latest_stats.clear()
                latest_stats.update(temp_stats)

            stop_event.wait(0.1)  # CPU負荷を抑えつつ、停止要求に素早く反応
    except Exception:
        traceback_text = traceback.format_exc()
        try:
            scanner_errors.put_nowait(traceback_text)
        except queue.Full:
            pass
        stop_event.set()


def check_scanner_error(scanner_errors):
    """スキャナスレッドで発生した致命的エラーを検知して例外化する。"""
    try:
        traceback_text = scanner_errors.get_nowait()
    except queue.Empty:
        return
    raise ScannerThreadError(f"スキャナースレッドで致命的エラーが発生しました。\n{traceback_text}")


def main():
    scanner_thread = None
    stop_event = threading.Event()
    scanner_errors = queue.Queue(maxsize=1)
    latest_stats = {}
    stats_lock = threading.Lock()

    try:
        # --- 設定 ---
        duration = 10
        top_n = 5
        time_axis = list(range(duration + 1))
        history = {}
        force_no_traffic = os.getenv("FORCE_NO_TRAFFIC", "0").lower() in ("1", "true", "yes")

        if force_no_traffic:
            print("再現モード有効: 通信データを描画対象から除外します")

        # スキャナースレッド開始
        scanner_thread = threading.Thread(
            target=background_scanner,
            args=(latest_stats, stats_lock, stop_event, scanner_errors),
            daemon=True,
        )
        scanner_thread.start()

        print(f"{duration}秒間の計測を開始...")

        # 初期データの準備（スキャナが最初のデータを取るまで少し待つ）
        time.sleep(2)
        check_scanner_error(scanner_errors)

        with stats_lock:
            last_snapshot = latest_stats.copy()

        start_time = time.time()

        for t in range(1, duration + 1):
            target_time = start_time + t

            # 待機
            sleep_time = target_time - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)

            check_scanner_error(scanner_errors)

            # 最新の値をサンプリング（一瞬で終わる）
            with stats_lock:
                current_snapshot = latest_stats.copy()

            for name, total in current_snapshot.items():
                diff_bytes = total - last_snapshot.get(name, total)
                if diff_bytes < 0:
                    diff_bytes = 0
                diff_mb = (diff_bytes * 8) / 1_000_000

                if name not in history:
                    history[name] = [0.0] * (duration + 1)
                history[name][t] = diff_mb

            last_snapshot = current_snapshot
            print(f"{t}秒経過... (誤差: {time.time() - target_time:.4f}s)")

        print("計測完了。グラフを表示します。")

        # --- データ整形（集約とソート） ---
        if force_no_traffic:
            history = {}

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
            ax.text(
                0.5,
                0.5,
                "No traffic detected",
                transform=ax.transAxes,
                ha='center',
                va='center',
            )

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
        return 0

    except KeyboardInterrupt:
        print("計測を中断しました。", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"エラーが発生しました: {exc}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return 1
    finally:
        stop_event.set()
        if scanner_thread is not None:
            scanner_thread.join(timeout=3.0)
            if scanner_thread.is_alive():
                print("警告: スキャナースレッドが終了待機時間内に停止しませんでした。", file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
