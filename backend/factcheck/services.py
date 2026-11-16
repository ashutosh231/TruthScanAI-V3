"""
Services for Fact-Checking business logic.
"""

from core.mongodb import get_factchecks_collection

def check_user_trial_limit(user):
    """
    Enforces strict 2 Free Trials Check for Non-Premium Users.
    Returns (True, None) if allowed.
    Returns (False, error_dict) if trial limit reached.
    """
    if getattr(user, "isPremium", False):
        return True, None

    factchecks_col = get_factchecks_collection()
    prior_checks_count = factchecks_col.count_documents({"user": user._id})

    if prior_checks_count >= 2:
        return False, {
            "success": False,
            "message": (
                "Trial limit reached: Free clearance is limited to 2 fact checks. "
                "Please upgrade to Premium Investigator (₹200/month) to continue scanning."
            ),
            "requiresUpgrade": True,
            "trialLimit": 2,
            "trialsUsed": prior_checks_count,
        }

    return True, None
