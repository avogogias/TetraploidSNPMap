"""Linkage map generation from ordered analysis results."""

import logging

logger = logging.getLogger(__name__)


def generate_linkage_map(ordered_result: dict, params: dict) -> dict:
    """Generate a linkage map from ordered markers and distances.

    Args:
        ordered_result: Ordered result with markers and inter-marker distances.
        params: Map generation parameters.

    Returns:
        Dictionary with linkage map groups, markers, and positions.
    """
    markers = ordered_result.get("ordered_markers", [])
    distances = ordered_result.get("distances", [])

    if not markers:
        return {"groups": [], "total_distance": 0.0}

    # Build positions from cumulative distances
    positions = [0.0]
    for d in distances:
        positions.append(positions[-1] + abs(d))

    # Create map entries
    map_markers = []
    for i, marker in enumerate(markers):
        pos = positions[i] if i < len(positions) else positions[-1]
        map_markers.append({
            "name": marker.get("name", f"Marker_{i}"),
            "position": round(pos, 2),
            "safe_name": marker.get("safe_name", ""),
        })

    total_distance = positions[-1] if positions else 0.0

    return {
        "groups": [
            {
                "name": "Linkage Group 1",
                "markers": map_markers,
                "total_distance": round(total_distance, 2),
            }
        ],
        "total_distance": round(total_distance, 2),
    }
