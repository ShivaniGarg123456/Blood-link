# BloodLink AI

**Owner:** Shashi

## Overview

The AI module of BloodLink processes natural-language blood requests, extracts structured information, maps free-text conditions to predefined categories, explains backend eligibility results, and detects potentially duplicate requests.

The AI module assists the system but does not make medical or donor eligibility decisions.

## Implemented Features

### 1. Blood Request Parser
- Extracts blood group (A+, A-, B+, B-, O+, O-, AB+, AB-).
- Extracts required blood units.
- Extracts hospital/location.
- Identifies urgency levels.
- Detects blood component requirements.
- Detects Hindi and English language.
- Identifies missing information.

### 2. LLM-Based Request Parser
- Uses OpenRouter API for natural-language understanding.
- Converts requests into structured JSON.
- Combines rule-based parsing with LLM extraction.
- Uses rule-based extraction as fallback when LLM fails.
- Handles incomplete requests and API errors.

### 3. Disease/Condition Mapper
- Maps free-text condition descriptions to predefined backend categories.
- Supports aliases and text normalization.
- Returns mapped categories without making medical diagnoses.

### 4. Eligibility Explanation
- Converts backend eligibility results into understandable explanations.
- Explains status and reasons.
- Formats eligibility dates.
- Does not modify backend eligibility decisions.

### 5. Duplicate Request Detector
- Normalizes request text.
- Compares requests using text similarity.
- Identifies potentially similar requests.
- Flags similar requests for manual review.
- Does not automatically reject requests.

## Technology Stack

- Python
- Pydantic
- Regular Expressions
- NLP / Text Processing
- OpenRouter API
- LLM Integration
- Pytest

## AI Module Structure

```text
AI/
├── services/
│   ├── request_parser.py
│   ├── llm_parser.py
│   ├── disease_mapper.py
│   ├── explanation.py
│   └── duplicate_detector.py
├── test_parser.py
├── test_llm_parser.py
├── test_disease_mapper.py
├── test_explanation.py
├── test_duplicate_detector.py
└── Readme.md
```

## Testing

Automated tests are implemented using pytest.

Run all AI tests:

```bash
py -3.13 -m pytest AI -v
```

Current test results:

**71 tests passed**

## Planned Features

- Speech-to-text support for Hindi and English.
- Integration with Whisper or browser speech recognition.
- Improved semantic duplicate detection.
- Further integration testing with Backend.

## Architecture Rule

The AI module never decides donor eligibility.

The Backend rules engine is responsible for eligibility decisions. The AI module only processes information and explains backend results.