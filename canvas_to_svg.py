#!/usr/bin/env python3
"""
Obsidian Canvas to SVG Converter

Converts Obsidian .canvas files (JSON format) to SVG images.
Supports text nodes, file nodes, links, and groups.
"""

import json
import sys
import html
import base64
import mimetypes
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional


class CanvasToSVG:
    def __init__(self, canvas_data: Dict[str, Any], vault_path: Optional[str] = None):
        self.canvas_data = canvas_data
        self.nodes = {node['id']: node for node in canvas_data.get('nodes', [])}
        self.edges = canvas_data.get('edges', [])
        self.vault_path = Path(vault_path) if vault_path else None
        
        # Calculate canvas bounds
        self.min_x, self.min_y, self.max_x, self.max_y = self._calculate_bounds()
        
        # Add padding
        self.padding = 50
        self.min_x -= self.padding
        self.min_y -= self.padding
        self.max_x += self.padding
        self.max_y += self.padding
        
        self.width = self.max_x - self.min_x
        self.height = self.max_y - self.min_y
    
    def _calculate_bounds(self) -> Tuple[float, float, float, float]:
        """Calculate the bounding box of all nodes."""
        if not self.nodes:
            return 0, 0, 800, 600
        
        min_x = min(node['x'] for node in self.nodes.values())
        min_y = min(node['y'] for node in self.nodes.values())
        max_x = max(node['x'] + node['width'] for node in self.nodes.values())
        max_y = max(node['y'] + node['height'] for node in self.nodes.values())
        
        return min_x, min_y, max_x, max_y
    
    def _transform_coords(self, x: float, y: float) -> Tuple[float, float]:
        """Transform canvas coordinates to SVG coordinates."""
        return x - self.min_x, y - self.min_y
    
    def _get_color(self, color_id: str) -> str:
        """Convert Obsidian color ID to hex color."""
        color_map = {
            '1': '#FF6B6B',  # Red
            '2': '#FFA500',  # Orange
            '3': '#FFD93D',  # Yellow
            '4': '#6BCB77',  # Green
            '5': '#4D96FF',  # Blue
            '6': '#9D84B7',  # Purple
        }
        return color_map.get(str(color_id), '#D0D0D0')
    
    def _is_image_file(self, filepath: str) -> bool:
        """Check if a file is an image based on extension."""
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.svg'}
        return Path(filepath).suffix.lower() in image_extensions
    
    def _load_image_as_base64(self, filepath: str) -> Optional[Tuple[str, str]]:
        """Load an image file and return base64 data and mime type."""
        if not self.vault_path:
            return None
        
        # Try to find the file relative to vault path
        full_path = self.vault_path / filepath
        
        if not full_path.exists():
            # Try without leading slash
            full_path = self.vault_path / filepath.lstrip('/')
        
        if not full_path.exists():
            return None
        
        try:
            # Determine mime type
            mime_type, _ = mimetypes.guess_type(str(full_path))
            if not mime_type or not mime_type.startswith('image/'):
                return None
            
            # Read and encode file
            with open(full_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            return image_data, mime_type
        except Exception as e:
            print(f"Warning: Could not load image {filepath}: {e}", file=sys.stderr)
            return None
    
    def _render_file_icon(self, svg_parts: List[str], x: float, y: float, 
                          width: float, height: float, filename: str):
        """Render a document icon for non-image files."""
        # Draw file icon (simple document shape)
        icon_x = x + width/2 - 15
        icon_y = y + 20
        svg_parts.append(
            f'<path d="M {icon_x} {icon_y} l 20 0 l 10 10 l 0 30 l -30 0 z" '
            f'fill="none" stroke="#666666" stroke-width="2"/>'
        )
        svg_parts.append(
            f'<path d="M {icon_x + 20} {icon_y} l 0 10 l 10 0" '
            f'fill="none" stroke="#666666" stroke-width="2"/>'
        )
        
        # Filename below icon
        svg_parts.append(
            f'<text x="{x + width/2}" y="{y + height - 20}" '
            f'font-family="Arial, sans-serif" font-size="12" fill="#000000" '
            f'text-anchor="middle">{filename}</text>'
        )
    
    def _wrap_text(self, text: str, max_width: int, font_size: int = 14) -> List[str]:
        """Simple text wrapping based on character count."""
        # Rough estimation: average character width is ~0.6 of font size
        chars_per_line = int(max_width / (font_size * 0.6))
        
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            word_length = len(word)
            if current_length + word_length + len(current_line) <= chars_per_line:
                current_line.append(word)
                current_length += word_length
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_length = word_length
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def _render_node(self, node: Dict[str, Any]) -> str:
        """Render a single node as SVG."""
        x, y = self._transform_coords(node['x'], node['y'])
        width = node['width']
        height = node['height']
        
        node_type = node.get('type', 'text')
        color = node.get('color')
        
        svg_parts = []
        
        # Background color
        if color:
            fill_color = self._get_color(color)
            opacity = 0.2
        else:
            fill_color = '#FFFFFF'
            opacity = 1.0
        
        # Draw rectangle
        svg_parts.append(
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}" '
            f'fill="{fill_color}" fill-opacity="{opacity}" '
            f'stroke="#888888" stroke-width="2" rx="5"/>'
        )
        
        # Add text content
        if node_type == 'text':
            text_content = node.get('text', '')
            lines = self._wrap_text(text_content, width - 20)
            
            text_y = y + 25
            for line in lines[:int(height / 20)]:  # Limit lines to fit height
                escaped_text = html.escape(line)
                svg_parts.append(
                    f'<text x="{x + 10}" y="{text_y}" '
                    f'font-family="Arial, sans-serif" font-size="14" fill="#000000">'
                    f'{escaped_text}</text>'
                )
                text_y += 20
        
        elif node_type == 'file':
            file_path = node.get('file', '')
            filename = Path(file_path).name
            escaped_filename = html.escape(filename)
            
            # Check if it's an image and try to load it
            if self._is_image_file(file_path):
                image_data = self._load_image_as_base64(file_path)
                
                if image_data:
                    base64_data, mime_type = image_data
                    
                    # Calculate image dimensions to fit within node
                    padding = 20
                    img_max_width = width - 2 * padding
                    img_max_height = height - 40  # Leave space for filename
                    
                    # Embed the image
                    svg_parts.append(
                        f'<image x="{x + padding}" y="{y + padding}" '
                        f'width="{img_max_width}" height="{img_max_height}" '
                        f'preserveAspectRatio="xMidYMid meet" '
                        f'href="data:{mime_type};base64,{base64_data}"/>'
                    )
                    
                    # Filename below image
                    svg_parts.append(
                        f'<text x="{x + width/2}" y="{y + height - 10}" '
                        f'font-family="Arial, sans-serif" font-size="12" fill="#000000" '
                        f'text-anchor="middle">{escaped_filename}</text>'
                    )
                else:
                    # Image couldn't be loaded, show icon fallback
                    self._render_file_icon(svg_parts, x, y, width, height, escaped_filename)
            else:
                # Not an image file, show document icon
                self._render_file_icon(svg_parts, x, y, width, height, escaped_filename)
        
        elif node_type == 'link':
            url = node.get('url', '')
            escaped_url = html.escape(url)
            
            # Link icon
            icon_x = x + 10
            icon_y = y + 20
            svg_parts.append(
                f'<text x="{icon_x}" y="{icon_y}" '
                f'font-family="Arial, sans-serif" font-size="20">🔗</text>'
            )
            
            # URL text
            lines = self._wrap_text(url, width - 20, 12)
            text_y = y + 50
            for line in lines[:3]:
                escaped_line = html.escape(line)
                svg_parts.append(
                    f'<text x="{x + 10}" y="{text_y}" '
                    f'font-family="Arial, sans-serif" font-size="12" fill="#0066CC">'
                    f'{escaped_line}</text>'
                )
                text_y += 18
        
        elif node_type == 'group':
            label = node.get('label', 'Group')
            escaped_label = html.escape(label)
            
            # Group label at top
            svg_parts.append(
                f'<text x="{x + 10}" y="{y + 20}" '
                f'font-family="Arial, sans-serif" font-size="16" font-weight="bold" '
                f'fill="#000000">{escaped_label}</text>'
            )
        
        return '\n'.join(svg_parts)
    
    def _render_edge(self, edge: Dict[str, Any]) -> str:
        """Render an edge (connection) between nodes."""
        from_id = edge.get('fromNode')
        to_id = edge.get('toNode')
        
        if from_id not in self.nodes or to_id not in self.nodes:
            return ''
        
        from_node = self.nodes[from_id]
        to_node = self.nodes[to_id]
        
        # Calculate connection points (center of nodes)
        from_x = from_node['x'] + from_node['width'] / 2
        from_y = from_node['y'] + from_node['height'] / 2
        to_x = to_node['x'] + to_node['width'] / 2
        to_y = to_node['y'] + to_node['height'] / 2
        
        from_x, from_y = self._transform_coords(from_x, from_y)
        to_x, to_y = self._transform_coords(to_x, to_y)
        
        # Get edge properties
        color = edge.get('color', '0')
        stroke_color = self._get_color(color) if color != '0' else '#888888'
        
        label = edge.get('label', '')
        
        svg_parts = []
        
        # Draw line
        svg_parts.append(
            f'<line x1="{from_x}" y1="{from_y}" x2="{to_x}" y2="{to_y}" '
            f'stroke="{stroke_color}" stroke-width="2" marker-end="url(#arrowhead)"/>'
        )
        
        # Add label if present
        if label:
            mid_x = (from_x + to_x) / 2
            mid_y = (from_y + to_y) / 2
            escaped_label = html.escape(label)
            
            svg_parts.append(
                f'<text x="{mid_x}" y="{mid_y - 5}" '
                f'font-family="Arial, sans-serif" font-size="12" fill="#000000" '
                f'text-anchor="middle" '
                f'style="background: white; padding: 2px;">{escaped_label}</text>'
            )
        
        return '\n'.join(svg_parts)
    
    def convert(self) -> str:
        """Convert canvas to SVG string."""
        svg_parts = []
        
        # SVG header
        svg_parts.append(
            f'<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
            f'<svg width="{self.width}" height="{self.height}" '
            f'xmlns="http://www.w3.org/2000/svg" version="1.1">'
        )
        
        # Define arrowhead marker
        svg_parts.append('''
  <defs>
    <marker id="arrowhead" markerWidth="10" markerHeight="10" 
            refX="9" refY="3" orient="auto">
      <polygon points="0 0, 10 3, 0 6" fill="#888888"/>
    </marker>
  </defs>
''')
        
        # Background
        svg_parts.append(
            f'<rect width="{self.width}" height="{self.height}" fill="#FAFAFA"/>'
        )
        
        # Render edges first (so they appear behind nodes)
        svg_parts.append('  <!-- Edges -->')
        for edge in self.edges:
            edge_svg = self._render_edge(edge)
            if edge_svg:
                svg_parts.append(f'  {edge_svg}')
        
        # Render nodes
        svg_parts.append('  <!-- Nodes -->')
        for node in self.nodes.values():
            svg_parts.append(f'  {self._render_node(node)}')
        
        # SVG footer
        svg_parts.append('</svg>')
        
        return '\n'.join(svg_parts)


