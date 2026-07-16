import re

def parse_mentions(text: str) -> list[dict]:
    """
    Parse mentions from text.
    Returns a list of dicts containing raw match, username, and position.
    """
    if not text:
        return []
    
    # Regex to match @mentions
    pattern = re.compile(r"@([a-zA-Z0-9_\-\.]+)")
    results = []
    for match in pattern.finditer(text):
        raw = match.group(0)
        username = match.group(1)
        # Avoid trailing dots or punctuation being captured as part of username
        # e.g., "@alice." -> username "alice"
        if username.endswith('.'):
            username = username[:-1]
            raw = raw[:-1]
            end_pos = match.end() - 1
        else:
            end_pos = match.end()
            
        results.append({
            "raw": raw,
            "username": username,
            "position": {
                "start": match.start(),
                "end": end_pos
            }
        })
    return results
