#!/bin/bash

# W&B Fully Connected Tokyo 2025 - AIエージェントワークショップ
# 環境変数設定ファイル作成スクリプト

set -e

# 色付きメッセージ用の設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ログ関数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 安全な入力関数（秘密情報用）
read_secret() {
    local prompt="$1"
    local var_name="$2"
    local value=""
    
    echo -n "$prompt"
    read -s value
    echo
    
    if [[ -z "$value" ]]; then
        log_warning "空の値が入力されました。スキップします。"
        return 1
    fi
    
    eval "$var_name='$value'"
    return 0
}

# 通常の入力関数
read_input() {
    local prompt="$1"
    local var_name="$2"
    local value=""
    
    echo -n "$prompt"
    read value
    
    if [[ -z "$value" ]]; then
        log_warning "空の値が入力されました。スキップします。"
        return 1
    fi
    
    eval "$var_name='$value'"
    return 0
}

# メイン処理
main() {
    log_info "W&B Fully Connected Tokyo 2025 - AIエージェントワークショップ"
    log_info "環境変数設定ファイル(.env)を作成します"
    echo

    # プロジェクトルートディレクトリに移動
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
    cd "$PROJECT_ROOT"

    # 既存の.envファイルをチェック
    if [[ -f ".env" ]]; then
        log_warning ".envファイルが既に存在します。"
        echo -n "上書きしますか？ (y/N): "
        read overwrite
        if [[ "$overwrite" != "y" && "$overwrite" != "Y" ]]; then
            log_info "処理を中断しました。"
            exit 0
        fi
    fi

    echo
    log_info "以下のAPIキーを入力してください（空Enter でスキップ可能）:"
    echo

    # 各APIキーの入力
    OPENAI_API_KEY=""
    PERPLEXITY_API_KEY=""
    WANDB_API_KEY=""
    WANDB_PROJECT="wandb-fc-2025-agent-workshop"
    LOG_LEVEL="INFO"
    
    # OpenAI API Key
    echo "🤖 OpenAI API Key"
    echo "   取得方法: https://platform.openai.com/api-keys"
    if read_secret "   APIキーを入力: " "OPENAI_API_KEY"; then
        :
    fi
    echo

    # Perplexity API Key
    echo "🔍 Perplexity AI API Key"
    echo "   取得方法: https://www.perplexity.ai/settings/api"
    if read_secret "   APIキーを入力: " "PERPLEXITY_API_KEY"; then
        :
    fi
    echo

    # W&B API Key
    echo "📊 Weights & Biases API Key"
    echo "   取得方法: https://wandb.ai/settings"
    if read_secret "   APIキーを入力: " "WANDB_API_KEY"; then
        :
    fi
    echo

    # 追加の環境変数
    log_info "追加の環境変数設定:"
    echo

    # W&B Project Name
    echo "📈 W&B Project Name (デフォルト: wandb-fc-2025-agent-workshop)"
    if ! read_input "   プロジェクト名を入力: " "WANDB_PROJECT"; then
        WANDB_PROJECT="wandb-fc-2025-agent-workshop"
    fi
    echo

    # Log Level
    echo "📝 ログレベル (DEBUG, INFO, WARNING, ERROR) (デフォルト: INFO)"
    if ! read_input "   ログレベルを入力: " "LOG_LEVEL"; then
        LOG_LEVEL="INFO"
    fi
    echo

    # .envファイルの作成
    log_info ".envファイルを作成中..."
    
    cat > .env << EOF
# W&B Fully Connected Tokyo 2025 - AIエージェントワークショップ
# 環境変数設定ファイル
# 作成日時: $(date '+%Y-%m-%d %H:%M:%S')

# =============================================================================
# API Keys
# =============================================================================

OPENAI_API_KEY=${OPENAI_API_KEY}
PERPLEXITY_API_KEY=${PERPLEXITY_API_KEY}
WANDB_API_KEY=${WANDB_API_KEY}
WANDB_PROJECT=${WANDB_PROJECT}
LOG_LEVEL=${LOG_LEVEL}

# =============================================================================
# Development Settings
# =============================================================================

# Python Path
PYTHONPATH=./:$PYTHONPATH

# Development Mode
DEVELOPMENT=true

# =============================================================================
# LangGraph Settings
# =============================================================================

# LangGraph Studio Configuration
LANGGRAPH_API_URL=http://localhost:2024

EOF

    # 権限設定
    chmod 600 .env

    log_success ".envファイルが正常に作成されました！"
    echo
    log_info "設定された環境変数:"
    echo "  OPENAI_API_KEY: ********"
    echo "  PERPLEXITY_API_KEY: ********"
    echo "  WANDB_API_KEY: ********"
    echo "  WANDB_PROJECT: ${WANDB_PROJECT}"
    echo "  LOG_LEVEL: ${LOG_LEVEL}"
    echo
    log_warning "重要: .envファイルには機密情報が含まれています。"
    log_warning "      このファイルをGitリポジトリにコミットしないでください。"
    echo
    log_info "次のコマンドでアプリケーションを起動できます:"
    echo "  uv sync"
    echo "  uv run langgraph dev --no-reload"
}

# エラーハンドリング
trap 'log_error "スクリプト実行中にエラーが発生しました"; exit 1' ERR

# メイン処理実行
main "$@"
