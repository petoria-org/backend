def apply_sorting(qs, sort):
    """
    Apply sorting to queryset
    """
    sort_map = {
        "newest": "-created_at",
        "oldest": "created_at",
        "last_updated": "-updated_at",
    }

    event_sort_map = {
        "event_newest": "-event_time",
        "event_oldest": "event_time",
    }

    if sort in event_sort_map:
        return qs.order_by(event_sort_map[sort])

    return qs.order_by(sort_map.get(sort, "-created_at"))
