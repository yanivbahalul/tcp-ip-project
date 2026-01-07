"""Modern color theme system for GUI."""

COLORS = {
    'bg_main': '#232323',
    'bg_secondary': '#2d2d2d',
    'bg_panel': '#353535',
    'bg_input': '#3d3d3d',
    'bg_hover': '#454545',
    'bg_active': '#4d4d4d',
    'bg_highlight': '#555555',
    
    'text_primary': '#e0e0e0',
    'text_secondary': '#b0b0b0',
    'text_muted': '#808080',
    'text_highlight': '#6ba3ff',
    'text_success': '#66d98f',
    'text_error': '#ff6b6b',
    'text_warning': '#ffb84d',
    
    'accent_primary': '#4a7fff',
    'accent_secondary': '#6b8fff',
    'accent_tertiary': '#8ba5ff',
    'accent_blue': '#4a7fff',
    'accent_green': '#66d98f',
    'accent_gradient_start': '#4a7fff',
    'accent_gradient_end': '#6b8fff',
    
    'btn_primary': '#4a7fff',
    'btn_primary_hover': '#3a6fef',
    'btn_secondary': '#4a7fff',
    'btn_secondary_hover': '#3a6fef',
    'btn_success': '#66d98f',
    'btn_danger': '#ff6b6b',
    'btn_disabled': '#3d3d3d',
    'btn_text': '#000000',
    
    'border_light': '#4d4d4d',
    'border_medium': '#555555',
    'border_dark': '#2d2d2d',
    'border_highlight': '#4a7fff',
    
    'chat_bg': '#232323',
    'chat_message_bg': '#2d2d2d',
    'chat_my_message_bg': '#4a7fff',
    'chat_my_message_text': '#232323',
    'chat_timestamp': '#808080',
    'chat_header_bg': '#353535',
    
    'status_online': '#66d98f',
    'status_offline': '#808080',
    'status_connecting': '#ffb84d',
    'status_error': '#ff6b6b',
    
    'list_bg': '#2d2d2d',
    'list_item_hover': '#3d3d3d',
    'list_item_selected': '#4a7fff',
    'list_item_text': '#e0e0e0',
    
    'scrollbar_bg': '#2d2d2d',
    'scrollbar_thumb': '#4d4d4d',
    'scrollbar_thumb_hover': '#5d5d5d',
}

FONTS = {
    'default': ('Segoe UI', 9),
    'small': ('Segoe UI', 8),
    'medium': ('Segoe UI', 10),
    'large': ('Segoe UI', 11),
    'bold': ('Segoe UI', 9, 'bold'),
    'heading': ('Segoe UI', 12, 'bold'),
    'title': ('Segoe UI', 14, 'bold'),
    'monospace': ('Consolas', 9),
}

SPACING = {
    'tiny': 2,
    'small': 5,
    'medium': 10,
    'large': 15,
    'xlarge': 20,
}

BORDER_RADIUS = {
    'small': 4,
    'medium': 6,
    'large': 8,
    'xlarge': 12,
}

def get_gradient_colors():
    """Return gradient colors tuple."""
    return (COLORS['accent_gradient_start'], COLORS['accent_gradient_end'])

def get_button_colors(style='primary'):
    """Return button colors dictionary for given style.
    
    Args:
        style: Button style ('primary', 'secondary', 'success', 'danger')
    
    Returns:
        Dictionary with 'bg', 'hover', and 'text' color keys
    """
    if style == 'primary':
        return {
            'bg': COLORS['btn_primary'],
            'hover': COLORS['btn_primary_hover'],
            'text': COLORS['btn_text'],
        }
    elif style == 'secondary':
        return {
            'bg': COLORS['btn_secondary'],
            'hover': COLORS['btn_secondary_hover'],
            'text': COLORS['btn_text'],
        }
    elif style == 'success':
        return {
            'bg': COLORS['btn_success'],
            'hover': COLORS['btn_primary_hover'],
            'text': '#000000',
        }
    elif style == 'danger':
        return {
            'bg': COLORS['btn_danger'],
            'hover': COLORS['btn_primary_hover'],
            'text': COLORS['btn_text'],
        }
    else:
        return {
            'bg': COLORS['bg_input'],
            'hover': COLORS['bg_hover'],
            'text': COLORS['text_primary'],
        }

