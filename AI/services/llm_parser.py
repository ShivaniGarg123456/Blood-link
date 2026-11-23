import os
import json
import requests

from pathlib import Path
from dotenv import load_dotenv

from AI.services.request_parser import (
    BloodRequestParseResult,
    parse_blood_request
)


# ============================================================
# 1. LOAD ENVIRONMENT VARIABLES
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")

API_KEY = os.getenv("OPENROUTER_API_KEY")

MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "openrouter/free"
)

API_URL = "https://openrouter.ai/api/v1/chat/completions"


# ============================================================
# 2. SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are an information extraction assistant for a blood donation
request application.

Your task is to extract structured information from user messages.

Return ONLY valid JSON.

Required JSON structure:

{
    "blood_group": null,
    "units": null,
    "hospital": null,
    "component": "whole_blood",
    "urgency": "normal",
    "language": "en",
    "missing_fields": []
}

RULES:

1. Extract blood group only if explicitly mentioned.

2. Valid blood groups:
   O-, O+, A-, A+, B-, B+, AB-, AB+

3. Extract units only if explicitly mentioned.

4. Units must be between 1 and 10.

5. Extract hospital name if mentioned.

6. BLOOD COMPONENT CLASSIFICATION:

   If the user explicitly requests:
   - RBC
   - red blood cells
   - red cells
   - packed red cells
   - packed RBC

   Set component to:
   "rbc"

   If the user explicitly requests:
   - whole blood

   Set component to:
   "whole_blood"

   If the blood component is not specified:
   Set component to:
   "whole_blood"

7. urgency must be one of:
   critical, high, normal

8. Words such as:
   emergency, immediately, urgent, ASAP, turant
   indicate critical urgency.

9. Words such as:
   soon, high priority, jaldi
   indicate high urgency.

10. Otherwise urgency is normal.

11. Detect language:
    Hindi or Hinglish = hi
    English = en

12. Never invent missing information.

13. missing_fields must contain the names of missing fields:
    blood_group, units, hospital

14. Do not determine blood compatibility.

15. Do not determine donor eligibility.

16. Do not provide medical advice.

