from tavily import TavilyClient
from config.settings import settings

class TavilyService:
    def __init__(self):
        self.client = TavilyClient(api_key=settings.TAVILY_API_KEY)
    
    def search(self, query: str, top_k: int = 5) -> list[str]:
        try:
            response = self.client.search(query=query, top_k=top_k)
            results = response.get("results", [])
            return [r.get("snippet") or r.get("content") or r.get("title", "") for r in results][:top_k]
        except Exception as e:
            print(f"Tavily search failed: {e}")
            return []

tavily_service = TavilyService()