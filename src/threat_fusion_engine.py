def combine_risks(network_risk, user_risk):

    final_risk = (0.6 * network_risk) + (0.4 * user_risk)

    if final_risk > 0.8:
        level = "CRITICAL"
    elif final_risk > 0.6:
        level = "HIGH"
    elif final_risk > 0.4:
        level = "MEDIUM"
    else:
        level = "LOW"

    return final_risk, level