"""
Synthetic data generator for TrustShield demo.
Generates realistic marketplace data with fraud patterns.
"""
import random
import uuid
import json
from datetime import datetime, timedelta
from typing import List, Dict


random.seed(42)


def random_id(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex[:10]}"


def random_datetime(days_ago_min: int = 0, days_ago_max: int = 365) -> datetime:
    now = datetime.utcnow()
    delta = timedelta(days=random.uniform(days_ago_min, days_ago_max))
    return now - delta


# ─── Sellers ────────────────────────────────────────────────────────────────

def generate_legitimate_seller() -> dict:
    age = random.randint(180, 1000)
    sales = random.randint(200, 5000)
    return {
        "id": random_id("seller_"),
        "name": random.choice([
            "QuickMart Express", "TrueDeals India", "ShopRight Solutions",
            "ValueKart Pro", "FastTrack Commerce", "BestBuy Online"
        ]) + f" {random.randint(10, 99)}",
        "account_age_days": age,
        "total_sales": sales,
        "total_returns": int(sales * random.uniform(0.02, 0.08)),
        "dispute_rate": round(random.uniform(0.01, 0.06), 3),
        "avg_rating": round(random.uniform(4.0, 4.9), 1),
        "is_new_seller": False,
        "seller_tier": "established" if age > 365 else "new",
        "brand_authorized": random.random() > 0.3,
        "country": "IN",
        "created_at": (datetime.utcnow() - timedelta(days=age)).isoformat(),
    }


def generate_fraudulent_seller() -> dict:
    age = random.randint(1, 15)
    sales = random.randint(1, 20)
    return {
        "id": random_id("seller_"),
        "name": random.choice([
            "LuxuryBrands99", "AuthenticGoods4U", "DirectImport Deals",
            "OfficialBrand Shop", "PremiumOriginalsIn"
        ]) + f" {random.randint(10, 99)}",
        "account_age_days": age,
        "total_sales": sales,
        "total_returns": int(sales * random.uniform(0.20, 0.60)),
        "dispute_rate": round(random.uniform(0.15, 0.40), 3),
        "avg_rating": round(random.uniform(4.7, 5.0), 1),  # suspiciously high
        "is_new_seller": True,
        "seller_tier": "new",
        "brand_authorized": False,
        "country": "IN",
        "created_at": (datetime.utcnow() - timedelta(days=age)).isoformat(),
    }


# ─── Customers ──────────────────────────────────────────────────────────────

def generate_legitimate_customer() -> dict:
    age = random.randint(90, 730)
    orders = random.randint(5, 60)
    returns = int(orders * random.uniform(0.02, 0.10))
    return {
        "id": random_id("cust_"),
        "account_age_days": age,
        "total_orders": orders,
        "total_returns": returns,
        "return_rate": round(returns / max(orders, 1), 3),
        "cod_refusal_rate": round(random.uniform(0.0, 0.10), 3),
        "linked_device_count": 1,
        "linked_account_count": 1,
    }


def generate_fraudulent_customer() -> dict:
    age = random.randint(1, 10)
    orders = random.randint(8, 20)
    returns = int(orders * random.uniform(0.50, 0.80))
    linked_devices = random.randint(2, 5)
    return {
        "id": random_id("cust_"),
        "account_age_days": age,
        "total_orders": orders,
        "total_returns": returns,
        "return_rate": round(returns / max(orders, 1), 3),
        "cod_refusal_rate": round(random.uniform(0.30, 0.65), 3),
        "linked_device_count": linked_devices,
        "linked_account_count": linked_devices,
    }


# ─── Products ────────────────────────────────────────────────────────────────

LEGITIMATE_PRODUCTS = [
    {"title": "Samsung 65-inch 4K Smart TV", "brand": "Samsung", "category": "electronics",
     "price": 42000, "msrp": 45000, "description": "Latest Samsung QLED 4K TV with smart features and Tizen OS. 3-year warranty included."},
    {"title": "Levi's 511 Slim Fit Jeans", "brand": "Levis", "category": "apparel",
     "price": 2199, "msrp": 2499, "description": "Classic Levi's 511 slim fit jeans in dark wash. Machine washable. Original product."},
    {"title": "Prestige Induction Cooktop 2000W", "brand": "Prestige", "category": "appliances",
     "price": 1849, "msrp": 2100, "description": "Prestige induction cooktop with 7 power levels and auto shut-off. ISI marked."},
]

FRAUDULENT_PRODUCTS = [
    {"title": "Nike Air Max 270 React - 100% Original Authentic", "brand": "Nike", "category": "footwear",
     "price": 1200, "msrp": 3200, "description": "100% authentic Nike shoes direct from factory. Original guaranteed. International shipment."},
    {"title": "Apple iPhone 15 Pro - Original Sealed Box", "brand": "Apple", "category": "electronics",
     "price": 28000, "msrp": 89900, "description": "Brand new sealed Apple iPhone 15 Pro 256GB. First copy imported original. Direct import."},
    {"title": "Rolex Submariner - Authentic Swiss Made", "brand": "Rolex", "category": "watches",
     "price": 45000, "msrp": 800000, "description": "Genuine Rolex Submariner wholesale price. 7 star quality master copy. Import from Switzerland."},
]


