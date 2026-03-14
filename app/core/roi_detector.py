def point_in_roi(x: float, y: float, roi: tuple[int, int, int, int]) -> bool:
    x1, y1, x2, y2 = roi
    return x1 <= x <= x2 and y1 <= y <= y2