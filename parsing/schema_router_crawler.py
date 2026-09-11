import os
import sys
import json
import asyncio
import logging
import argparse
from typing import List, Optional
from dotenv import load_dotenv

# Configure UTF-8 encoding for Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

from src.scraper import GovernmentWebScraper
from src.extractor import GroqServiceExtractor, GovernmentServiceBlueprint
from src.embeddings import HuggingFaceEmbedder
from src.db import SupabaseVectorStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("GovernmentPipeline")


class GovernmentPipelineRunner:
    """
    Autonomous Pipeline:
    1. Scrapes Government Portals using Playwright + BeautifulSoup.
    2. Extracts structured form blueprints (selectors, inputs, buttons, navigation) via Groq LLM.
    3. Generates 384-dimensional normalized vector embeddings with Hugging Face Sentence-Transformers.
    4. Stores and indexes blueprints in Supabase pgvector.
    5. Performs semantic similarity retrieval over pgvector.
    """
    def __init__(self):
        self.scraper = GovernmentWebScraper(headless=True)
        self.extractor = GroqServiceExtractor()
        self.embedder = HuggingFaceEmbedder()
        self.db = SupabaseVectorStore()

    async def process_portal_or_form(self, url: str, portal_base_url: Optional[str] = None) -> Optional[GovernmentServiceBlueprint]:
        """
        Crawls a single URL, sanitizes DOM with BeautifulSoup, extracts structured blueprint with Groq,
        generates Hugging Face 384-d embedding, and saves to Supabase pgvector.
        """
        base_portal = portal_base_url or url
        logger.info(f"🚀 [Scraping] Fetching and rendering portal: {url}")

        try:
            # Step 1: Render dynamic page via Playwright
            page_data = await self.scraper.fetch_page_content(url)
            
            # Step 2: Clean DOM and extract interactive elements with BeautifulSoup
            dom_data = self.scraper.sanitize_and_extract_form_dom(page_data["html"], url)
            logger.info(
                f"📊 [Sanitized DOM] Found {len(dom_data['form_elements'])} inputs, "
                f"{len(dom_data['action_buttons'])} buttons, "
                f"{len(page_data['discovered_links'])} candidate service links."
            )

            # Step 3: Extract structured blueprint via Groq LLM
            logger.info("🧠 [Groq LLM] Synthesizing form blueprint & submission workflow...")
            blueprint = await self.extractor.extract_service_blueprint(
                portal_url=base_portal,
                form_url=url,
                dom_data=dom_data
            )

            logger.info(
                f"✅ [Extracted] Service: '{blueprint.service_title}' | "
                f"Dept: '{blueprint.department_name}' | "
                f"Fields: {len(blueprint.form_fields)} | "
                f"Submit Button: '{blueprint.submit_button_selector}'"
            )

            # Step 4: Generate Hugging Face 384-d Embedding
            logger.info("📐 [Embedding] Generating Hugging Face vector embedding (384-dim)...")
            embedding = self.embedder.embed_query(blueprint.search_content)

            # Step 5: Save to Supabase pgvector
            if self.db.client:
                logger.info("💾 [Supabase] Upserting blueprint and embedding into pgvector...")
                self.db.upsert_service(blueprint, embedding)
                logger.info(f"🎉 Successfully stored '{blueprint.service_title}' in pgvector!")
            else:
                logger.warning("⚠️ Supabase credentials not configured in .env. Skipped database insert.")

            return blueprint

        except Exception as e:
            logger.error(f"❌ Error processing {url}: {e}", exc_info=True)
            return None

    async def run_discovery_and_crawling(self, target_portals: List[str], max_sublinks: int = 2):
        """
        Discovers service links on target portals and crawls each discovered service form.
        """
        for portal_url in target_portals:
            logger.info(f"\n==========================================")
            logger.info(f"🌐 Crawling Portal: {portal_url}")
            logger.info(f"==========================================")

            try:
                # Scrape home portal to discover specific service forms
                page_data = await self.scraper.fetch_page_content(portal_url)
                discovered = page_data.get("discovered_links", [])

                # Process the main portal URL itself first
                await self.process_portal_or_form(portal_url)

                # Process discovered sub-service URLs
                count = 0
                for item in discovered:
                    sub_url = item["url"]
                    if sub_url != portal_url and count < max_sublinks:
                        logger.info(f"\n➡️ [Discovered Service Link] ({item['text']}): {sub_url}")
                        await self.process_portal_or_form(sub_url, portal_base_url=portal_url)
                        count += 1

            except Exception as e:
                logger.error(f"Failed to crawl portal {portal_url}: {e}")

    async def search_pgvector(self, query: str):
        """
        Searches pgvector database for matching government services and forms.
        """
        print("\n" + "=" * 60)
        print(f"🔍 SEMANTIC QUERY: \"{query}\"")
        print("=" * 60)

        query_vector = self.embedder.embed_query(query)
        matches = self.db.query_similar_services(query_embedding=query_vector, match_threshold=0.3, match_count=3)

        if not matches:
            print("\n⚠️ No matching records found in pgvector (or table is empty/uninitialized).")
            return

        print(f"\n✅ Found {len(matches)} matching service(s) in pgvector:\n")
        for idx, match in enumerate(matches, 1):
            print(f"[{idx}] {match.get('service_title')} (Similarity: {match.get('similarity', 0):.3f})")
            print(f"    Department: {match.get('department_name')}")
            print(f"    Form URL: {match.get('form_url')}")
            print(f"    Submit Button: {match.get('submit_button_selector')}")
            print(f"    Total Fields: {len(match.get('form_fields', []))}")
            print("-" * 60)


