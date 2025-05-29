def escape_markup(text: str) -> str:
    """Escape square brackets for Textual markup."""
    return text.replace("[", "\[").replace("]", "\]")