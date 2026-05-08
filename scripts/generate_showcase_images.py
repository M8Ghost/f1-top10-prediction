from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont, ImageOps


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PREDICTIONS_PATH = PROJECT_ROOT / "outputs" / "predictions"
FIGURES_PATH = PROJECT_ROOT / "outputs" / "figures"
HEADSHOTS_PATH = PROJECT_ROOT / "outputs" / "driver_headshots"
SHOWCASE_PATH = FIGURES_PATH / "showcase"

DEFAULT_COMPLETED_RACES = [
    "2025_06_miami_grand_prix",
    "2025_08_monaco_grand_prix",
    "2025_12_british_grand_prix",
    "2025_18_singapore_grand_prix",
    "2025_24_abu_dhabi_grand_prix",
]

TEAM_COLORS = {
    "Red Bull": "#3671C6",
    "McLaren": "#FF8000",
    "Ferrari": "#E80020",
    "Mercedes": "#27F4D2",
    "Aston Martin": "#229971",
    "Alpine": "#0093CC",
    "Williams": "#64C4FF",
    "Racing Bulls": "#6692FF",
    "RB F1 Team": "#6692FF",
    "Haas F1 Team": "#B6BABD",
    "Kick Sauber": "#52E252",
    "Sauber": "#52E252",
}

POINTS = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create curated PNG showcase images for results and forecasts.")
    parser.add_argument("--upcoming", type=Path, default=PREDICTIONS_PATH / "upcoming_top10_predictions.csv")
    parser.add_argument("--max-upcoming-races", type=int, default=4)
    parser.add_argument("--completed-races", nargs="*", default=DEFAULT_COMPLETED_RACES)
    parser.add_argument("--output", type=Path, default=SHOWCASE_PATH)
    return parser.parse_args()


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def team_color(name: str) -> str:
    lowered = str(name).lower()
    for key, value in TEAM_COLORS.items():
        if key.lower() in lowered:
            return value
    return "#56616B"


def text_width(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.ImageFont) -> int:
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0]


def fit_text(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.ImageFont, max_width: int) -> str:
    if text_width(draw, text, fnt) <= max_width:
        return text
    value = text
    while value and text_width(draw, value + "...", fnt) > max_width:
        value = value[:-1]
    return value + "..." if value else ""


