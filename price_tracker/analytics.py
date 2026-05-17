"""
Reusable price analytics for Smart Shopper.
"""

from __future__ import annotations

from typing import Iterable, Mapping


MIN_HISTORY_POINTS = 5


def analyze_price_history(
    prices: Iterable[float],
    *,
    current_price: float | None = None,
    forecast_days: int = 7,
) -> dict:
    price_list = [float(price) for price in prices]
    if len(price_list) < MIN_HISTORY_POINTS:
        raise ValueError("Not enough data for prediction yet.")

    slope, intercept = _linear_regression(price_list)

    current = float(current_price) if current_price is not None else float(price_list[-1])
    predicted_7d = max(0.0, float(intercept + slope * ((len(price_list) - 1) + forecast_days)))
    average_price = _mean(price_list)
    std_dev = _std_dev(price_list)
    volatility_ratio = (std_dev / average_price) if average_price else 0.0
    discount_pct = ((average_price - current) / average_price * 100.0) if average_price else 0.0
    deal_detected = bool(average_price and current < average_price * 0.85)

    if abs(slope) < 1e-9:
        trend = "stable"
    elif slope < 0:
        trend = "dropping"
    else:
        trend = "rising"

    change_pct = (abs(predicted_7d - current) / current * 100.0) if current else 0.0

    return {
        "trend": trend,
        "current": round(current, 2),
        "current_price": round(current, 2),
        "predicted_7d": round(predicted_7d, 2),
        "change_pct": round(change_pct, 1),
        "recommendation": "WAIT" if predicted_7d < current else "BUY NOW",
        "deal_detected": deal_detected,
        "deal_message": (
            f"Price is {round(discount_pct, 1)}% lower than the historical average."
            if deal_detected
            else "Current price is within the normal historical range."
        ),
        "average_price": round(average_price, 2),
        "volatility": classify_volatility(volatility_ratio),
        "volatility_pct": round(volatility_ratio * 100.0, 2),
        "std_dev": round(std_dev, 2),
        "data_points": len(price_list),
        "slope": round(float(slope), 4),
        "confidence": min(95, 55 + max(0, len(price_list) - MIN_HISTORY_POINTS) * 6),
    }


def summarize_watchlist_insights(
    products: Iterable[Mapping],
    histories: Mapping[int, Iterable[float]],
) -> dict:
    metrics = []

    for product in products:
        product_id = int(product["id"])
        current_price = product.get("current_price")
        history_prices = [float(price) for price in histories.get(product_id, [])]

        if current_price is None and history_prices:
            current_price = history_prices[-1]

        if current_price is None:
            continue

        current = float(current_price)
        observed_prices = history_prices or [current]
        peak_price = max(observed_prices) if observed_prices else current
        average_price = _mean(observed_prices) if observed_prices else current
        std_dev = _std_dev(observed_prices) if observed_prices else 0.0
        volatility_ratio = (std_dev / average_price) if average_price else 0.0
        drop_pct = ((peak_price - current) / peak_price * 100.0) if peak_price else 0.0

        metrics.append(
            {
                "name": product.get("name") or f"Product {product_id}",
                "drop_pct": max(0.0, drop_pct),
                "volatility_ratio": volatility_ratio,
            }
        )

    if not metrics:
        return {
            "best_deal_product": None,
            "largest_drop_pct": 0.0,
            "most_volatile_product": None,
            "average_price_drop_pct": 0.0,
        }

    best_deal = max(metrics, key=lambda item: item["drop_pct"])
    most_volatile = max(metrics, key=lambda item: item["volatility_ratio"])
    average_drop_pct = sum(item["drop_pct"] for item in metrics) / len(metrics)

    return {
        "best_deal_product": best_deal["name"],
        "largest_drop_pct": round(best_deal["drop_pct"], 1),
        "most_volatile_product": most_volatile["name"],
        "average_price_drop_pct": round(average_drop_pct, 1),
    }


def classify_volatility(volatility_ratio: float) -> str:
    if volatility_ratio < 0.03:
        return "low"
    if volatility_ratio < 0.08:
        return "medium"
    return "high"


def _load_numpy():
    try:
        import numpy as np
    except ModuleNotFoundError:
        return None

    return np


def _mean(values: list[float]) -> float:
    np = _load_numpy()
    if np is not None:
        return float(np.mean(np.asarray(values, dtype=float)))
    return sum(values) / len(values) if values else 0.0


def _std_dev(values: list[float]) -> float:
    np = _load_numpy()
    if np is not None:
        return float(np.std(np.asarray(values, dtype=float)))
    if not values:
        return 0.0
    avg = _mean(values)
    variance = sum((value - avg) ** 2 for value in values) / len(values)
    return variance ** 0.5


def _linear_regression(values: list[float]) -> tuple[float, float]:
    np = _load_numpy()
    if np is not None:
        value_array = np.asarray(values, dtype=float)
        x_axis = np.arange(len(value_array), dtype=float)
        slope, intercept = np.polyfit(x_axis, value_array, 1)
        return float(slope), float(intercept)

    count = len(values)
    if count == 1:
        return 0.0, float(values[0])

    x_values = list(range(count))
    sum_x = sum(x_values)
    sum_y = sum(values)
    sum_xy = sum(x * y for x, y in zip(x_values, values))
    sum_x2 = sum(x * x for x in x_values)
    denominator = count * sum_x2 - sum_x * sum_x

    if denominator == 0:
        return 0.0, _mean(values)

    slope = (count * sum_xy - sum_x * sum_y) / denominator
    intercept = (sum_y - slope * sum_x) / count
    return float(slope), float(intercept)