def generate_legitimate_product() -> dict:
    template = random.choice(LEGITIMATE_PRODUCTS)
    return {
        "id": random_id("prod_"),
        "title": template["title"],
        "description": template["description"],
        "brand": template["brand"],
        "category": template["category"],
        "price": template["price"] * random.uniform(0.9, 1.1),
        "msrp": template["msrp"],
        "image_url": f"https://example.com/images/{random_id()}.jpg",
        "listing_age_days": random.randint(30, 365),
    }


def generate_fraudulent_product() -> dict:
    template = random.choice(FRAUDULENT_PRODUCTS)
    return {
        "id": random_id("prod_"),
        "title": template["title"],
        "description": template["description"],
        "brand": template["brand"],
        "category": template["category"],
        "price": template["price"] * random.uniform(0.85, 1.15),
        "msrp": template["msrp"],
        "image_url": f"https://example.com/images/{random_id()}.jpg",
        "listing_age_days": random.randint(1, 5),
    }


# ─── Reviews ─────────────────────────────────────────────────────────────────

LEGIT_REVIEW_TEXTS = [
    "Great product, exactly as described. Delivery was fast.",
    "Good quality for the price. Would recommend.",
    "Packaging was secure. Product works as expected.",
    "Decent product. Had minor issues with packaging but the item is fine.",
    "Very satisfied with this purchase. Will buy again.",
    "Product matches the description. Good seller communication.",
    "Arrived on time. Quality is acceptable for this price range.",
    "Works well. No complaints so far after two weeks of use.",
]

FAKE_REVIEW_TEXTS = [
    "Amazing product! Highly recommend this seller! Best quality!",
    "Excellent quality amazing product best seller recommend everyone!",
    "Super fast delivery amazing quality highly recommended seller!",
    "Best product ever! Amazing seller! Five stars always!",
    "Excellent purchase amazing quality fast delivery highly recommend!",
    "Outstanding product! Great seller! Very happy with purchase!",
    "Wonderful quality! Best seller on platform! Highly recommend!",
    "Fantastic product incredible quality fast shipping five stars!",
]


def generate_legitimate_reviews(product_id: str, count: int = None) -> List[dict]:
    if count is None:
        count = random.randint(3, 15)
    reviews = []
    base_time = datetime.utcnow() - timedelta(days=random.randint(10, 90))

    for i in range(count):
        offset_hours = random.uniform(0, 720)  # spread over 30 days
        ts = base_time + timedelta(hours=offset_hours)
        rating = random.choices([3, 4, 4, 5, 5], k=1)[0]
        reviews.append({
            "id": random_id("rev_"),
            "customer_id": random_id("cust_"),
            "rating": rating,
            "text": random.choice(LEGIT_REVIEW_TEXTS) + f" {'Delivery took {} days.'.format(random.randint(2, 6))}",
            "timestamp": ts.isoformat() + "Z",
            "verified_purchase": random.random() > 0.2,
        })
    return reviews


def generate_fake_reviews(product_id: str, count: int = None) -> List[dict]:
    if count is None:
        count = random.randint(10, 18)

    # Coordinated burst: all in same 20-minute window
    base_time = datetime.utcnow() - timedelta(hours=random.randint(2, 24))
    base_device = random_id("dev_")
    reviews = []

    # Create cluster of related customer IDs
    cluster_custs = [random_id("cust_") for _ in range(min(count, 8))]

    for i in range(count):
        offset_seconds = random.uniform(0, 20 * 60)  # within 20 minutes
        ts = base_time + timedelta(seconds=offset_seconds)
        cust_id = cluster_custs[i % len(cluster_custs)]
        reviews.append({
            "id": random_id("rev_"),
            "customer_id": cust_id,
            "rating": 5,
            "text": random.choice(FAKE_REVIEW_TEXTS),
            "timestamp": ts.isoformat() + "Z",
            "verified_purchase": False,
        })
    return reviews


# ─── Demo Scenarios ──────────────────────────────────────────────────────────

def build_scenario_a() -> dict:
    """Scenario A: Legitimate seller — ALLOW"""
    customer = generate_legitimate_customer()
    # Make legitimacy clear
    customer["return_rate"] = 0.04
    customer["cod_refusal_rate"] = 0.02
    customer["account_age_days"] = 420

    seller = generate_legitimate_seller()
    seller["account_age_days"] = 540
    seller["total_sales"] = 1240
    seller["dispute_rate"] = 0.02
    seller["brand_authorized"] = True

    product = generate_legitimate_product()

    return {
        "event_id": "evt_scenario_a",
        "case_type": "transaction",
        "customer": customer,
        "transaction": {
            "id": random_id("txn_"),
            "amount": float(product["price"]),
            "payment_method": "card",
            "is_first_time_buyer": False,
            "orders_last_24h": 1,
            "orders_last_7d": 3,
            "status": "completed",
        },
        "seller": seller,
        "product": product,
        "reviews": generate_legitimate_reviews(product["id"], 12),
        "device": {
            "id": random_id("dev_"),
            "linked_accounts": 1,
            "vpn_detected": False,
            "emulator_detected": False,
        },
        "review_window_hours": 24,
        "scenario_label": "A",
    }


