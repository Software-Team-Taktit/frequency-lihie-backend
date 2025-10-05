DIGITS = {'0': 'אפס', '1':'','2':'', '3': '', '4': '', '5': '', '6':'', '7': '', '8':'', '9':''}

def _digits_to_hebrew(s: str) -> str:
    return ''.join('נקודה' if ch == '.' else DIGITS.get(ch, ch) for ch in s)

