"""
Centralized text cleaning utilities for HTML/CSS content.
Provides conservative cleaning that preserves content while removing formatting.
"""

import re
from typing import Optional


def clean_html_css(content: str) -> str:
    """
    Clean HTML tags and CSS from content to produce clean plain text.
    
    This is a CONSERVATIVE approach that focuses on removing markup
    while preserving the actual text content.
    
    Args:
        content: Raw content that may contain HTML/CSS
        
    Returns:
        Cleaned plain text content
    """
    if not content:
        return ""
    
    # Remove HTML comments
    content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
    
    # Remove script and style tags with their content
    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
    content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove all HTML tags but keep the content inside
    content = re.sub(r'<[^>]+>', '', content)
    
    # Convert common HTML entities to text
    html_entities = {
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&apos;': "'",
        '&nbsp;': ' ',
        '&#8211;': '–',  # en dash
        '&#8212;': '—',  # em dash
        '&#8216;': ''',  # left single quote
        '&#8217;': ''',  # right single quote
        '&#8220;': '"',  # left double quote
        '&#8221;': '"',  # right double quote
        '&#8230;': '…',  # ellipsis
    }
    
    for entity, replacement in html_entities.items():
        content = content.replace(entity, replacement)
    
    # Remove remaining HTML entities (but be conservative)
    content = re.sub(r'&[a-zA-Z0-9#]+;', '', content)
    
    # Replace Unicode paragraph separators with regular newlines
    content = content.replace('\u2029', '\n')
    content = content.replace('\u2028', '\n')
    
    # Clean up excessive whitespace but preserve paragraph structure
    # Replace multiple spaces with single space
    content = re.sub(r'[ \t]+', ' ', content)
    
    # Replace multiple newlines with at most two newlines (preserve paragraphs)
    content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
    
    # Remove leading/trailing whitespace from each line
    lines = content.split('\n')
    lines = [line.strip() for line in lines]
    content = '\n'.join(lines)
    
    # Remove empty lines at the beginning and end
    content = content.strip()
    
    return content


def extract_plain_text(content: str, preserve_formatting: bool = True) -> str:
    """
    Extract plain text from HTML/RTF content with optional formatting preservation.
    
    Args:
        content: Content to clean
        preserve_formatting: If True, preserve paragraph breaks and basic structure
        
    Returns:
        Clean plain text
    """
    if preserve_formatting:
        return clean_html_css(content)
    else:
        # More aggressive cleaning that removes all formatting
        cleaned = clean_html_css(content)
        # Convert all whitespace to single spaces
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()