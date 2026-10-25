"""
MarketQuest - Text Layout & Typography Utilities
Provides accurate font-metric-aware word wrapping, clipping, truncation, and bounds checking.
Prevents text from overflowing containers across all UI components.
"""

import pygame
from typing import List, Tuple, Optional

def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> List[str]:
    """Wrap text to fit within max_width using font metrics."""
    if not text:
        return []
    
    max_width = max(10, max_width)
    paragraphs = text.split('\n')
    wrapped_lines = []

    for para in paragraphs:
        if not para:
            wrapped_lines.append("")
            continue

        words = para.split(' ')
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip() if current_line else word
            width, _ = font.size(test_line)

            if width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    wrapped_lines.append(current_line)
                    current_line = word
                else:
                    # Single word exceeds width; force character breakdown
                    acc = ""
                    for ch in word:
                        if font.size(acc + ch)[0] <= max_width:
                            acc += ch
                        else:
                            if acc:
                                wrapped_lines.append(acc)
                            acc = ch
                    current_line = acc

        if current_line:
            wrapped_lines.append(current_line)

    return wrapped_lines


def truncate_text(text: str, font: pygame.font.Font, max_width: int, ellipsis: str = "...") -> str:
    """Truncate text with ellipsis if it exceeds max_width."""
    if not text or font.size(text)[0] <= max_width:
        return text

    ell_w, _ = font.size(ellipsis)
    avail_w = max(0, max_width - ell_w)

    lo = 0
    hi = len(text)
    best = ""
    while lo <= hi:
        mid = (lo + hi) // 2
        sub = text[:mid]
        if font.size(sub)[0] <= avail_w:
            best = sub
            lo = mid + 1
        else:
            hi = mid - 1

    return best + ellipsis


def render_wrapped_text(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: Tuple[int, int, int],
    rect: pygame.Rect,
    line_spacing: int = 2,
    max_lines: Optional[int] = None
) -> int:
    """Render wrapped text strictly bounded inside rect, returning total height rendered."""
    lines = wrap_text(text, font, rect.width)
    if max_lines is not None:
        lines = lines[:max_lines]

    line_h = font.get_linesize() + line_spacing
    cur_y = rect.y
    rendered_count = 0

    # Clip to container bounds
    orig_clip = surface.get_clip()
    surface.set_clip(rect)

    try:
        for line in lines:
            if cur_y + font.get_linesize() > rect.bottom:
                break
            surf = font.render(line, True, color)
            surface.blit(surf, (rect.x, cur_y))
            cur_y += line_h
            rendered_count += 1
    finally:
        surface.set_clip(orig_clip)

    return rendered_count * line_h
