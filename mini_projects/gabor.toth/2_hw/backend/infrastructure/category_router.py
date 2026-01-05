"""Category routing implementation using OpenAI."""

from typing import List, Dict, Optional
import json
import openai

from domain.models import CategoryDecision
from domain.interfaces import CategoryRouter


class OpenAICategoryRouter(CategoryRouter):
    """LLM-based category router using OpenAI Chat Completions."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model

    async def generate_description(
        self,
        category: str,
        new_document_title: str,
        new_document_snippet: str,
        existing_description: Optional[str] = None
    ) -> str:
        """Generate or enhance category description based on uploaded documents.
        
        Args:
            category: Category name
            new_document_title: Title of the newly uploaded document
            new_document_snippet: First 500 chars of document content
            existing_description: Current description (if any)
        
        Returns:
            Enhanced description text
        """
        prompt = f"""You are a document categorizer. Your task is to create or enhance a category description based on uploaded documents.

Category name: "{category}"
New document title: "{new_document_title}"
New document content (first 500 chars): "{new_document_snippet}"
"""
        
        if existing_description:
            prompt += f"""Current category description: "{existing_description}"

Task: Enhance the existing description to include the new document's topics and content type.
- Keep the core essence of the existing description
- Add new topics/keywords from the new document
- Make it more comprehensive
"""
        else:
            prompt += """Task: Create a concise, comprehensive description for this category based on the document.
- Describe what topics/documents this category contains
- Include keywords that would help LLM routing
- Be specific and technical where applicable
"""
        
        prompt += """
Return ONLY the new description text (no JSON, no quotes, plain text, 1-2 sentences max)."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=200
            )
            
            description = response.choices[0].message.content.strip()
            print(f"[DescriptionGen] Category: {category}")
            print(f"[DescriptionGen] New description: {description}")
            return description
            
        except Exception as e:
            print(f"[DescriptionGen] Error: {e}")
            # Fallback
            return f"Dokumentumok a '{category}' kategóriához"

    async def decide_category(
        self, question: str, available_categories: List[str]
    ) -> CategoryDecision:
        """Decide which category to search based on question."""
        categories_str = ", ".join(available_categories) if available_categories else "none"

        prompt = f"""Te egy magyar dokumentum-kategorizáló asszisztens vagy.

A felhasználó kérdése: "{question}"

Elérhető kategóriák: {categories_str}

SZABÁLYOK:
1. Analizáld, hogy a kérdés kapcsolódik-e VALAMELYIK kategóriához
2. Válaszolj JSON formátumban, CSAK ezekkel a mezőkkel:
   - "category": a lista pontos kategóriája (string), vagy null ha nincs match
   - "reason": rövid magyar magyarázat (string)
3. NE használj markdown-t, CSAK JSON

KRITIKUS: Legyél BEFOGADÓ! Ha az elérhető dokumentumokból válaszolható a kérdés, akkor annak a kategóriát válaszd!

Példák:
- Kérdés: "Mit jelent a groundedness?" + kategóriák="ai" → {{"category": "ai", "reason": "A groundedness RAG-es koncepció"}}
- Kérdés: "Milyen az idő?" + kategóriák="ai" → {{"category": null, "reason": "Az idő nem kapcsolódik a dokumentumokhoz"}}

Emlékeztesd: Az "ai" kategória AI technológiákat, vektoradatbázisokat, RAG-et tartalmaz.
"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,  # Lower temp for more consistency
        )

        response_text = response.choices[0].message.content.strip()
        print(f"[CategoryRouter] Question: {question}")
        print(f"[CategoryRouter] Available: {available_categories}")
        print(f"[CategoryRouter] Raw response: {response_text}")

        # Parse JSON response
        try:
            data = json.loads(response_text)
            category = data.get("category")
            reason = data.get("reason", "")

            # Validate: category must be in available list or None
            if category is not None and category not in available_categories:
                print(f"[CategoryRouter] Category '{category}' not in list, setting to None")
                category = None
                reason = f"Kategória '{category}' nem szerepel a felsorolt kategóriák között."

            print(f"[CategoryRouter] Final decision: category={category}, reason={reason}")
            return CategoryDecision(category=category, reason=reason)
        except json.JSONDecodeError as e:
            print(f"[CategoryRouter] JSON parse error: {e}")
            # Fallback: no category matched
            return CategoryDecision(
                category=None,
                reason="Kategória eldöntése sikertelen."
            )

    async def route(
        self, question: str, available_categories: List[str], 
        descriptions_text: str = ""
    ) -> str:
        """Match question to category using descriptions.
        
        Args:
            question: User's question/query
            available_categories: List of category slugs
            descriptions_text: Formatted descriptions of categories
        
        Returns:
            Best matching category slug or None
        """
        if not available_categories:
            return None
        
        if len(available_categories) == 1:
            return available_categories[0]
        
        # Build detailed category instructions
        category_list = "\n".join([f"  - {cat}" for cat in available_categories])
        
        prompt = f"""You are a Hungarian document categorizer. Your task is to route the user's question to the BEST matching document category.

USER QUESTION:
"{question}"

AVAILABLE DOCUMENT CATEGORIES:
{descriptions_text}

VALID CATEGORY SLUGS (you MUST choose one from this list):
{category_list}

MATCHING INSTRUCTIONS:
1. Carefully read the user's question and understand what information they need
2. Review each category's description to understand its content
3. Find the category whose documents would BEST answer the user's question
4. Consider both direct matches (same topic) and indirect matches (related topics)
5. IMPORTANT: You MUST return one of the valid category slugs listed above

RESPONSE FORMAT:
Return ONLY a valid JSON object (no markdown, no code blocks):
{{"category": "<category slug>", "reasoning": "<brief Hungarian explanation (1 sentence)>"}}

Remember: The category must be EXACTLY one of the valid slugs listed above."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,  # Very low temp for consistent matching
            )

            response_text = response.choices[0].message.content.strip()
            print(f"[Router] Question: {question}")
            print(f"[Router] Categories: {available_categories}")
            print(f"[Router] Raw response: {response_text}")
            
            # Try to parse JSON
            data = json.loads(response_text)
            category = data.get("category")
            reasoning = data.get("reasoning", "")
            
            # Validate category is in available list
            if category not in available_categories:
                print(f"[Router] ⚠️ Invalid category '{category}' (not in {available_categories})")
                # Try to find closest match
                category = None
                for avail_cat in available_categories:
                    if avail_cat.lower() in response_text.lower():
                        category = avail_cat
                        print(f"[Router] Found partial match: {category}")
                        break
                
                if not category:
                    category = available_categories[0] if available_categories else None
                    print(f"[Router] No match found, using first category: {category}")
            
            print(f"[Router] ✓ Final category: {category}, reasoning: {reasoning}")
            return category
            
        except json.JSONDecodeError as e:
            print(f"[Router] ❌ JSON parse error: {e}")
            print(f"[Router] Raw response was: {response_text}")
            # Fallback: try to find category name in response
            for avail_cat in available_categories:
                if avail_cat.lower() in response_text.lower():
                    print(f"[Router] Found category in response: {avail_cat}")
                    return avail_cat
            return available_categories[0] if available_categories else None
        except Exception as e:
            print(f"[Router] ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return available_categories[0] if available_categories else None