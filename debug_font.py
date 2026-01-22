import os
import sys
from subtitle_exporter import SubtitleExporter
import config

print(f"Config Font Path: {config.SUBTITLE_FONT_PATH}")
if os.path.exists(config.SUBTITLE_FONT_PATH):
    print("✓ Font file exists")
else:
    print("✗ Font file DOES NOT exist")

exporter = SubtitleExporter()
print(f"Detected Font Name: '{exporter.font_name}'")

if exporter.font_name == "Archivo Black":
    print("✓ SUCCESS: Archivo Black detected correctly")
else:
    print(f"✗ FAILURE: Expected 'Archivo Black', got '{exporter.font_name}'")
