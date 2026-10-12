"""Divergence engine — route water from where it is EXCESS to where it is SHORT.

Two levels:

* **within a city** — match surplus zones to deficit zones, respecting each
  donor's transferable fraction and a network loss factor;
* **between cities** — when a city cannot fix its own deficit, look for a nearby
  city with a surplus (within CROSS_CITY_MAX_DISTANCE_KM) and propose a transfer.

The **divergence index** measures how *unevenly* the water balance is spread:
    divergence = sum(|balance_i|) / (2 * total_demand)
0 = perfectly matched, higher = more water sitting in the wrong place.
"""
from __future__ import annotations

import math
from typing import Any

from config import (CROSS_CITY_MAX_DISTANCE_KM, TRANSFER_EFFICIENCY,
                    TRANSFER_MAX_FRACTION_OF_SURPLUS)


def divergence_index(balances: list[float], total_demand: float) -> float:
    if total_demand <= 0:
        return 0.0
    return round(sum(abs(b) for b in balances) / (2.0 * total_demand), 4)


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return round(2 * r * math.asin(math.sqrt(a)), 1)


def route_within_city(zones) -> dict[str, Any]:
    """Greedily move surplus -> deficit inside one city.

    Donors can give up to TRANSFER_MAX_FRACTION_OF_SURPLUS of their surplus
    (keeping a buffer); deficits are filled worst-first. A network loss factor
    reduces the water that actually arrives.
    """
    z = zones.copy()
    donors = z[z["excess_kl"] > 0].copy()
    deficits = z[z["shortage_kl"] > 0].copy()
    donors["donatable_kl"] = donors["excess_kl"] * TRANSFER_MAX_FRACTION_OF_SURPLUS

    transfers = []
    # fill the worst-off zones first
    for _, d in deficits.sort_values("shortage_risk", ascending=False).iterrows():
        need = float(d["shortage_kl"])
        for idx, dn in donors.sort_values("donatable_kl", ascending=False).iterrows():
            if need <= 1e-6:
                break
            avail = float(donors.at[idx, "donatable_kl"])
            if avail <= 1e-6:
                continue
            sent = min(avail, need / TRANSFER_EFFICIENCY)     # gross needed to deliver `need`
            delivered = sent * TRANSFER_EFFICIENCY
            donors.at[idx, "donatable_kl"] = avail - sent
            need -= delivered
            transfers.append({
                "from_zone": dn["zone_id"], "to_zone": d["zone_id"],
                "sent_kl": round(sent, 1), "delivered_kl": round(delivered, 1),
                "loss_kl": round(sent - delivered, 1),
                "efficiency": TRANSFER_EFFICIENCY,
            })

    delivered_total = sum(t["delivered_kl"] for t in transfers)
    total_shortage = float(z["shortage_kl"].sum())
    total_excess = float(z["excess_kl"].sum())
    return {
        "scope": "within-city",
        "divergence_index": divergence_index(z["balance_kl"].tolist(), float(z["pred_daily_kl"].sum())),
        "total_shortage_kl": round(total_shortage, 1),
        "total_excess_kl": round(total_excess, 1),
        "transferable_excess_kl": round(float((z["excess_kl"] * TRANSFER_MAX_FRACTION_OF_SURPLUS).sum()), 1),
        "delivered_kl": round(delivered_total, 1),
        "residual_shortage_kl": round(max(total_shortage - delivered_total, 0.0), 1),
        "transfers": transfers,
    }


def route_between_cities(city_states: list[dict]) -> dict[str, Any]:
    """Propose inter-city transfers for cities that still have a residual deficit.

    city_states: list of {city, lat, lon, residual_shortage_kl, surplus_kl}.
    """
    donors = [dict(c) for c in city_states if c.get("surplus_kl", 0) > 0]
    receivers = [c for c in city_states if c.get("residual_shortage_kl", 0) > 0]
    transfers = []
    for rec in sorted(receivers, key=lambda c: -c["residual_shortage_kl"]):
        need = rec["residual_shortage_kl"]
        candidates = []
        for dn in donors:
            if dn["city"] == rec["city"] or dn["surplus_kl"] <= 0:
                continue
            dist = haversine_km(dn["lat"], dn["lon"], rec["lat"], rec["lon"])
            if dist <= CROSS_CITY_MAX_DISTANCE_KM:
                candidates.append((dist, dn))
        for dist, dn in sorted(candidates, key=lambda x: x[0]):
            if need <= 1e-6:
                break
            avail = dn["surplus_kl"]
            if avail <= 1e-6:
                continue
            sent = min(avail, need / TRANSFER_EFFICIENCY)
            delivered = sent * TRANSFER_EFFICIENCY
            dn["surplus_kl"] -= sent
            need -= delivered
            transfers.append({
                "from_city": dn["city"], "to_city": rec["city"],
                "distance_km": dist, "sent_kl": round(sent, 1),
                "delivered_kl": round(delivered, 1), "loss_kl": round(sent - delivered, 1),
                "feasible": True,
            })
    return {
        "scope": "between-cities",
        "max_distance_km": CROSS_CITY_MAX_DISTANCE_KM,
        "transfers": transfers,
        "delivered_kl": round(sum(t["delivered_kl"] for t in transfers), 1),
        "note": ("Inter-city transfer is a planning suggestion only, capped by "
                 "distance and transferable surplus. It assumes tanker/rail feasibility."),
    }


def bearing(lat1, lon1, lat2, lon2) -> str:
    """Compass direction from point 1 to point 2."""
    dlon = math.radians(lon2 - lon1)
    y = math.sin(dlon) * math.cos(math.radians(lat2))
    x = (math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) -
         math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(dlon))
    deg = (math.degrees(math.atan2(y, x)) + 360) % 360
    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return dirs[int((deg + 22.5) // 45) % 8]


def nearest_donors(city: dict, candidates: list[dict], k: int = 3,
                   max_km: float = 500.0) -> list[dict]:
    """The nearest cities that have a water SURPLUS, with distance and direction.

    `candidates` is a list of {city, lat, lon, excess_kl, band}. Only cities with
    a positive surplus are considered; results are sorted by distance, so the
    first entry is the nearest and shortest route.
    """
    out = []
    for c in candidates:
        if c["city"] == city["city"] or c.get("excess_kl", 0) <= 0:
            continue
        d = haversine_km(city["lat"], city["lon"], c["lat"], c["lon"])
        if d > max_km:
            continue
        deliverable = c["excess_kl"] * TRANSFER_MAX_FRACTION_OF_SURPLUS * TRANSFER_EFFICIENCY
        out.append({
            "city": c["city"], "distance_km": d,
            "direction": bearing(city["lat"], city["lon"], c["lat"], c["lon"]),
            "band": c.get("band"), "surplus_kl": round(c["excess_kl"], 1),
            "deliverable_kl": round(deliverable, 1),
            "lat": c["lat"], "lon": c["lon"],
        })
    out.sort(key=lambda x: x["distance_km"])
    return out[:k]