# ==============================================================================
# CLI Entrypoint
# ==============================================================================

async def main():
    parser = argparse.ArgumentParser(description="Gov Portal Scraper & pgvector Population Pipeline")
    parser.add_argument("--crawl", action="store_true", help="Run crawler over target government portals to populate pgvector")
    parser.add_argument("--url", type=str, help="Crawl and parse a specific form or portal URL")
    parser.add_argument("--query", type=str, help="Search pgvector database using semantic vector query")
    parser.add_argument("--test", action="store_true", help="Run self-test with sample DOM, Groq extraction, and HF embeddings")

    args = parser.parse_args()
    runner = GovernmentPipelineRunner()

    if args.query:
        await runner.search_pgvector(args.query)
    elif args.url:
        await runner.process_portal_or_form(args.url)
    elif args.crawl:
        TARGET_PORTALS = [
            "https://sampark.rajasthan.gov.in/GrievanceRegistration.aspx",
            "https://services.jaipurmc.org/complaints/new",
            "https://citizen.mpenagarpalika.gov.in/pgportal/register-complaint"
        ]
        await runner.run_discovery_and_crawling(TARGET_PORTALS)
    elif args.test:
        logger.info("Running pipeline self-test...")
        sample_html = """
        <html>
            <head><title>Jaipur Nagar Nigam - Streetlight & Sanitation Complaint Portal</title></head>
            <body>
                <h1>Register Civic Grievance</h1>
                <p>Citizens can lodge complaints regarding streetlight outages, uncollected garbage, or drainage overflow. Please keep your Aadhaar or Consumer Number handy.</p>
                <form id="grievanceForm" action="/submit" method="POST">
                    <label for="txtName">Full Name</label>
                    <input type="text" id="txtName" name="citizen_name" required placeholder="Enter full name" />
                    
                    <label for="txtMobile">Mobile Number</label>
                    <input type="text" id="txtMobile" name="mobile_no" required placeholder="10-digit mobile number" />

                    <label for="selDept">Department</label>
                    <select id="selDept" name="department" required>
                        <option value="1">Electricity / Streetlights</option>
                        <option value="2">Sanitation & Garbage Disposal</option>
                        <option value="3">Water Supply & Sewerage</option>
                    </select>

                    <label for="txtAddress">Location / Ward</label>
                    <textarea id="txtAddress" name="ward_address" placeholder="Enter Ward No and Landmark"></textarea>

                    <button type="submit" id="btnSubmitGrievance">Submit Complaint</button>
                </form>
            </body>
        </html>
        """
        dom_data = runner.scraper.sanitize_and_extract_form_dom(sample_html, "https://services.jaipurmc.org")
        blueprint = await runner.extractor.extract_service_blueprint(
            portal_url="https://services.jaipurmc.org",
            form_url="https://services.jaipurmc.org/complaints/new",
            dom_data=dom_data
        )
        print("\n" + "=" * 60)
        print("📄 EXTRACTED GOVERNMENT SERVICE BLUEPRINT (via Groq LLM):")
        print("=" * 60)
        print(blueprint.model_dump_json(indent=2))

        # Test Hugging Face embedding
        emb = runner.embedder.embed_query(blueprint.search_content)
        print("\n" + "=" * 60)
        print(f"📐 HUGGING FACE VECTOR EMBEDDING (384-dim, Length: {len(emb)}):")
        print("=" * 60)
        print(f"Sample dimensions: {emb[:8]}...")
        print("\n✅ End-to-end self-test completed successfully!")
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
