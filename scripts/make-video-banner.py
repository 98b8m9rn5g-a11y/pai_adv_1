"""Render caption text once, avoiding font-shaping differences in FFmpeg."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parents[1]
font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", 24)
canvas = Image.new("RGB", (1280, 110), "#111111")
draw = ImageDraw.Draw(canvas)
lines = [
    "日本語の指示で動くAI配送ロボット（外部APIなし）",
    "緑＝受付／橙＝倉庫｜指示をAIで分類 → ROS 2で自動移動",
    "文字TF-IDF＋ロジスティック回帰／学習48件／障害物のない固定2地点",
]
for i, line in enumerate(lines):
    assert draw.textlength(line, font=font) < 1240
    draw.text((20, 6 + 33 * i), line, font=font, fill="white")
out = root / "simulation/video-banner.png"
canvas.save(out)
print(out)
