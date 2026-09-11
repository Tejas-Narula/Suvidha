# 🕷️ Government Portal Scraping & Knowledge Ingestion Pipeline

Autonomous data extraction and pgvector indexing engine designed to scrape Indian government portals, extract clean interactable form blueprints using **Groq LLM**, generate **384-dimensional vector embeddings**, and index them in **Supabase pgvector**.

---

## 🏗️ Pipeline Architecture

```
1. Crawl & Render (Playwright)
   └─► Renders JavaScript-heavy dynamic portals & SPAs in headless Chromium.

2. Sanitize & Parse DOM (BeautifulSoup)
   └─► Strips noise & extracts <input>, <select>, <textarea>, action buttons & instructions.

3. Structured Extraction (Groq LLM - openai/gpt-oss-120b)
   └─► Synthesizes a strict GovernmentServiceBlueprint (CSS selectors, required fields, navigation steps, submit buttons).

4. Vector Embeddings (Hugging Face all-MiniLM-L6-v2)
   └─► Generates 384-dimensional normalized embeddings for semantic cosine similarity search.

5. Database Indexing (Supabase pgvector)
   └─► Upserts records into `government_schemas` table with an HNSW cosine index.
```

---

## 📂 Core Modules

* **`src/scraper.py` (`GovernmentWebScraper`)**:
  * Headless Playwright browser runner.
  * Discovers bilingual service links and grievance forms (Hindi + English keywords).
  * Extracts input labels, dropdown options, and button selectors.

* **`src/extractor.py` (`GroqServiceExtractor`)**:
  * Pydantic schemas: `FormField`, `NavigationStep`, `GovernmentServiceBlueprint`.
  * Passes sanitized DOM to Groq LLM with strict JSON schema constraints.
  * Guarantees complete `navigation_steps`, `form_fields`, and `submission_steps`.

* **`src/embeddings.py` (`HuggingFaceEmbedder`)**:
  * Uses `sentence-transformers/all-MiniLM-L6-v2` (supports local model cache or FastEmbed ONNX).
  * Outputs 384-dimensional normalized float arrays.

* **`src/db.py` (`SupabaseVectorStore`)**:
  * Manages database upserts on conflict of `form_url`.
  * Executes similarity searches using `match_government_schemas` RPC.

---

## 🚀 CLI Commands

### 1. Run Pipeline Self-Test
Validates DOM extraction, Groq blueprint parsing, and vector embedding generation on sample civic HTML:
```bash
python schema_router_crawler.py --test
```

### 2. Semantic Search Query
Tests matching accuracy directly against Supabase pgvector:
```bash
python schema_router_crawler.py --query "I want to apply for new farmer financial support scheme"
```

### 3. Crawl Specific URL
Scrapes, parses, and indexes a single portal or form endpoint:
```bash
python schema_router_crawler.py --url "https://pmkisan.gov.in/RegistrationFormNew.aspx"
```

### 4. Batch Discovery & Crawl
Runs discovery over target government portals:
```bash
python schema_router_crawler.py --crawl
```

---

## 🗄️ Database Setup (`schema.sql`)

Before running the pipeline, ensure the following is executed in the Supabase SQL Editor:
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS government_schemas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_title TEXT NOT NULL,
    intent TEXT NOT NULL,
    department_name TEXT NOT NULL,
    portal_url TEXT NOT NULL,
    form_url TEXT NOT NULL UNIQUE,
    navigation_steps JSONB NOT NULL DEFAULT '[]'::jsonb,
    form_fields JSONB NOT NULL DEFAULT '[]'::jsonb,
    submit_button_selector TEXT NOT NULL,
    submission_steps JSONB NOT NULL DEFAULT '[]'::jsonb,
    search_content TEXT NOT NULL,
    raw_blueprint JSONB NOT NULL DEFAULT '{}'::jsonb,
    embedding vector(384),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS government_schemas_embedding_hnsw_idx 
ON government_schemas 
USING hnsw (embedding vector_cosine_ops);
```
