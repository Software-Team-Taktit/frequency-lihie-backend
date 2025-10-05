DIGITS = {'0': 'אפס', '1':'','2':'', '3': '', '4': '', '5': '', '6':'', '7': '', '8':'', '9':''}

def _digits_to_hebrew(s: str) -> str:
    return ''.join('נקודה' if ch == '.' else DIGITS.get(ch, ch) for ch in s)

def freq_to_phrase_he(freq_hz: float, style: str = "digits") -> str:
    if freq_hz >= 1e6:
        val = round(freq_hz/1e6, 3); unit = 'מגה-הרץ'
    elif freq_hz >= 1e3:
        val = round(freq_hz/1e3, 1); unit = 'קילו-הרץ'
    else:
        val = int(round(freq_hz)); unit = 'הרץ'
    s = f"{val}".rstrip('0').rstrip('.') if isinstance(val, float) else f"{val}"
    spoken = _digits_to_hebrew(s) if style == "digits" else s
    return f"עברו לתדר {spoken} {unit}"