def build_scenario_b() -> dict:
    """Scenario B: Fraud ring — HOLD"""
    customer = generate_fraudulent_customer()
    customer["return_rate"] = 0.67
    customer["cod_refusal_rate"] = 0.45
    customer["account_age_days"] = 3
    customer["linked_account_count"] = 3
    customer["linked_device_count"] = 3

    seller = generate_fraudulent_seller()
    seller["account_age_days"] = 7
    seller["total_sales"] = 12
    seller["dispute_rate"] = 0.25
    seller["brand_authorized"] = False

    product = {
        "id": random_id("prod_"),
        "title": "Nike Air Max 270 React - 100% Original Authentic",
        "description": "100% authentic Nike shoes direct from factory. Original guaranteed. International shipment.",
        "brand": "Nike",
        "category": "footwear",
        "price": 1200.0,
        "msrp": 3200.0,
        "image_url": "https://example.com/images/fake_nike.jpg",
        "listing_age_days": 2,
    }

    reviews = generate_fake_reviews(product["id"], 14)

    return {
        "event_id": "evt_scenario_b",
        "case_type": "transaction",
        "customer": customer,
        "transaction": {
            "id": random_id("txn_"),
            "amount": 1200.0,
            "payment_method": "COD",
            "is_first_time_buyer": True,
            "orders_last_24h": 5,
            "orders_last_7d": 11,
            "status": "completed",
        },
        "seller": seller,
        "product": product,
        "reviews": reviews,
        "device": {
            "id": random_id("dev_"),
            "linked_accounts": 3,
            "vpn_detected": False,
            "emulator_detected": True,
        },
        "review_window_hours": 1,
        "scenario_label": "B",
    }


def build_scenario_c() -> dict:
    """Scenario C: Ambiguous — REVIEW"""
    customer = {
        "id": random_id("cust_"),
        "account_age_days": 45,
        "total_orders": 8,
        "total_returns": 3,
        "return_rate": 0.38,
        "cod_refusal_rate": 0.22,
        "linked_device_count": 2,
        "linked_account_count": 2,
    }

    seller = {
        "id": random_id("seller_"),
        "name": "NewStyle Trends " + str(random.randint(10, 99)),
        "account_age_days": 28,
        "total_sales": 45,
        "total_returns": 8,
        "dispute_rate": 0.09,
        "avg_rating": 4.6,
        "is_new_seller": True,
        "seller_tier": "new",
        "brand_authorized": False,
        "country": "IN",
        "created_at": (datetime.utcnow() - timedelta(days=28)).isoformat(),
    }

    product = {
        "id": random_id("prod_"),
        "title": "Adidas Ultraboost Running Shoes",
        "description": "Adidas Ultraboost 22 running shoes. Imported. Original packaging.",
        "brand": "Adidas",
        "category": "footwear",
        "price": 3800.0,
        "msrp": 6500.0,
        "image_url": "https://example.com/images/adidas_ambiguous.jpg",
        "listing_age_days": 10,
    }

    # Moderately suspicious reviews: 6 reviews in 2 hours, moderate similarity
    base_time = datetime.utcnow() - timedelta(hours=3)
    reviews = []
    for i in range(6):
        ts = base_time + timedelta(minutes=random.uniform(0, 120))
        reviews.append({
            "id": random_id("rev_"),
            "customer_id": random_id("cust_"),
            "rating": random.choice([4, 5, 5, 5]),
            "text": random.choice([
                "Good product, fast delivery. Recommended!",
                "Nice quality shoes. Good seller. Fast shipping!",
                "Excellent product! Very satisfied with delivery speed.",
                "Good quality for price. Recommended seller.",
            ]),
            "timestamp": ts.isoformat() + "Z",
            "verified_purchase": random.random() > 0.5,
        })

    return {
        "event_id": "evt_scenario_c",
        "case_type": "transaction",
        "customer": customer,
        "transaction": {
            "id": random_id("txn_"),
            "amount": 3800.0,
            "payment_method": "COD",
            "is_first_time_buyer": False,
            "orders_last_24h": 2,
            "orders_last_7d": 4,
            "status": "completed",
        },
        "seller": seller,
        "product": product,
        "reviews": reviews,
        "device": {
            "id": random_id("dev_"),
            "linked_accounts": 2,
            "vpn_detected": False,
            "emulator_detected": False,
        },
        "review_window_hours": 2,
        "scenario_label": "C",
    }


DEMO_SCENARIOS = {
    "A": build_scenario_a,
    "B": build_scenario_b,
    "C": build_scenario_c,
}