def convert_canvas_to_svg(canvas_path: str, output_path: str = None, 
                          vault_path: str = None) -> str:
    """
    Convert an Obsidian canvas file to SVG.
    
    Args:
        canvas_path: Path to the .canvas file
        output_path: Path for the output SVG file (optional)
        vault_path: Path to the Obsidian vault root (for resolving image paths)
    
    Returns:
        The SVG content as a string
    """
    # Read canvas file
    with open(canvas_path, 'r', encoding='utf-8') as f:
        canvas_data = json.load(f)
    
    # If vault_path not provided, use the directory of the canvas file
    if vault_path is None:
        vault_path = Path(canvas_path).parent
    
    # Convert to SVG
    converter = CanvasToSVG(canvas_data, vault_path)
    svg_content = converter.convert()
    
    # Write to file if output path provided
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        print(f"SVG saved to: {output_path}")
    
    return svg_content


def main():
    if len(sys.argv) < 2:
        print("Usage: python canvas_to_svg.py <canvas_file> [output_file] [vault_path]")
        print("\nExamples:")
        print("  python canvas_to_svg.py my_canvas.canvas")
        print("  python canvas_to_svg.py my_canvas.canvas output.svg")
        print("  python canvas_to_svg.py my_canvas.canvas output.svg /path/to/vault")
        print("\nIf vault_path is not provided, the script will look for images")
        print("relative to the canvas file's directory.")
        sys.exit(1)
    
    canvas_file = sys.argv[1]
    
    # Generate output filename if not provided
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        output_file = Path(canvas_file).with_suffix('.svg')
    
    # Get vault path if provided
    vault_path = sys.argv[3] if len(sys.argv) > 3 else None
    
    try:
        convert_canvas_to_svg(canvas_file, str(output_file), vault_path)
        print("Conversion successful!")
    except FileNotFoundError:
        print(f"Error: Canvas file '{canvas_file}' not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: '{canvas_file}' is not a valid JSON file.")
        sys.exit(1)
    except Exception as e:
        print(f"Error during conversion: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
