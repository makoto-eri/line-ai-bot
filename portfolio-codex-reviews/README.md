# portfolio-codex-reviews — Claude Code と Codex の受け渡しフォルダ

Claude Code（左ターミナル）と Codex（右ターミナル）を並べて開発するときに、両者の間で計画書・レビュー・指摘を受け渡すための共有フォルダ。

**どちらの AI も自動では動かない。** ユーザーが各ターミナルに手で指示を入力する必要がある。Claude Code 側は `codex-bridge` スキルがファイル作成・プロンプト整形を自動で行うので、ユーザー操作は「指示一言」＋「右ターミナルへのペースト1回」に最小化される。

## フォルダ構成

```
portfolio-codex-reviews/
├── README.md          # このファイル
├── to-codex/          # Claude → Codex（計画書・レビュー依頼・反映報告）
└── from-codex/        # Codex → Claude（レビュー結果・修正指示）
```

## 標準ワークフロー

### パターン1: Plan mode の計画レビュー

```
ユーザー(左): 「〇〇を作りたい」
Claude:      Plan mode で計画作成 → ~/.claude/plans/plan-*.md
ユーザー(左): 「この計画コデックスに見てもらって」
Claude:      to-codex/YYYY-MM-DD-<topic>-plan.md に計画を書き出し
              Codex用プロンプトを提示（コピペ1回）
ユーザー(右): プロンプトを Codex にペースト
Codex:       from-codex/<同名>-response.md にレビューを書く
ユーザー(左): 「コデックスから返事きた」
Claude:      最新 from-codex を読み、計画を改訂または反映
```

### パターン2: 実装コードのレビュー

```
ユーザー(左): 「今のコードをコデックスにレビューしてもらって」
Claude:      to-codex/YYYY-MM-DD-<topic>-review.md に対象パスと観点を記載
              Codex用プロンプトを提示
ユーザー(右): プロンプトを Codex にペースト
Codex:       対象ファイルを直接読み、from-codex/ にレビューを書く
ユーザー(左): 「レビュー読んで反映」
Claude:      最新 from-codex を読み、修正を適用
```

## ファイル命名規則

| 用途 | 形式 |
|---|---|
| 計画レビュー依頼 | `to-codex/YYYY-MM-DD-<topic>-plan.md` |
| コードレビュー依頼 | `to-codex/YYYY-MM-DD-<topic>-review.md` |
| Codex返信 | `from-codex/YYYY-MM-DD-<topic>-<kind>-response.md` |
| 反映報告 | `to-codex/YYYY-MM-DD-<topic>-<kind>-applied.md` |
| 往復2回目以降 | `-v2`, `-v3` を suffix で |

## 注意

- Claude Code から Codex を起動したり指示を送ったりはできない。**ユーザーが両方のターミナルに手で指示を入力する**
- 完了したやり取りは `archive/YYYY-MM/` に移しておくと現在進行中が見やすい
- 計画レビューは計画ファイル1つで完結する（Codexはコードを読みに行かなくてよい）
- コードレビューは対象パスを書くだけでよい（Codexが直接ソースを読む）

## Claude Code 側のスキル

`codex-bridge` グローバルスキルがインストールされていると、以下のキーワードで自動発動する:

- 「コデックスに渡す/送る/レビューしてもらう」
- 「プランをコデックスに」「セカンドオピニオン」
- 「コデックスから返事きた」「from-codex 読んで反映」

スキル本体: `~/.claude/skills/codex-bridge/SKILL.md`
