from datetime import datetime


def format_date(date_string):
    """Convert YYYY-MM-DD into a readable date."""

    if not date_string:
        return None

    try:
        date_obj = datetime.strptime(date_string, "%Y-%m-%d")
        return date_obj.strftime("%d %B %Y")

    except ValueError:
        return date_string


def explain_eligibility(result):
    """
    Convert backend eligibility result into plain-language explanation.

    This function does not make or modify eligibility decisions.
    It only explains the result returned by the backend.
    """

    if not isinstance(result, dict):
        return {
            "status": "unknown",
            "explanation": "Unable to understand the provided result."
        }

    status = result.get("status")
    reason = result.get("reason", "")
    eligible_after = result.get("eligible_after")

    if status == "eligible":
        explanation = (
            "The backend has returned an eligible status. "
            "The hospital will perform the final assessment."
        )

    elif status == "not_eligible":
        explanation = (
            "The backend has returned a not eligible status. "
            "Please refer to the hospital for the final assessment."
        )

    elif status == "eligible_after":
        formatted_date = format_date(eligible_after)

        if formatted_date:
            explanation = (
                f"The backend has returned a waiting-period status. "
                f"The recorded date is {formatted_date}. "
                f"The hospital will confirm the final assessment."
            )
        else:
            explanation = (
                "The backend has returned a waiting-period status. "
                "The hospital will confirm the final assessment."
            )

    else:
        explanation = (
            "The eligibility result could not be recognized. "
            "Please refer to the original backend response."
        )

    return {
        "status": status,
        "explanation": explanation,
        "original_reason": reason,
        "eligible_after": eligible_after
    }


if __name__ == "__main__":

    test_results = [
        {
            "status": "eligible",
            "reason": "You can donate. The hospital will do the final check.",
            "eligible_after": None
        },
        {
            "status": "not_eligible",
            "reason": "You can't donate because of a medical condition.",
            "eligible_after": None
        },
        {
            "status": "eligible_after",
            "reason": "You donated recently.",
            "eligible_after": "2027-01-15"
        },
        {
            "status": "unknown",
            "reason": "Unknown result",
            "eligible_after": None
        }
    ]

    for result in test_results:

        explanation = explain_eligibility(result)

        print("\nBackend Result:")
        print(result)

        print("\nPlain-language Explanation:")
        print(explanation["explanation"])