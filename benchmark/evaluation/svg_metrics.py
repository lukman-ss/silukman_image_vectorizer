import gzip
import os
import re
from typing import Dict, Union

import defusedxml.ElementTree as defused_ET
import xml.etree.ElementTree as ET


class SVGComplexityCalculator:
    """
    Analyzes the complexity of an SVG file.
    
    Security:
    Uses `defusedxml` to prevent XML vulnerabilities (Billion Laughs, quadratic blowup, 
    external entity expansion).
    
    Metrics:
    - path_count: Number of <path> elements.
    - group_count: Number of <g> elements.
    - element_count: Total number of XML elements.
    - fill_count / stroke_count: Occurrences of fill and stroke (attributes or styles).
    - unique_colors: Count of unique color definitions found.
    - total_commands: Total number of path commands (M, C, L, Z, etc.).
    - command_distribution: Dictionary of command frequencies.
    - estimated_coordinates: Approximate number of float coordinates in paths.
    - svg_bytes / compressed_svg_bytes: File sizes (uncompressed vs gzip).
    - width / height / viewBox: Dimensions from the root element.
    """
    
    # Regex to extract letters (commands) from path 'd' attribute
    # Letters are M, m, Z, z, L, l, H, h, V, v, C, c, S, s, Q, q, T, t, A, a
    RE_COMMANDS = re.compile(r'[MmLlHhVvCcSsQqTtAaZz]')
    
    # Regex to extract numeric coordinates (handles scientific notation and decimals)
    RE_COORDS = re.compile(r'[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?')

    def __init__(self):
        pass

    def _extract_colors(self, elem: ET.Element) -> list:
        colors = []
        
        # Check direct attributes
        if 'fill' in elem.attrib:
            colors.append(elem.attrib['fill'].strip().lower())
        if 'stroke' in elem.attrib:
            colors.append(elem.attrib['stroke'].strip().lower())
            
        # Check style attribute
        if 'style' in elem.attrib:
            styles = elem.attrib['style'].split(';')
            for style in styles:
                if ':' in style:
                    key, val = style.split(':', 1)
                    key = key.strip().lower()
                    val = val.strip().lower()
                    if key in ('fill', 'stroke') and val != 'none':
                        colors.append(val)
        return colors

    def _remove_namespace(self, tag: str) -> str:
        if '}' in tag:
            return tag.split('}', 1)[1]
        return tag

    def calculate(self, svg_path: str) -> Dict[str, Union[int, float, str, Dict]]:
        if not os.path.exists(svg_path):
            return {"error": f"File not found: {svg_path}"}
            
        try:
            # Safely parse XML
            tree = defused_ET.parse(svg_path)
            root = tree.getroot()
        except Exception as e:
            return {"error": f"Failed to parse SVG: {str(e)}"}
            
        metrics = {
            "path_count": 0,
            "group_count": 0,
            "total_element_count": 0,
            "fill_count": 0,
            "stroke_count": 0,
            "total_path_command_count": 0,
            "command_distribution": {},
            "estimated_coordinate_count": 0,
            "svg_bytes": os.path.getsize(svg_path),
            "compressed_svg_bytes": 0,
            "width": root.attrib.get('width', ""),
            "height": root.attrib.get('height', ""),
            "viewBox": root.attrib.get('viewBox', "")
        }
        
        # Calculate gzip size
        with open(svg_path, 'rb') as f:
            raw_data = f.read()
            metrics["compressed_svg_bytes"] = len(gzip.compress(raw_data))
            
        unique_colors = set()
        
        for elem in root.iter():
            metrics["total_element_count"] += 1
            tag = self._remove_namespace(elem.tag)
            
            if tag == 'path':
                metrics["path_count"] += 1
                
                # Analyze path 'd' string
                d_str = elem.attrib.get('d', '')
                
                commands = self.RE_COMMANDS.findall(d_str)
                coords = self.RE_COORDS.findall(d_str)
                
                metrics["total_path_command_count"] += len(commands)
                metrics["estimated_coordinate_count"] += len(coords)
                
                for cmd in commands:
                    cmd_upper = cmd.upper()
                    metrics["command_distribution"][cmd_upper] = metrics["command_distribution"].get(cmd_upper, 0) + 1
                    
            elif tag == 'g':
                metrics["group_count"] += 1
                
            # Count fills and strokes (approximate)
            colors = self._extract_colors(elem)
            for c in colors:
                if c != 'none':
                    unique_colors.add(c)
                
            if 'fill' in elem.attrib or ('style' in elem.attrib and 'fill:' in elem.attrib['style']):
                metrics["fill_count"] += 1
            if 'stroke' in elem.attrib or ('style' in elem.attrib and 'stroke:' in elem.attrib['style']):
                metrics["stroke_count"] += 1
                
        metrics["unique_color_count"] = len(unique_colors)
        
        return metrics