def load_headshot(code: str, size: int) -> Image.Image | None:
    path = HEADSHOTS_PATH / f"{str(code).upper()}.png"
    if not path.exists() or path.stat().st_size == 0:
        return None

    image = Image.open(path).convert("RGBA")
    image = ImageOps.contain(image, (size, size))
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.alpha_composite(image, ((size - image.width) // 2, size - image.height))

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
    canvas.putalpha(mask)
    return canvas


def draw_headshot(
    image: Image.Image,
    draw: ImageDraw.ImageDraw,
    code: str,
    box: tuple[int, int, int, int],
    border: str,
) -> None:
    x1, y1, x2, y2 = box
    size = min(x2 - x1, y2 - y1)
    cx = x1 + (x2 - x1 - size) // 2
    cy = y1 + (y2 - y1 - size) // 2
    draw.ellipse((cx, cy, cx + size, cy + size), fill="#F2F5F6", outline=border, width=5)

    headshot = load_headshot(code, size - 10)
    if headshot:
        image.alpha_composite(headshot, (cx + 5, cy + 5))
    else:
        initials = str(code).upper()[:3]
        fnt = font(26, bold=True)
        tw = text_width(draw, initials, fnt)
        draw.text((cx + size / 2 - tw / 2, cy + size / 2 - 15), initials, fill="#123C43", font=fnt)


def copy_completed_race_images(output: Path, race_ids: list[str]) -> list[Path]:
    destination = output / "completed_results"
    destination.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []

    sources = [
        ("overview", FIGURES_PATH / "predictions" / "race_overviews"),
        ("card", FIGURES_PATH / "predictions" / "race_cards"),
    ]
    for race_id in race_ids:
        for label, source_dir in sources:
            source = source_dir / f"{race_id}.png"
            if not source.exists():
                continue
            target = destination / f"{race_id}_{label}.png"
            shutil.copy2(source, target)
            copied.append(target)
    return copied


def draw_podium(
    image: Image.Image,
    draw: ImageDraw.ImageDraw,
    race_df: pd.DataFrame,
    x: int,
    y: int,
) -> None:
    title_font = font(28, True)
    small_font = font(17)
    label_font = font(19, True)
    draw.text((x, y), "Virtual podium", fill="#123C43", font=title_font)

    top3 = race_df.head(3).reset_index(drop=True)
    layout = [
        (1, x + 230, y + 70, 260, 280),
        (2, x + 20, y + 150, 230, 245),
        (3, x + 505, y + 150, 230, 245),
    ]
    rank_to_row = {index + 1: row for index, row in top3.iterrows()}
    for rank, bx, by, bw, bh in layout:
        row = rank_to_row.get(rank)
        if row is None:
            continue
        color = team_color(row["constructor_name"])
        draw.rounded_rectangle((bx, by, bx + bw, by + bh), radius=20, fill="#FFFFFF", outline="#D5DDE1", width=2)
        draw.rounded_rectangle((bx, by, bx + bw, by + 12), radius=6, fill=color)
        draw.text((bx + 16, by + 24), f"P{rank}", fill="#123C43", font=font(34, True))
        draw_headshot(image, draw, row["driver_code"], (bx + bw - 108, by + 28, bx + bw - 16, by + 120), color)
        draw.text((bx + 16, by + 84), str(row["driver_code"]), fill="#123C43", font=font(33, True))
        name = fit_text(draw, str(row["driver_name"]), small_font, bw - 32)
        draw.text((bx + 16, by + 126), name, fill="#263238", font=small_font)
        team = fit_text(draw, str(row["constructor_name"]), small_font, bw - 32)
        draw.text((bx + 16, by + 153), team, fill="#56616B", font=small_font)
        prob = float(row.get("top10_probability", 0.0)) * 100
        raw = float(row.get("predicted_finish_position_raw", rank))
        draw.text((bx + 16, by + bh - 45), f"Top10 {prob:.0f}%  |  raw P{raw:.1f}", fill="#123C43", font=label_font)


def draw_top10_table(
    image: Image.Image,
    draw: ImageDraw.ImageDraw,
    race_df: pd.DataFrame,
    x: int,
    y: int,
    width: int,
) -> None:
    draw.text((x, y), "Predicted top 10", fill="#123C43", font=font(28, True))
    row_h = 58
    start_y = y + 52
    for index, row in race_df.head(10).reset_index(drop=True).iterrows():
        rank = index + 1
        yy = start_y + index * row_h
        fill = "#FFFFFF" if index % 2 == 0 else "#F7F9FA"
        color = team_color(row["constructor_name"])
        draw.rounded_rectangle((x, yy, x + width, yy + row_h - 6), radius=12, fill=fill, outline="#E0E6EA")
        draw.rounded_rectangle((x, yy, x + 8, yy + row_h - 6), radius=5, fill=color)
        draw.text((x + 20, yy + 15), f"{rank:02d}", fill="#123C43", font=font(22, True))
        draw_headshot(image, draw, row["driver_code"], (x + 74, yy + 7, x + 121, yy + 54), color)
        draw.text((x + 136, yy + 9), str(row["driver_code"]), fill="#123C43", font=font(22, True))
        name = fit_text(draw, str(row["driver_name"]), font(17), 245)
        draw.text((x + 205, yy + 7), name, fill="#263238", font=font(17))
        team = fit_text(draw, str(row["constructor_name"]), font(14), 245)
        draw.text((x + 205, yy + 32), team, fill="#56616B", font=font(14))
        prob = float(row.get("top10_probability", 0.0)) * 100
        points = POINTS[index]
        draw.text((x + width - 230, yy + 12), f"{prob:>4.0f}% top10", fill="#123C43", font=font(18, True))
        draw.text((x + width - 92, yy + 12), f"{points} pts", fill="#D8A31A", font=font(18, True))


def render_upcoming_card(race_id: str, race_df: pd.DataFrame, output: Path) -> Path:
    race_df = race_df.sort_values(["predicted_finish_rank", "top10_probability"], ascending=[True, False]).copy()
    first = race_df.iloc[0]
    width, height = 1600, 950
    image = Image.new("RGBA", (width, height), "#EEF3F5")
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle((32, 28, width - 32, height - 28), radius=28, fill="#FFFFFF", outline="#D5DDE1", width=2)
    draw.rectangle((32, 28, width - 32, 150), fill="#123C43")
    draw.text((64, 56), f"{first['season']} {first['grand_prix']} prediction", fill="#FFFFFF", font=font(42, True))

    subtitle = (
        f"{first['race_date']} | {first['circuit_name']} | "
        f"weather: {first.get('prediction_weather_source', 'n/a')} | "
        f"qualifying: {first.get('prediction_qualifying_source', 'n/a')}"
    )
    draw.text((66, 112), subtitle, fill="#DDEDEF", font=font(18))

    note = "Forecast view generated from current model outputs. Points are virtual F1 points for the predicted top 10."
    draw.text((66, height - 72), note, fill="#56616B", font=font(18))

    draw_podium(image, draw, race_df, 76, 192)
    draw_top10_table(image, draw, race_df, 800, 190, 700)

    output.mkdir(parents=True, exist_ok=True)
    path = output / f"{race_id}_forecast_card.png"
    image.convert("RGB").save(path, quality=95)
    return path


def render_upcoming_cards(upcoming_path: Path, output: Path, max_races: int) -> list[Path]:
    if not upcoming_path.exists() or upcoming_path.stat().st_size == 0:
        return []

    df = pd.read_csv(upcoming_path)
    if df.empty:
        return []

    destination = output / "upcoming_forecasts"
    written: list[Path] = []
    for race_id in df["race_id"].drop_duplicates().head(max_races):
        race_df = df[df["race_id"] == race_id].copy()
        if race_df.empty:
            continue
        written.append(render_upcoming_card(str(race_id), race_df, destination))
    return written


def write_readme(output: Path, completed: list[Path], upcoming: list[Path]) -> None:
    lines = [
        "# Prediction Showcase PNGs",
        "",
        "This folder contains curated visual artifacts for quick project demos.",
        "",
        "## Completed 2025 Race Results",
        "",
    ]
    lines.extend(f"- `{path.relative_to(PROJECT_ROOT).as_posix()}`" for path in completed)
    lines.extend(
        [
            "",
            "## Upcoming Race Forecasts",
            "",
        ]
    )
    lines.extend(f"- `{path.relative_to(PROJECT_ROOT).as_posix()}`" for path in upcoming)
    lines.extend(
        [
            "",
            "Regenerate with:",
            "",
            "```powershell",
            "python scripts/generate_showcase_images.py",
            "```",
            "",
        ]
    )
    (output / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    output = args.output if args.output.is_absolute() else PROJECT_ROOT / args.output
    output.mkdir(parents=True, exist_ok=True)

    completed = copy_completed_race_images(output, args.completed_races)
    upcoming = render_upcoming_cards(
        args.upcoming if args.upcoming.is_absolute() else PROJECT_ROOT / args.upcoming,
        output,
        args.max_upcoming_races,
    )
    write_readme(output, completed, upcoming)

    print(f"Copied completed-race PNGs: {len(completed)}")
    print(f"Generated upcoming forecast PNGs: {len(upcoming)}")
    print(f"Showcase folder: {output}")


if __name__ == "__main__":
    main()
