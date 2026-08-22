"""
API Client for Polymarket Analytics Frontend.

Provides convenient methods for communicating with the backend API.
"""

import os
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime


class PolymarketAPIClient:
    """Client for Polymarket Analytics Backend API"""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or os.getenv("BACKEND_URL", "http://localhost:8000")).rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Dict = None,
        data: Dict = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """Make HTTP request to API"""
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"API request failed: {e}"
            }

    def get(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        """Make GET request"""
        return self._request("GET", endpoint, params=params)

    def post(self, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """Make POST request"""
        return self._request("POST", endpoint, data=data)

    def health_check(self) -> Dict[str, Any]:
        """Check API health status"""
        return self.get("/health")

    def get_live_markets(
        self,
        category: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get live markets"""
        params = {"limit": limit}
        if category:
            params["category"] = category
        return self.get("/api/v1/markets/live", params)

    def get_mock_markets(
        self,
        scenario_id: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get mock markets"""
        params = {"limit": limit}
        if scenario_id:
            params["scenario_id"] = scenario_id
        return self.get("/api/v1/markets/mock", params)

    def get_resolved_markets(
        self,
        category: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get resolved markets"""
        params = {"limit": limit}
        if category:
            params["category"] = category
        return self.get("/api/v1/markets/resolved", params)

    def get_category_performance(self) -> Dict[str, Any]:
        """Get category performance analytics"""
        return self.get("/api/v1/analytics/category-performance")

    def get_signal_performance(self) -> Dict[str, Any]:
        """Get signal performance analytics"""
        return self.get("/api/v1/analytics/signal-performance")

    def export_to_csv(
        self,
        data: List[Dict],
        filename: str,
        prefix: str = "polymarket_export"
    ) -> str:
        """Export data to CSV file"""
        import pandas as pd

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_filename = f"{prefix}_{timestamp}_{filename}"

        df = pd.DataFrame(data)
        df.to_csv(full_filename, index=False)

        return full_filename


# Convenience instance
api_client = PolymarketAPIClient()
