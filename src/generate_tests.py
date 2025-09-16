
import os
import argparse
import base64
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
#api_key = os.getenv("OPENAI_API_KEY")
content = """
You are a senior QA strategist and web UI/UX analyst. Your job is to generate a high-quality, test-planning blueprint for a website using only a single screenshot of a webpage. You must infer testable features and interactions from visible UI. Be precise, cautious, and explicit about uncertainties. Output only JSON conforming exactly to the schema below. No prose outside JSON.

Inputs
- screenshot: an image of the webpage at a specific moment. You will receive this as the conversation’s image input.
- optional_hints:
  - known_url: {KNOWN_URL or null}
  - device_hint: {DESKTOP|TABLET|MOBILE or null}
  - notes: {FREE_TEXT or null}

Objective
From the screenshot, produce a structured test plan identifying:
- UI components and their likely roles/interactions.
- Feature areas to test, with concise rationale and priorities.
- Potential user flows present or implied.
- Accessibility, responsiveness, cross-browser, i18n, and other global checks.
- Ambiguities, assumptions, and open questions for follow-up.
- A brief coverage and risk summary.

Critical rules
- Base all findings on what is visible or reasonably implied by standard web conventions; never invent backend logic or hidden features.
- Mark anything speculative as inferred and include confidence scores (0.0–1.0).
- Provide short justifications (max two sentences each). Do not provide chain-of-thought or step-by-step internal reasoning.
- If you cannot determine a field, use null or an empty array. Do not fabricate facts.
- Use stable component IDs like "cmp-001", "cmp-002", etc.
- Bounding boxes must be normalized to the image: 0.0–1.0 for x, y, w, h with four decimal places.
- Be concise and deterministic.

What to analyze from the screenshot
1) Page context: infer page type (e.g., landing, product, article), viewport category (desktop/tablet/mobile), theme (light/dark), and key visual cues.
2) Components: locate and classify visible UI components (buttons, links, inputs, selects, checkboxes, radios, textareas, search bars, nav bars, menus/hamburgers, breadcrumbs, tabs, accordions, carousels, cards, tables, banners/hero, modals/dialogs, toasts, footers/headers, pagination, sliders, video, images/icons, cookie banners, badges/chips, sidebars).
   - For each: id, type, visible text/label, bbox_pct, state hints (e.g., disabled, hoverable, expanded), inferred actions (click/tap/type/hover/scroll/drag), and confidence.
3) Text extraction: list notable visible strings and map them to the nearest component where applicable.
4) Features/Test areas: group related components into test areas (e.g., Navigation, Search, Authentication, Forms, Content Display, Media, E‑commerce CTAs, Filters/Sorting, Notifications/Toasts, Cookie Consent, Footer links, etc.).
   - For each area: summary, rationale (<=2 sentences), priority (P1/P2/P3), concise test ideas, edge cases, accessibility checks, cross-browser and responsiveness notes, i18n notes, data dependencies, related component IDs, inferred flag, and confidence.
5) User flows: identify any likely flows (e.g., Sign up, Contact submission, Add to cart, Download, Newsletter subscribe, Book a demo).
   - Include start components, step actions and expected visible outcomes (high-level), assumptions, priority, and confidence.
6) Global checks: propose accessibility, responsiveness (breakpoints to consider), i18n (RTL, long strings), performance hints visible from UI (e.g., heavy hero media), security-related UI hints (e.g., password fields, sensitive inputs), analytics/cookie consent, SEO-visible hints (e.g., heading hierarchy).
7) Uncertainties and open questions: call out what you can’t determine from a single screenshot and what to clarify.
8) Coverage summary: estimate coverage of critical UI components and top residual risks.

Output format (JSON only)
Return exactly one JSON object conforming to this schema. Use the specified enums and value ranges.

{
  "metadata": {
    "known_url": string|null,
    "device_hint": "DESKTOP"|"TABLET"|"MOBILE"|null,
    "notes": string|null,
    "assumptions": [string]
  },
  "page_context": {
    "title_guess": string|null,
    "page_type_guess": "LANDING"|"LISTING"|"DETAIL"|"ARTICLE"|"DASHBOARD"|"FORM"|"AUTH"|"CHECKOUT"|"OTHER"|null,
    "viewport_guess": "DESKTOP"|"TABLET"|"MOBILE"|null,
    "theme_guess": "LIGHT"|"DARK"|null,
    "confidence": number
  },
  "components": [
    {
      "id": "cmp-001",
      "type": "BUTTON"|"LINK"|"INPUT"|"SELECT"|"TEXTAREA"|"CHECKBOX"|"RADIO"|"SEARCH"|"NAV"|"MENU"|"HAMBURGER"|"BREADCRUMB"|"TAB"|"ACCORDION"|"CAROUSEL"|"CARD"|"TABLE"|"BANNER"|"HERO"|"MODAL"|"TOAST"|"FOOTER"|"HEADER"|"PAGINATION"|"SLIDER"|"VIDEO"|"IMAGE"|"ICON"|"COOKIE_BANNER"|"SIDEBAR"|"BADGE"|"CHIP"|"OTHER",
      "label_text": string|null,
      "visible_text": [string],
      "bbox_pct": {"x": number, "y": number, "w": number, "h": number},
      "state_hints": [ "PRIMARY"|"SECONDARY"|"DISABLED"|"HOVERABLE"|"FOCUSABLE"|"SELECTED"|"EXPANDED"|"COLLAPSED" ],
      "inferred_actions": [ "CLICK"|"TAP"|"TYPE"|"HOVER"|"SCROLL"|"DRAG" ],
      "confidence": number
    }
  ],
  "user_flows": [
    {
      "name": string,
      "priority": "P1"|"P2"|"P3",
      "starts_with": ["cmp-001"],
      "steps": [
        { "action": "CLICK"|"TYPE"|"SELECT"|"SCROLL"|"HOVER"|"NAVIGATE", "on": "cmp-001", "expected_ui_result": string }
      ],
      "assumptions": [string],
      "confidence": number
    }
  ],
  "test_areas": [
    {
      "feature": string,
      "related_components": ["cmp-001"],
      "summary": string,
      "rationale": string,
      "priority": "P1"|"P2"|"P3",
      "confidence": number,
      "test_ideas": [string],
      "edge_cases": [string],
      "accessibility_checks": [string],
      "cross_browser_notes": [string],
      "responsiveness_notes": [string],
      "i18n_notes": [string],
      "data_dependencies": [string],
      "inferred": boolean
    }
  ],
  "global_checks": {
    "accessibility": [string],
    "responsiveness": [string],
    "i18n": [string],
    "performance_hints": [string],
    "security_ui_hints": [string],
    "analytics_cookies": [string],
    "seo_hints": [string]
  },
  "uncertainties": [string],
  "open_questions": [string],
  "coverage_summary": {
    "critical_components_total": number,
    "covered_components": number,
    "coverage_pct": number,
    "top_risks": [string]
  }
}

Generation directives
- Keep rationale and explanations brief (<= 2 sentences each).
- Use normalized bbox_pct with four decimals (0.0000–1.0000).
- Prioritize findings with highest user impact and failure risk as P1.
- Avoid backend assumptions; focus on what can be validated from the UI or through typical UI interactions.
- If the screenshot lacks elements for a category (e.g., no visible search), omit that test area or mark it inferred with low confidence if strongly suggested by UI conventions.
- Output only valid JSON as specified.

Runtime variable binding
- Inject optional_hints. If absent, set fields to null and add an assumption noting lack of hints.
"""
def generate_test_cases(image_path, prompt):
    """
    Sends an image to OpenAI and saves the response.

    Args:
        image_path (str): The path to the image file.
        prompt (str): The prompt to send to OpenAI.
    """
    # Get the OpenAI API key from environment variables
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set.")
        return

    client = OpenAI(api_key=api_key)

    # Encode the image in base64
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": content
                },

                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
        )

        # Create the output directory
        output_dir = "Generated_Test_Cases"
        os.makedirs(output_dir, exist_ok=True)

        # Save the response
        test_case_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(image_path))[0]}_test_cases.txt")
        with open(test_case_path, "w", encoding="utf-8") as f:
            f.write(response.choices[0].message.content)
        print(f"Test cases saved to {test_case_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    image_name = 'x_screenshot.png'
    prompt = "Inputs:known_url: \"https://x.com\"\n  - device_hint: \"DESKTOP\"\n  - notes: \"Focus on all the actionable elements.\"\nObjective: Produce a structured test plan."
    print("CWD:", os.getcwd())

    image_path = os.path.join("../scraped_data", image_name)

    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")
    else:
        generate_test_cases(image_path, prompt)
