import json

from dotenv import load_dotenv
from langchain_core.tools import tool
from perplexity.types.search_create_response import SearchCreateResponse
from perplexity import Perplexity


load_dotenv()


@tool
def search_web(search_view: str) -> str:
    """指定されたキーワードでWeb検索を行い、検索結果を返します.

    Args:
    ----
        search_view (str): Web検索に使用するキーワードや観点です。例えば、特定の技術や最新動向に関するキーワードを指定することで、より広範囲かつ深い情報収集が可能になります。

    Returns:
    -------
        SearchCreateResponse: 検索結果。

    """  # noqa: E501
    client = Perplexity()
    search_create_response: SearchCreateResponse = client.search.create(
        query=search_view,
        max_results=3,
        max_tokens_per_page=512
    )
    return json.dumps([
        {
            "title": result.title,
            "url": result.url,
            "snippet": result.snippet,
        }
        for result in search_create_response.results
    ], ensure_ascii=False)

