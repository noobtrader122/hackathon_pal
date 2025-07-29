import os
import re
from PIL import Image, ImageDraw, ImageFont
from typing import Optional

def format_sample_inserts(test_data: str) -> Optional[str]:
    """
    Extracts up to two sets of values from test_data,
    and returns a single INSERT statement with these value tuples.
    Example:
        INSERT INTO employee VALUES (1, 'Ray', 20000), (2, 'something', 34344);
    """
    # Find table name from test_data (case insensitive)
    entity_match = re.search(r"insert into\s+(\w+)", test_data, re.IGNORECASE)
    if not entity_match:
        return None
    entity_name = entity_match.group(1)

    # Find all value tuples inside parentheses that appear after INSERT statements
    # This regex matches balanced parentheses containing anything except parentheses inside (non-greedy)
    # Simple approach assumes no nested parentheses in values.
    values = re.findall(r"\((?:[^)(]+|\([^)(]*\))*\)", test_data)
    sample_values = values[:2]  # Take first two values tuples

    if not sample_values:
        return None

    # Join the tuples with commas into a single INSERT statement
    combined_values = ", ".join(sample_values)
    return f"INSERT INTO {entity_name} VALUES {combined_values};"

def format_sample_outputs(expected_result) -> Optional[str]:
    """
    Formats a list-of-lists result as aligned text table.
    """
    if expected_result and isinstance(expected_result, list) and len(expected_result) > 0:
        cols = max(len(row) for row in expected_result)
        padded_rows = [row + [''] * (cols - len(row)) for row in expected_result]
        widths = [
            max(len(str(row[c])) for row in padded_rows)
            for c in range(cols)
        ]
        lines = []
        for row in padded_rows:
            line = " | ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row))
            lines.append(line)
        return "\n".join(lines)
    return None

def generate_table_snippet_from_testcase(testcase):
    """
    Returns a well-formatted string including CREATE TABLE,
    up to two value tuples in a single INSERT statement, and sample outputs.
    """
    if testcase is None:
        return ""
    schema_sql = testcase.test_schema.strip()
    formatted_inserts = format_sample_inserts(testcase.test_data)
    formatted_outputs = format_sample_outputs(testcase.expected_result)

    parts = [schema_sql]
    if formatted_inserts:
        parts.append("\n\nSample Inserts:\n" + formatted_inserts)
    if formatted_outputs:
        parts.append("\n\nSample Outputs:\n" + formatted_outputs)
    return "\n".join(parts)

def description_to_image(description: str, sample_table: str, image_path: str):
    """
    Render the challenge description and optional sample_table as a PNG image.
    """
    text = description
    if sample_table:
        text += "\n\nSample Table:\n" + sample_table

    # Font selection
    if os.name == "nt":  # Windows
        font_path = "C:\\Windows\\Fonts\\arial.ttf"
    else:
        # Provide your actual font path on Linux or fallback default below
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

    try:
        font = ImageFont.truetype(font_path, 20)
    except OSError:
        font = ImageFont.load_default()

    # Line wrapping (max 90 chars per line)
    lines = []
    for orig_line in text.split('\n'):
        while len(orig_line) > 90:
            split_at = orig_line.rfind(' ', 0, 90)
            if split_at == -1:
                split_at = 90
            lines.append(orig_line[:split_at])
            orig_line = orig_line[split_at:].lstrip()
        lines.append(orig_line)

    # For text size calculation using getbbox (Pillow ≥10.0)
    def get_text_size(font, text):
        bbox = font.getbbox(text)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        return width, height

    max_width = max((get_text_size(font, line)[0] for line in lines), default=700) + 24
    height_per_line = get_text_size(font, 'Ay')[1] + 4
    total_height = 30 + len(lines) * height_per_line

    image = Image.new("RGB", (max(700, max_width), total_height), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    y = 10
    for line in lines:
        draw.text((12, y), line, font=font, fill=(0, 0, 0))
        y += height_per_line

    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    image.save(image_path)
    return image_path
