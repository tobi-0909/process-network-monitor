# Session Handoff Template - process-network-monitor

セッション間での進捗引き継ぎを5分で完了するためのテンプレートです。

---

## 1. 現在のプロジェクト状態（最新）

**v1.0: リリース完了** 🎉 (2026-03-01)
- 計測対象: プロセス I/O差分（`read_bytes + write_bytes`）
- 実装完了: #10, #11, #12, #14
- 検証完了: 通常実行 ✓, 再現モード ✓, メモリ安定 ✓
- リリース宣言: Issue #19 クローズ済み

**v1.1: 計画中** (Milestone #2)
- #13: グローバル状態削減（テスト容易性）
- #15: logging移行（運用性向上）

**v2.0: 検討中** (Milestone #3)
- テーマ: メトリクス拡張（I/O差分 → 直接ネットワーク計測）
- 検討段階（Epic 未作成）

---

## 2. ブランチ・コミット状態

| 項目 | 状態 |
|------|------|
| 現在のブランチ | `main` |
| 最新コミット | `9333026` (Mark v1.0 as complete) |
| ステージング待ち | なし |
| 差分（未コミット） | なし |

**確認コマンド:**
```bash
git status
git log --oneline -n 3
```

---

## 3. 最新マイルストーン / Issue 状態

**v1.0関連（完了）**
- Issue #10: CLOSED（PR #16）
- Issue #11: CLOSED（PR #17）
- Issue #12: CLOSED（PR #21）
- Issue #14: CLOSED（PR #22）
- Issue #19: CLOSED（チェックリスト）

**v1.1関連（OPEN）**
- Issue #13: OPEN (milestone:v1.1, priority:medium)
- Issue #15: OPEN (milestone:v1.1, priority:low)

**確認コマンド:**
```bash
gh issue list --state open
gh issue list --milestone v1.1 --state open
```

---

## 4. ドキュメント参照

- **定義・完了基準**: [docs/definition-of-done.md](definition-of-done.md)
  - v1.0 DoD: 全項目 [x]
  - v2.0計画: section 6.5
- **実装**: [monitor_network.py](../monitor_network.py)
  - 最新変更: `time.perf_counter()` 化（#14）
- **説明**: [README.md](../README.md)
  - v1.0スコープ明記済み

---

## 5. 次のアクション候補

### 短期（1セッション）
- [ ] v1.1 #13 着手（グローバル状態削減）
- [ ] v1.1 #15 着手（logging移行）
- [ ] リリースノート作成（任意）

### 中期
- [ ] v1.1 マイルストーン完了 → v1.1 リリース
- [ ] v2.0 Epic を起票・設計

### 参考コマンド

**Issue操作:**
```bash
gh issue view <number>                    # Issue詳細表示
gh issue comment <number> --body "..."    # コメント追加
gh issue edit <number> --milestone v1.1   # マイルストーン変更
```

**ブランチ作業:**
```bash
git checkout -b fix/issue-NNN-desc        # 新ブランチ作成
git add . && git commit -m "msg"          # コミット
git push -u origin fix/issue-NNN-desc     # push
gh pr create --base main                  # PR作成
gh pr merge <pr-number> --squash          # PR マージ
```

**検証:**
```bash
python3 monitor_network.py                # 通常実行
FORCE_NO_TRAFFIC=1 python3 monitor_network.py  # 再現モード
```

---

## 6. 重要な方針

- **計測対象**: v1.0は「I/O差分」で確定。精密ネットワーク計測は v2.0
- **変更管理**: すべて PR 経由で main へ反映
- **ドキュメント**: DoD と README が真実の源
- **運用**: Issue ベースで優先度・Milestone を管理

---

## 使い方

新しいセッションで作業開始時：
1. このファイルを読む（3分）
2. 上記「ブランチ・コミット状態」の確認コマンドを実行（1分）
3. 次のアクション候補から選ぶ（1分）

変更があったら、このファイルを更新してコミットしておくと、次セッションがスムーズです。

