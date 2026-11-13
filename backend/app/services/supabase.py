"""
Supabase Service for Report History & User Accounts (Optional).

Supports:
- Guest mode (anonymous sessions)
- Storing extracted & explained report history when credentials are provided
"""

import logging
from typing import Optional, Dict, Any, List
from app.config import settings

logger = logging.getLogger("reportsaathi.supabase")

supabase_client = None

def get_supabase_client():
    global supabase_client
    if supabase_client is not None:
        return supabase_client

    url = settings.SUPABASE_URL.strip()
    key = settings.SUPABASE_KEY.strip()

    if not url or not key:
        return None

    try:
        from supabase import create_client
        supabase_client = create_client(url, key)
        return supabase_client
    except Exception as e:
        logger.warning(f"Failed to initialize Supabase client: {e}")
        return None

def is_supabase_enabled() -> bool:
    return get_supabase_client() is not None

def save_report_history(report_data: Dict[str, Any], user_id: Optional[str] = None) -> Optional[str]:
    """Save an analyzed report to Supabase if configured."""
    client = get_supabase_client()
    if not client:
        return None

    try:
        payload = {
            "user_id": user_id or "guest",
            "filename": report_data.get("extraction", {}).get("filename", "unknown"),
            "summary": report_data.get("summary", ""),
            "parameters_count": len(report_data.get("parameters_explained", [])),
            "report_data": report_data
        }
        res = client.table("reports").insert(payload).execute()
        if res.data and len(res.data) > 0:
            return res.data[0].get("id")
    except Exception as e:
        logger.error(f"Error saving to Supabase: {e}")
    return None
