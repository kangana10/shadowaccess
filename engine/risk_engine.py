# risk_engine.py

def calculate_risk(session_data):
    """
    Calculates a risk score (0-100) and assigns a risk level based on session anomalies.
    Returns a dictionary response for easy integration with backend APIs.
    """
    score = 0
    reasons = []

    # Rule 1: Typing speed change (+20)
    if session_data.get("typing_speed_changed") == True:
        score += 20
        reasons.append("Typing speed changed significantly")

    # Rule 2: Mouse movement anomaly (+20)
    if session_data.get("mouse_anomaly") == True:
        score += 20
        reasons.append("Unusual mouse movement detected")

    # Rule 3: Rapid downloads (+30)
    if session_data.get("rapid_downloads") == True:
        score += 30
        reasons.append("Rapid download activity detected")

    # Rule 4: IP / Location change (+20)
    if session_data.get("ip_changed") == True:
        score += 20
        reasons.append("Session IP or location changed")

    # Rule 5: Repeated failed action (+10)
    if session_data.get("failed_actions") == True:
        score += 10
        reasons.append("Repeated failed actions recorded")

    # Assign Risk Level based on score
    if score >= 70:
        level = "Critical / Lock"
        action = "Block Session"
    elif score >= 30:
        level = "Warning"
        action = "Require Verification"
    else:
        level = "Normal"
        action = "Allow"

    return {
        "user_id": session_data.get("user_id"),
        "risk_score": score,
        "risk_level": level,
        "recommended_action": action,
        "reasons": reasons
    }


# --- TEST SCENARIOS ---
if __name__ == "__main__":
    normal_session = {
        "user_id": "user_001",
        "typing_speed_changed": False,
        "mouse_anomaly": False,
        "rapid_downloads": False,
        "ip_changed": False,
        "failed_actions": False
    }

    warning_session = {
        "user_id": "user_002",
        "typing_speed_changed": True,
        "mouse_anomaly": False,
        "rapid_downloads": False,
        "ip_changed": True,
        "failed_actions": False
    }

    critical_session = {
        "user_id": "user_003",
        "typing_speed_changed": True,
        "mouse_anomaly": True,
        "rapid_downloads": True,
        "ip_changed": False,
        "failed_actions": True
    }

    print("--- SCENARIO 1 ---")
    print(calculate_risk(normal_session))

    print("\n--- SCENARIO 2 ---")
    print(calculate_risk(warning_session))

    print("\n--- SCENARIO 3 ---")
    print(calculate_risk(critical_session))