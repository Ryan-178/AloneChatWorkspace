from typing import Any, Dict, List, Optional

from alonechat.core.base_tool import BaseTool


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the web for information. Returns a list of search results with title, snippet, and URL."
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query string",
            },
            "num_results": {
                "type": "integer",
                "description": "Number of results to return (default 5)",
                "default": 5,
            },
        },
        "required": ["query"],
    }

    def execute(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = []
                for r in ddgs.text(query, max_results=num_results):
                    results.append({
                        "title": r.get("title", ""),
                        "snippet": r.get("body", ""),
                        "url": r.get("href", ""),
                    })
                return results
        except ImportError:
            return [{"title": "DuckDuckGo search unavailable", "snippet": "Install duckduckgo-search to use web search", "url": ""}]
        except Exception as e:
            return [{"title": "Search error", "snippet": str(e), "url": ""}]
