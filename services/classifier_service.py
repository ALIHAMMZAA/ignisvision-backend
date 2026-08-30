from services.context_service import get_worldcover_context


def calculate_risk(frp: float, brightness: float) -> str:
    """
    Temporary thermal-intensity risk heuristic.
    This is NOT an ML prediction.
    """

    if frp >= 20 or brightness >= 330:
        return "HIGH"

    if frp >= 10 or brightness >= 315:
        return "MEDIUM"

    return "LOW"


def classify_anomaly(anomaly: dict) -> dict:
    """
    Prototype rule-based classifier using:
    - FIRMS thermal features
    - ESA WorldCover land-cover context

    classification_confidence is a heuristic score from 0.0 to 1.0,
    NOT a calibrated ML probability.
    """

    frp = float(anomaly["frp"])
    brightness = float(anomaly["brightness"])
    firms_confidence = int(anomaly["confidence"])
    latitude = float(anomaly["latitude"])
    longitude = float(anomaly["longitude"])

    context = get_worldcover_context(latitude, longitude)

    worldcover_value = context["worldcover_value"]
    land_cover = context["land_cover_label"]

    # Start all class scores at zero.
    scores = {
        "Industrial Fire": 0.0,
        "Forest Fire": 0.0,
        "Agricultural Burn": 0.0,
        "Urban Thermal Event": 0.0,
    }

    # ---------------------------------------------------------
    # LAND-COVER EVIDENCE
    # ---------------------------------------------------------

    # Tree cover strongly supports a forest-fire hypothesis.
    if worldcover_value == 10:
        scores["Forest Fire"] += 0.70

    # Shrubland/grassland provides weaker vegetation evidence.
    elif worldcover_value in (20, 30):
        scores["Forest Fire"] += 0.25

    # Cropland strongly supports agricultural burning.
    elif worldcover_value == 40:
        scores["Agricultural Burn"] += 0.70

    # Built-up strongly supports an urban thermal event.
    elif worldcover_value == 50:
        scores["Urban Thermal Event"] += 0.70

    # ---------------------------------------------------------
    # THERMAL EVIDENCE
    # ---------------------------------------------------------

    if frp >= 20:
        for category in scores:
            scores[category] += 0.15

    elif frp >= 10:
        for category in scores:
            scores[category] += 0.10

    elif frp >= 5:
        for category in scores:
            scores[category] += 0.05

    if brightness >= 330:
        for category in scores:
            scores[category] += 0.15

    elif brightness >= 315:
        for category in scores:
            scores[category] += 0.10

    elif brightness >= 305:
        for category in scores:
            scores[category] += 0.05

    # ---------------------------------------------------------
    # INDUSTRIAL / URBAN HEURISTIC
    # ---------------------------------------------------------
    #
    # We do NOT have a dedicated industrial-source dataset yet.
    # Therefore this is only a prototype signal:
    # very strong thermal activity + built-up land.
    #
    # This must NOT be presented as verified industrial detection.

    if worldcover_value == 50 and (frp >= 20 or brightness >= 330):
        scores["Industrial Fire"] += 0.45

    # FIRMS confidence provides a small amount of supporting
    # evidence, but remains distinct from classifier confidence.
    if firms_confidence >= 80:
        for category in scores:
            scores[category] += 0.05

    # ---------------------------------------------------------
    # SELECT WINNER
    # ---------------------------------------------------------

    best_classification = max(scores, key=scores.get)
    best_score = scores[best_classification]

    # Require enough evidence before assigning a category.
    if best_score < 0.70:
        classification = "Under Analysis"
        classification_confidence = 0.0
    else:
        classification = best_classification

        # Convert heuristic score to a bounded 0.0–1.0 value.
        classification_confidence = min(best_score, 1.0)

    risk = calculate_risk(frp, brightness)

    # Only assign a concrete land-cover label when WorldCover
    # gives us a directly useful category.
    if worldcover_value == 10:
        land_cover_output = "Forest"
    elif worldcover_value == 40:
        land_cover_output = "Agricultural"
    elif worldcover_value == 50:
        land_cover_output = "Built-up"
    elif worldcover_value in (20, 30):
        land_cover_output = "Vegetated"
    else:
        land_cover_output = "Under Analysis"

    return {
        "classification": classification,
        "classification_confidence": round(
            classification_confidence,
            2,
        ),
        "land_cover": land_cover_output,
        "risk": risk,
    }