17. Return JSON only.
"""


# ============================================================
# 3. RESULT MERGING
# ============================================================

def merge_parser_results(
    rule_result: BloodRequestParseResult,
    llm_result: BloodRequestParseResult
) -> BloodRequestParseResult:

    """
    Combines rule-based and LLM parser results.

    Rule-based extracted information gets priority.
    LLM fills missing information.

    Missing fields are recalculated after merging.
    """

    print("Merging rule-based and LLM results...")


    # --------------------------------------------------------
    # BLOOD GROUP
    # --------------------------------------------------------

    blood_group = (
        rule_result.blood_group
        if rule_result.blood_group is not None
        else llm_result.blood_group
    )


    # --------------------------------------------------------
    # UNITS
    # --------------------------------------------------------

    units = (
        rule_result.units
        if rule_result.units is not None
        else llm_result.units
    )


    # --------------------------------------------------------
    # HOSPITAL
    # --------------------------------------------------------

    hospital = (
        rule_result.hospital
        if rule_result.hospital is not None
        else llm_result.hospital
    )


    # --------------------------------------------------------
    # COMPONENT
    # --------------------------------------------------------

    component = rule_result.component

    # If rule-based parser detects RBC, preserve it.
    # If rule-based parser defaults to whole_blood
    # but LLM explicitly identifies RBC, use RBC.

    if (
        component == "whole_blood"
        and llm_result.component == "rbc"
    ):

        component = "rbc"


    # --------------------------------------------------------
    # URGENCY
    # --------------------------------------------------------

    urgency_priority = {

        "normal": 1,

        "high": 2,

        "critical": 3

    }


    rule_urgency = rule_result.urgency

    llm_urgency = llm_result.urgency


    if (
        urgency_priority.get(llm_urgency, 1)
        >
        urgency_priority.get(rule_urgency, 1)
    ):

        urgency = llm_urgency

    else:

        urgency = rule_urgency


    # --------------------------------------------------------
    # LANGUAGE
    # --------------------------------------------------------

    language = rule_result.language


    # --------------------------------------------------------
    # RECALCULATE MISSING FIELDS
    # --------------------------------------------------------

    missing_fields = []


    if blood_group is None:

        missing_fields.append("blood_group")


    if units is None:

        missing_fields.append("units")


    if hospital is None:

        missing_fields.append("hospital")


    # --------------------------------------------------------
    # CREATE FINAL RESULT
    # --------------------------------------------------------

    final_result = BloodRequestParseResult(

        blood_group=blood_group,

        units=units,

        hospital=hospital,

        component=component,

        urgency=urgency,

        language=language,

        missing_fields=missing_fields

    )


    print("Result merging successful.")

    return final_result


# ============================================================
# 4. RULE-BASED FALLBACK
# ============================================================

def fallback_parser(text: str) -> BloodRequestParseResult:

    """
    Uses the existing rule-based parser when the LLM fails.
    """

    print("Using rule-based parser as fallback.")

    return parse_blood_request(text)


# ============================================================
# 5. LLM PARSER
# ============================================================

def parse_blood_request_llm(
    text: str
) -> BloodRequestParseResult:

    """
    Parses natural language blood requests.

    Workflow:

    1. Validate input.
    2. Run rule-based parser first.
    3. Return immediately if all required fields are extracted.
    4. Call OpenRouter only when information is missing.
    5. Extract response.
    6. Parse JSON.
    7. Validate using Pydantic.
    8. Merge rule-based and LLM results.
    9. Fallback if anything fails.
    """


    # --------------------------------------------------------
    # 1. EMPTY INPUT VALIDATION
    # --------------------------------------------------------

    if not text or not text.strip():

        print("Empty request received.")

        return fallback_parser(text)


    # --------------------------------------------------------
    # 2. FIRST ATTEMPT: RULE-BASED PARSING
    # --------------------------------------------------------

    print("Running rule-based parser first...")

    rule_result = parse_blood_request(text)


    # --------------------------------------------------------
    # 3. CHECK MISSING FIELDS
    # --------------------------------------------------------

    if not rule_result.missing_fields:

        print("All required fields extracted by rule-based parser.")

        print("Skipping LLM API call.")

        return rule_result


    # --------------------------------------------------------
    # 4. LLM REQUIRED
    # --------------------------------------------------------

    print("Some fields are missing.")

    print("Calling LLM for additional extraction...")


    # --------------------------------------------------------
    # 5. API KEY VALIDATION
    # --------------------------------------------------------

    if not API_KEY:

        print("OpenRouter API key not found.")

        return fallback_parser(text)


    # --------------------------------------------------------
    # 6. API HEADERS
    # --------------------------------------------------------

    headers = {

        "Authorization": f"Bearer {API_KEY}",

        "Content-Type": "application/json",

        "HTTP-Referer": "http://localhost",

        "X-Title": "BloodLink AI Parser"

    }


    # --------------------------------------------------------
    # 7. API PAYLOAD
    # --------------------------------------------------------

    payload = {

        "model": MODEL,

        "messages": [

            {

                "role": "system",

                "content": SYSTEM_PROMPT

            },

            {

                "role": "user",

                "content": text

            }

        ],

        "temperature": 0,

        "max_tokens": 300

    }


    # ========================================================
    # 8. API REQUEST
    # ========================================================

    try:

        print("Calling OpenRouter API...")


        response = requests.post(

            API_URL,

            headers=headers,

            json=payload,

            timeout=30

        )


        # ----------------------------------------------------
        # HTTP ERROR CHECK
        # ----------------------------------------------------

        response.raise_for_status()


        # ----------------------------------------------------
        # CONVERT RESPONSE INTO DICTIONARY
        # ----------------------------------------------------

        response_data = response.json()


        # ----------------------------------------------------
        # EXTRACT CHOICES
        # ----------------------------------------------------

        choices = response_data.get("choices", [])


        if not choices:

            print("No choices returned by OpenRouter.")

            return fallback_parser(text)


        message = choices[0].get("message", {})


        # ----------------------------------------------------
        # EXTRACT CONTENT
        # ----------------------------------------------------

        content = message.get("content")


        if content is None:

            print("LLM returned None content.")

            return fallback_parser(text)


        if not content.strip():

            print("LLM returned empty content.")

            return fallback_parser(text)


        # ----------------------------------------------------
        # REMOVE MARKDOWN CODE FENCES
        # ----------------------------------------------------

        content = content.strip()


        if content.startswith("```json"):

            content = content.replace("```json", "", 1)


        elif content.startswith("```"):

            content = content.replace("```", "", 1)


        if content.endswith("```"):

            content = content[:-3]


        content = content.strip()


        # ====================================================
        # 9. JSON PARSING
        # ====================================================

        try:

            parsed_data = json.loads(content)


        except json.JSONDecodeError as error:

            print("Invalid JSON returned by LLM.")

            print(f"JSON error: {error}")

            return fallback_parser(text)


        # ====================================================
        # 10. PYDANTIC VALIDATION
        # ====================================================

        try:

            llm_result = BloodRequestParseResult(

                **parsed_data

            )


            print("LLM parsing successful.")


            # ------------------------------------------------
            # MERGE RULE-BASED AND LLM RESULTS
            # ------------------------------------------------

            final_result = merge_parser_results(

                rule_result=rule_result,

                llm_result=llm_result

            )


            return final_result


        except Exception as error:

            print("Pydantic validation failed.")

            print(f"Validation error: {error}")

            return fallback_parser(text)


    # ========================================================
    # 11. ERROR HANDLING
    # ========================================================

    except requests.exceptions.Timeout:

        print("OpenRouter request timed out.")

        return fallback_parser(text)


    except requests.exceptions.HTTPError as error:

        print("OpenRouter HTTP error.")

        print(f"Error: {error}")


        # ----------------------------------------------------
        # PRINT API ERROR MESSAGE
        # ----------------------------------------------------

        try:

            print("API response:", response.text)

        except Exception:

            pass


        return fallback_parser(text)


    except requests.exceptions.RequestException as error:

        print("Network error while calling OpenRouter.")

        print(f"Error: {error}")

        return fallback_parser(text)


    except Exception as error:

        print("Unexpected LLM parser error.")

        print(f"Error: {error}")

        return fallback_parser(text)


# ============================================================
# 12. TESTING
# ============================================================

if __name__ == "__main__":

    test_requests = [

        # Complete requests - rule-based parser handles them

        "Need 3 units O negative blood at Apollo Hospital",

        "Need 2 bags AB+ blood at Fortis Hospital",


        # RBC requests

        "Need 2 units B+ RBC at AIIMS Delhi",

        "Need 3 units O- red blood cells at Apollo Hospital",

        "Need 2 units A+ packed red cells at Fortis Hospital",


        # Whole blood requests

        "Need 2 units B+ whole blood at AIIMS Delhi",


        # Requests requiring LLM

        "Mujhe 2 units B+ blood AIIMS Delhi mein urgently chahiye",

        "Please arrange blood immediately",

        "Mujhe A positive blood chahiye",

        "Mujhe 4 unit O positive blood turant chahiye"

    ]


    for request in test_requests:


        print("\n" + "=" * 60)

        print("REQUEST:", request)

        print("=" * 60)


        result = parse_blood_request_llm(request)


        print("\nRESULT:")


        print(

            json.dumps(

                result.model_dump(),

                indent=4,

                ensure_ascii=False

            )

        )