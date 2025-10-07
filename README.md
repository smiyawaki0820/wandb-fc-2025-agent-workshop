# 現場で活用するためのAIエージェントワークショップ

https://fullyconnected.jp/

## 設定

### API

- OpenAI
- W&B
- Perplexity
- Jina

### 環境設定


```baash
uv sync
export PYTHONPATH="./:$PYTHONPATH"
```

## 実装

### クイックスタート

```bash
uv run langgraph dev --no-reload
```

### 詳細

#### 情報調査

```bash
uv run python app/application/use_case/execute_task_agent/agent.py
```

#### DeepResearch

```bash
uv run python app/aplication/use_case/research_agent/agent.py
```


## 連絡

shumpei.miyawaki@algomatic.jp