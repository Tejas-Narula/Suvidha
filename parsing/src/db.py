import os
import logging
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from src.extractor import GovernmentServiceBlueprint

logger = logging.getLogger(__name__)

class SupabaseVectorStore:
    """
    Manages storing, upserting, and retrieving Government Service Blueprints and
    vector embeddings in Supabase pgvector.
    """
    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

        if not self.supabase_url or not self.supabase_key:
            logger.warning("Supabase credentials not set in .env. Database operations will be skipped.")
            self.client: Optional[Client] = None
        else:
            self.client = create_client(self.supabase_url, self.supabase_key)

    def upsert_service(self, blueprint: GovernmentServiceBlueprint, embedding: List[float]) -> Dict[str, Any]:
        """
        Upserts a parsed government service blueprint with its 384-dimensional vector embedding into pgvector.
        """
        if not self.client:
            raise ValueError("Supabase client is not initialized. Please configure SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.")

        record = {
            "service_title": blueprint.service_title,
            "intent": blueprint.intent,
            "department_name": blueprint.department_name,
            "portal_url": blueprint.portal_url,
            "form_url": blueprint.form_url,
            "navigation_steps": [s.model_dump() for s in blueprint.navigation_steps],
            "form_fields": [f.model_dump() for f in blueprint.form_fields],
            "submit_button_selector": blueprint.submit_button_selector,
            "submission_steps": blueprint.submission_steps,
            "search_content": blueprint.search_content or "",
            "raw_blueprint": blueprint.model_dump(),
            "embedding": embedding,
            "updated_at": "now()"
        }

        try:
            response = self.client.table("government_schemas").upsert(
                record,
                on_conflict="form_url"
            ).execute()
            return response.data
        except Exception as e:
            logger.warning(
                f"Supabase upsert warning: {e}. "
                "Ensure schema.sql has been executed in your Supabase SQL Editor to create 'government_schemas' table."
            )
            return {"status": "table_not_initialized", "error": str(e)}

    def query_similar_services(
        self,
        query_embedding: List[float],
        match_threshold: float = 0.3,
        match_count: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Executes semantic vector similarity search in pgvector using the match_government_schemas RPC function.
        """
        if not self.client:
            raise ValueError("Supabase client is not initialized.")

        try:
            rpc_params = {
                "query_embedding": query_embedding,
                "match_threshold": match_threshold,
                "match_count": match_count
            }
            response = self.client.rpc("match_government_schemas", rpc_params).execute()
            return response.data or []
        except Exception as e:
            logger.warning(
                f"Supabase pgvector query notice: {e}. "
                "Ensure schema.sql has been executed in your Supabase SQL Editor."
            )
            return []
