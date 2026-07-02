"""Split Ugra character sheet into transparent PNG assets."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

SOURCE = Path(__file__).resolve().parents[1] / "assets" / "ugra-character-sheet.png"
OUT_DIR = Path(__file__).resolve().parents[1] / "frontend" / "public" / "assets" / "ugra"

# Regions tuned for 1024×682 source sheet (left, top, right, bottom)
REGIONS: dict[str, tuple[int, int, int, int]] = {
    # Hero
    "hero/desk": (20, 20, 340, 255),
    # Agent states — row 1
    "states/greeting": (350, 22, 478, 145),
    "states/job-search": (488, 22, 608, 145),
    "states/job-analysis": (618, 22, 748, 145),
    "states/fit-assessment": (752, 22, 872, 145),
    "states/prepare-response": (882, 22, 1010, 145),
    # Row 2
    "states/send-response": (350, 158, 478, 278),
    "states/waiting": (488, 158, 608, 278),
    "states/response-received": (618, 158, 748, 278),
    "states/invitation": (752, 158, 872, 278),
    "states/rejection": (882, 158, 1010, 278),
    # Row 3
    "states/error": (305, 295, 435, 415),
    "states/no-jobs": (445, 295, 565, 415),
    "states/success": (575, 295, 695, 415),
    "states/planning": (705, 295, 825, 415),
    "states/statistics": (835, 295, 955, 415),
    "states/save-vacancy": (895, 295, 1010, 415),  # overlaps — fix below
    "states/night-work": (895, 418, 1010, 535),
}

# Fix row 3 — 6 stickers + night work on separate positions
ROW3 = {
    "states/error": (305, 295, 435, 415),
    "states/no-jobs": (445, 295, 565, 415),
    "states/success": (575, 295, 695, 415),
    "states/planning": (705, 295, 825, 415),
    "states/statistics": (835, 295, 955, 415),
    "states/save-vacancy": (305, 418, 435, 535),
    "states/night-work": (445, 418, 565, 535),
}

TURNS = {
    "turns/front": (12, 478, 112, 638),
    "turns/three-quarter": (118, 478, 218, 638),
    "turns/side": (224, 478, 324, 638),
    "turns/back": (330, 478, 430, 638),
}

EMOTIONS = {
    "emotions/joy": (480, 478, 555, 555),
    "emotions/surprise": (560, 478, 635, 555),
    "emotions/sadness": (640, 478, 715, 555),
    "emotions/anger": (720, 478, 795, 555),
    "emotions/tired": (800, 478, 875, 555),
    "emotions/curious": (880, 478, 955, 555),
    "emotions/delighted": (950, 478, 1020, 555),
}

# Rebuild REGIONS cleanly
REGIONS = {
    "hero/desk": (20, 20, 340, 255),
    "states/greeting": (350, 22, 478, 145),
    "states/job-search": (488, 22, 608, 145),
    "states/job-analysis": (618, 22, 748, 145),
    "states/fit-assessment": (752, 22, 872, 145),
    "states/prepare-response": (882, 22, 1010, 145),
    "states/send-response": (350, 158, 478, 278),
    "states/waiting": (488, 158, 608, 278),
    "states/response-received": (618, 158, 748, 278),
    "states/invitation": (752, 158, 872, 278),
    "states/rejection": (882, 158, 1010, 278),
    **ROW3,
    **TURNS,
    **EMOTIONS,
}

# Map agent UI events → asset path
EVENT_MAP = {
    "VacancyFound": "states/job-search",
    "JobAnalyzed": "states/fit-assessment",
    "ApplicationSubmitted": "states/send-response",
    "InterviewReceived": "states/invitation",
    "InterviewScheduled": "states/invitation",
    "OfferReceived": "states/success",
    "SkillGapDetected": "states/job-analysis",
    "AgentStateChanged": "states/statistics",
    "NotificationSent": "states/response-received",
    "ResumeUpdated": "states/save-vacancy",
    "LearningCompleted": "states/planning",
    "GoalProgressUpdated": "states/planning",
    "error": "states/error",
    "idle": "states/greeting",
    "thinking": "states/job-analysis",
    "working": "states/send-response",
    "search": "states/job-search",
    "rejection": "states/rejection",
    "waiting": "states/waiting",
    "no_jobs": "states/no-jobs",
    "night": "states/night-work",
}


def remove_white_background(img: Image.Image, threshold: int = 238) -> Image.Image:
    rgba = img.convert("RGBA")
    data = np.array(rgba)
    r, g, b = data[:, :, 0], data[:, :, 1], data[:, :, 2]
    white = (r > threshold) & (g > threshold) & (b > threshold)
    # Soft edge for anti-aliased whites
    near_white = (r > threshold - 15) & (g > threshold - 15) & (b > threshold - 15)
    alpha = np.where(white, 0, 255)
    alpha = np.where(near_white & ~white, 180, alpha)
    data[:, :, 3] = alpha.astype(np.uint8)
    return Image.fromarray(data)


def trim_transparent(img: Image.Image, padding: int = 8) -> Image.Image:
    data = np.array(img)
    alpha = data[:, :, 3]
    ys, xs = np.where(alpha > 10)
    if len(xs) == 0:
        return img
    left, right = max(0, xs.min() - padding), min(img.width, xs.max() + padding)
    top, bottom = max(0, ys.min() - padding), min(img.height, ys.max() + padding)
    return img.crop((left, top, right, bottom))


def export_assets() -> dict:
    source = Image.open(SOURCE).convert("RGB")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest: dict = {"version": 1, "character": "ugra-snow-leopard", "assets": {}, "eventMap": EVENT_MAP}

    for name, box in REGIONS.items():
        cropped = source.crop(box)
        transparent = trim_transparent(remove_white_background(cropped))
        out_path = OUT_DIR / f"{name.replace('/', '-')}.png"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        transparent.save(out_path, "PNG", optimize=True)
        manifest["assets"][name] = f"/assets/ugra/{out_path.name}"
        print(f"  {name} -> {out_path.name} ({transparent.size[0]}x{transparent.size[1]})")

    manifest_path = OUT_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    print(f"Source: {SOURCE}")
    print(f"Output: {OUT_DIR}\n")
    m = export_assets()
    print(f"\nExported {len(m['assets'])} assets + manifest.json")
