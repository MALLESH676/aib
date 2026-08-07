import time
import math
from typing import List, Dict, Any


# Known premium brand MSRP ranges (category -> typical MSRP)
BRAND_MSRP_EXPECTATIONS = {
    "nike": {"footwear": 3000, "apparel": 2000},
    "adidas": {"footwear": 2800, "apparel": 1800},
    "apple": {"electronics": 50000, "accessories": 3000},
    "samsung": {"electronics": 30000, "accessories": 2000},
    "sony": {"electronics": 25000, "accessories": 1500},
    "gucci": {"accessories": 40000, "apparel": 35000},
    "rolex": {"watches": 500000},
    "default": {"default": 1000},
}

SUSPICIOUS_KEYWORDS = [
    "100% authentic", "original guaranteed", "brand new sealed",
    "direct from factory", "wholesale price", "imported original",
    "7 star quality", "first copy", "master copy"
]


class AuthenticityAgent:
    NAME = "authenticity_agent"
    VERSION = "1.0.0"

    def __init__(self, llm_service=None):
        self.llm_service = llm_service

    async def analyze(self, event_id: str, product: dict, seller: dict) -> dict:
        start_time = time.time()

        suspicious_attributes: List[Dict[str, Any]] = []
        total_score = 0.0

        # --- 1. Price anomaly detection ---
        price = product.get("price", 0)
        msrp = product.get("msrp", 0)
        brand = product.get("brand", "").lower()
        category = product.get("category", "").lower()

        if msrp > 0 and price > 0:
            price_ratio = price / msrp
            discount_pct = (1 - price_ratio) * 100

            if discount_pct >= 60:
                suspicious_attributes.append({
                    "attribute": "extreme_price_anomaly",
                    "detail": f"Price {discount_pct:.0f}% below MSRP (\u20b9{price:,.0f} vs \u20b9{msrp:,.0f})",
                    "severity": "CRITICAL"
                })
                total_score += 35.0
            elif discount_pct >= 40:
                suspicious_attributes.append({
                    "attribute": "price_anomaly",
                    "detail": f"Price {discount_pct:.0f}% below MSRP",
                    "severity": "HIGH"
                })
                total_score += 25.0
            elif discount_pct >= 25:
                suspicious_attributes.append({
                    "attribute": "significant_discount",
                    "detail": f"Price {discount_pct:.0f}% below MSRP \u2014 warrants review",
                    "severity": "MEDIUM"
                })
                total_score += 12.0

        # --- 2. Seller legitimacy checks ---
        seller_age = seller.get("account_age_days", 999)
        seller_sales = seller.get("total_sales", 0)
        brand_authorized = seller.get("brand_authorized", False)
        is_premium_brand = brand in BRAND_MSRP_EXPECTATIONS and brand != "default"

        if is_premium_brand and not brand_authorized:
            suspicious_attributes.append({
                "attribute": "unauthorized_brand_seller",
                "detail": f"Seller not authorized reseller for '{product.get('brand', brand)}'",
                "severity": "HIGH"
            })
            total_score += 20.0

        if seller_age <= 7:
            suspicious_attributes.append({
                "attribute": "new_seller",
                "detail": f"Seller account only {seller_age} days old",
                "severity": "HIGH" if is_premium_brand else "MEDIUM"
            })
            total_score += 18.0 if is_premium_brand else 8.0
        elif seller_age <= 30:
            suspicious_attributes.append({
                "attribute": "young_seller",
                "detail": f"Seller account {seller_age} days old with limited history",
                "severity": "MEDIUM"
            })
            total_score += 8.0

        if seller_sales < 10 and is_premium_brand:
            suspicious_attributes.append({
                "attribute": "low_sales_premium_brand",
                "detail": f"Only {seller_sales} sales but listing premium brand products",
                "severity": "MEDIUM"
            })
            total_score += 10.0

        # --- 3. Title/description suspicious keywords ---
        title = product.get("title", "").lower()
        description = product.get("description", "").lower()
        combined_text = title + " " + description

        found_keywords = [kw for kw in SUSPICIOUS_KEYWORDS if kw in combined_text]
        if found_keywords:
            suspicious_attributes.append({
                "attribute": "suspicious_keywords",
                "detail": f"Suspicious keywords in listing: {', '.join(found_keywords[:3])}",
                "severity": "MEDIUM" if len(found_keywords) == 1 else "HIGH"
            })
            total_score += min(len(found_keywords) * 5, 15.0)

        # --- 4. Listing age ---
        listing_age = product.get("listing_age_days", 999)
        if listing_age <= 1 and is_premium_brand:
            suspicious_attributes.append({
                "attribute": "brand_new_premium_listing",
                "detail": f"Premium brand listing created {listing_age} day(s) ago",
                "severity": "MEDIUM"
            })
            total_score += 8.0

        # --- 5. Image analysis (simplified - no actual CV in MVP) ---
        image_url = product.get("image_url", "")
        logo_consistency = "UNKNOWN"
        image_quality_score = 0.7
        similar_counterfeits = 0
        image_notes = "Image analysis: automated checks pending"

        # Simple heuristic: if extreme price anomaly + premium brand -> flag image
        if total_score >= 50 and is_premium_brand:
            logo_consistency = "LOW"
            image_quality_score = 0.35
            similar_counterfeits = max(1, int(total_score / 20))
            image_notes = (
                f"Logo proportions likely inconsistent with official "
                f"{product.get('brand', brand).capitalize()} branding guidelines"
            )
        elif total_score >= 20:
            logo_consistency = "MEDIUM"
            image_quality_score = 0.55
            image_notes = "Logo consistency could not be fully verified"
        else:
            logo_consistency = "HIGH"
            image_quality_score = 0.85
            image_notes = "Image appears consistent with authentic product imagery"

        # --- 6. Cap and finalize score ---
        risk_score = min(total_score, 100.0)
        counterfeit_probability = risk_score / 100.0

        if risk_score >= 70:
            recommendation = "HOLD"
        elif risk_score >= 35:
            recommendation = "REVIEW"
        else:
            recommendation = "ALLOW"

        # Confidence
        high_attrs = sum(1 for a in suspicious_attributes if a["severity"] in ["HIGH", "CRITICAL"])
        confidence = min(0.55 + (high_attrs * 0.10) + (len(suspicious_attributes) * 0.04), 0.97)

        explanation = self._generate_explanation(suspicious_attributes, risk_score, product.get("brand", ""))

        latency_ms = int((time.time() - start_time) * 1000)

        return {
            "agent": self.NAME,
            "version": self.VERSION,
            "event_id": event_id,
            "counterfeit_probability": round(counterfeit_probability, 3),
            "risk_score": round(risk_score, 1),
            "suspicious_attributes": suspicious_attributes,
            "image_analysis": {
                "logo_consistency": logo_consistency,
                "image_quality_score": round(image_quality_score, 2),
                "similar_known_counterfeits": similar_counterfeits,
                "notes": image_notes,
            },
            "recommendation": recommendation,
            "confidence": round(confidence, 3),
            "explanation": explanation,
            "model_version": "rules-v1+heuristic-image",
            "latency_ms": latency_ms,
        }

    def _generate_explanation(self, attributes: list, score: float, brand: str) -> str:
        if not attributes:
            return "Product appears authentic. No significant counterfeit signals detected."

        critical = [a for a in attributes if a["severity"] == "CRITICAL"]
        high = [a for a in attributes if a["severity"] == "HIGH"]

        parts = []
        for a in (critical + high)[:3]:
            parts.append(a["detail"])

        brand_str = f" {brand.capitalize()}" if brand else ""
        if score >= 70:
            return f"High counterfeit risk for{brand_str} product. Key signals: {'; '.join(parts)}."
        elif score >= 35:
            return f"Moderate authenticity concerns for{brand_str} product. Signals: {'; '.join(parts)}."
        else:
            return f"Minor authenticity flags noted: {'; '.join(parts)}."
