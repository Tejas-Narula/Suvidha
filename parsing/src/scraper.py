import re
import logging
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Page, Browser

logger = logging.getLogger(__name__)

class GovernmentWebScraper:
    """
    Playwright + BeautifulSoup Scraper for Government Portals:
    - Renders dynamic JavaScript-heavy single-page applications and portals.
    - Discovers service categories, navigation links, and grievance forms.
    - Sanitizes and structures DOM elements into token-optimized representations for Groq LLM.
    """
    def __init__(self, headless: bool = True, timeout_ms: int = 30000):
        self.headless = headless
        self.timeout_ms = timeout_ms

    async def fetch_page_content(self, url: str) -> Dict[str, Any]:
        """
        Loads the URL in Playwright Chromium, waits for dynamic DOM rendering,
        and returns the full HTML along with discovered links and page metadata.
        """
        async with async_playwright() as p:
            browser: Browser = await p.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-setuid-sandbox"
                ]
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800}
            )
            page: Page = await context.new_page()

            try:
                logger.info(f"Navigating to {url}...")
                await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                # Wait for any dynamic scripts or spinners to finish
                try:
                    await page.wait_for_load_state("networkidle", timeout=8000)
                except Exception:
                    pass  # Some gov sites stream or poll constantly

                # Extract title and rendered HTML
                title = await page.title()
                html = await page.content()
                current_url = page.url

                # Discover interactive links and service buttons
                discovered_links = await self._discover_service_links(page, current_url)

                return {
                    "url": current_url,
                    "title": title,
                    "html": html,
                    "discovered_links": discovered_links
                }
            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
                raise
            finally:
                await browser.close()

    async def _discover_service_links(self, page: Page, base_url: str) -> List[Dict[str, str]]:
        """
        Discovers links and buttons related to services, forms, grievances, certificates, and applications.
        Supports both English and Hindi/Regional government portal terms.
        """
        service_keywords = [
            "service", "grievance", "complaint", "apply", "register", "citizen", 
            "portal", "track", "status", "scheme", "shikayat", "sewa", "pension", 
            "certificate", "ration", "water", "electricity", "tax", "municipal", "form",
            "servicesandschemes", "servicedetails", "details", "lodge", "pramanpatra",
            "सेवा", "योजना", "शिकायत", "आवेदन", "पंजीकरण", "प्रमाणपत्र", "लॉग इन",
            "मूलनिवास", "जाति", "राजस्व", "अप्लाई", "हेल्पलाइन"
        ]
        
        links = await page.eval_on_selector_all(
            "a[href], button, [role='button'], .btn",
            """elements => elements.map(el => ({
                text: (el.innerText || el.textContent || '').trim().replace(/\\s+/g, ' '),
                href: el.getAttribute('href') || '',
                id: el.getAttribute('id') || '',
                className: el.getAttribute('class') || '',
                tagName: el.tagName.toLowerCase()
            }))"""
        )

        filtered = []
        seen_urls = set()
        for item in links:
            text = item.get("text", "")
            href = item.get("href", "")
            if not href or href.startswith("#") or href.startswith("javascript:"):
                continue

            full_url = urljoin(base_url, href)
            # Same origin or government subdomain links
            if urlparse(full_url).netloc and full_url not in seen_urls:
                text_lower = text.lower()
                href_lower = href.lower()
                if any(kw in text_lower or kw in href_lower for kw in service_keywords):
                    seen_urls.add(full_url)
                    filtered.append({
                        "text": text,
                        "url": full_url,
                        "tag": item.get("tagName", ""),
                        "selector": f"#{item['id']}" if item.get("id") else f"a[href='{href}']"
                    })

        return filtered[:30]

    def sanitize_and_extract_form_dom(self, html: str, base_url: str) -> Dict[str, Any]:
        """
        Uses BeautifulSoup to remove boilerplate/noise and extracts clean,
        structured interactive form elements, buttons, and instructional content.
        """
        soup = BeautifulSoup(html, "html.parser")

        # 1. Strip script, style, svg, header/footer boilerplate to save token context
        for element in soup(["script", "style", "noscript", "svg", "header", "footer", "nav"]):
            element.decompose()

        # 2. Extract Headings and Instructions
        headings = [h.get_text(strip=True) for h in soup.find_all(["h1", "h2", "h3"]) if h.get_text(strip=True)]
        
        # 3. Extract Form Fields
        form_elements = []
        raw_inputs = soup.find_all(["input", "select", "textarea"])

        for idx, el in enumerate(raw_inputs):
            tag_name = el.name
            input_type = el.get("type", "text").lower() if tag_name == "input" else tag_name
            if input_type in ["hidden", "submit", "button", "reset"]:
                continue

            el_id = el.get("id", "")
            el_name = el.get("name", "")
            el_placeholder = el.get("placeholder", "")
            el_required = el.has_attr("required") or el.get("aria-required") == "true"

            # Derive human label from <label for="..."> or parent label or preceding text
            label_text = ""
            if el_id:
                lbl = soup.find("label", attrs={"for": el_id})
                if lbl:
                    label_text = lbl.get_text(strip=True)
            if not label_text and el.parent and el.parent.name == "label":
                label_text = el.parent.get_text(strip=True)
            if not label_text:
                label_text = el_placeholder or el_name or el_id or f"Field {idx+1}"

            # Options for dropdowns
            options = []
            if tag_name == "select":
                for opt in el.find_all("option"):
                    opt_val = opt.get("value", "").strip()
                    opt_txt = opt.get_text(strip=True)
                    if opt_txt and opt_val:
                        options.append(f"{opt_txt} (value={opt_val})")

            # Determine best CSS selector
            if el_id:
                css_selector = f"#{el_id}"
            elif el_name:
                css_selector = f"{tag_name}[name='{el_name}']"
            else:
                css_selector = f"{tag_name}:nth-of-type({idx+1})"

            form_elements.append({
                "label": label_text,
                "input_type": input_type,
                "css_selector": css_selector,
                "name": el_name,
                "id": el_id,
                "placeholder": el_placeholder,
                "is_required": el_required,
                "options": options[:15]  # limit options preview
            })

        # 4. Extract Submit and Action Buttons
        action_buttons = []
        buttons = soup.find_all(["button", "input"])
        for btn in buttons:
            btn_type = btn.get("type", "").lower()
            btn_text = btn.get_text(strip=True) or btn.get("value", "")
            if btn.name == "button" or btn_type in ["submit", "button"]:
                btn_id = btn.get("id", "")
                btn_name = btn.get("name", "")
                if btn_id:
                    selector = f"#{btn_id}"
                elif btn_name:
                    selector = f"{btn.name}[name='{btn_name}']"
                elif btn_text:
                    selector = f"{btn.name}:has-text('{btn_text}')"
                else:
                    selector = f"{btn.name}[type='{btn_type}']"

                action_buttons.append({
                    "text": btn_text or "Submit",
                    "type": btn_type or "button",
                    "selector": selector
                })

        # 5. Extract General Informational Text / Instructions (e.g. guidelines for filing)
        paragraphs = [p.get_text(strip=True) for p in soup.find_all(["p", "li"]) if len(p.get_text(strip=True)) > 20]
        instruction_text = "\n".join(paragraphs[:10])

        return {
            "headings": headings,
            "instruction_text": instruction_text,
            "form_elements": form_elements,
            "action_buttons": action_buttons
        }
