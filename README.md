# W&B Fully Connected Tokyo 2025 - AIエージェントワークショップ

現場で活用するためのAIエージェントワークショップへようこそ！

**イベント詳細**: https://fullyconnected.jp/

## 📋 概要

本プロジェクトは、Weights & Biases (W&B) Fully Connected Tokyo 2025イベント向けの実践的なAIエージェントワークショップです。LangGraphを使用してマルチステップのリサーチエージェントを構築し、現場で活用可能な実装を学習できます。

## 🏗️ アーキテクチャ

プロジェクトはクリーンアーキテクチャのアプローチに基づいて構成されています：

```
app/
├── application/        # アプリケーション層
│   └── use_case/
│       └── research_agent/
├── core/              # コア機能
├── domain/            # ドメイン層
└── infrastructure/    # インフラストラクチャ層
```

## 🛠️ 技術スタック

- **Python**: 3.12+
- **フレームワーク**: LangGraph, LangChain
- **LLMプロバイダー**: OpenAI, Perplexity AI
- **ML追跡**: Weave (W&B)
- **データ検証**: Pydantic
- **コード品質**: Ruff, MyPy

## ⚙️ セットアップ

### 必要要件

- Python 3.12以上
- UV (推奨パッケージマネージャー)

### API設定

以下のAPIキーが必要です：

- OpenAI API Key
- Perplexity AI API Key
- W&B API Key

### 環境構築

```bash
bash scripts/create_env_file.sh
```

## 🚀 実行方法

### クイックスタート（LangGraphサーバー）

```bash
uv run langgraph dev --no-reload
```

### 個別実行

#### リサーチエージェント

```bash
uv run python app/application/use_case/research_agent/agent.py
```

## 📖 主要機能

### ResearchAgent

メインのリサーチエージェント。以下のステップで動作します：

1. **要件収集**: リサーチ要件の分析
2. **計画構築**: リサーチ計画の作成
3. **タスク実行**: 個別タスクの処理
4. **レポート生成**: 最終結果の出力

### ツールとユーティリティ

- **ウェブ検索**: Perplexity APIを使用
- **コンテンツ管理**: ローカルストレージ管理
- **プロンプト管理**: Jinjaテンプレート使用

## 📁 プロジェクト構造

```
├── storage/
│   ├── prompts/        # プロンプトテンプレート
│   ├── outputs/        # 生成されたレポート
│   └── fixtures/       # テスト用データ
├── app/
│   ├── application/    # ユースケース実装
│   ├── core/          # 共通機能
│   ├── domain/        # ドメインロジック
│   └── infrastructure/ # 外部サービス連携
└── langgraph.json     # LangGraph設定
```

## 📞 お問い合わせ

ご質問やサポートが必要な場合は、以下までご連絡ください：

**Email**: shumpei.miyawaki@algomatic.jp

---

**W&B Fully Connected Tokyo 2025で実践的なAIエージェント開発を学びましょう！** 🎉
