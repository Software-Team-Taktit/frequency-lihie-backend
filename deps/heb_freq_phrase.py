# deps/heb_freq_phrase.py

DIGITS = {
    '0': 'אפס',
    '1': 'אחד',
    '2': 'שתיים',
    '3': 'שלוש',
    '4': 'ארבע',
    '5': 'חמש',
    '6': 'שש',
    '7': 'שבע',
    '8': 'שמונה',
    '9': 'תשע',
}

def _digits_to_he(s: str) -> str:
    return ' '.join('נקודה' if ch == '.' else DIGITS.get(ch, ch) for ch in s)

def frequency_to_phrase_he(freq_hz: float, style: str = "digits") -> str:
    if freq_hz >= 1e6:
        val = round(freq_hz / 1e6, 3)
        unit = 'מגה־הרץ'
    elif freq_hz >= 1e3:
        val = round(freq_hz / 1e3, 1)
        unit = 'קילו־הרץ'
    else:
        val = int(round(freq_hz))
        unit = 'הרץ'

    s = f"{val}".rstrip('0').rstrip('.') if isinstance(val, float) else f"{val}"
    spoken = _digits_to_he(s) if style == "digits" else s
    return f"עברו לתדר {spoken} {unit}"

def freq_to_phrase_he(freq_hz: float, style: str = "digits") -> str:
    return frequency_to_phrase_he(freq_hz, style)
