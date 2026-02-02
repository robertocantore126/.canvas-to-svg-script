# Obsidian Canvas to SVG Converter
Convert your Obsidian Canvas files to beautiful, self-contained SVG images. Perfect for sharing your visual thinking, embedding in documentation, or archiving your canvas work.
🎯 Features

📝 Full Node Support - Text, files, links, and groups
🖼️ Image Embedding - Automatically embeds images as base64 (self-contained SVG)
🔗 Connections - Preserves edges with arrows and labels
🎨 Color Preservation - Maintains Obsidian's color palette
📦 Zero Dependencies - Pure Python, no external packages required
⚡ Simple CLI - One command to convert your canvas

🚀 Quick Start
bash# Basic conversion
python canvas_to_svg.py my_canvas.canvas


python canvas_to_svg.py input.canvas output.svg

Specify vault path for image resolution:
python canvas_to_svg.py canvas.canvas output.svg /path/to/vault
