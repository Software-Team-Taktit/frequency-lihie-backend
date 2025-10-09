DIGITS = {
    '0': 'אפס',
    '1': 'אחת',
    '2': 'שתיים',
    '3': 'שלוש',
    '4': 'ארבע',
    '5': 'חמש',
    '6': 'שש',
    '7': 'שבע',
    '8': 'שמונה',
    '9': 'תשע',
}

TENS = ["", "עשר", "עשרים", "שלושים", "ארבעים", "חמישים", "שישים", "שבעים", "שמונים", "תשעים"]
THOUSANDS = ["", "", "", "שלושת", "ארבעת" , "חמשת", "ששת", "שבעת", "שמונת", "תשעת"]

def teens(n: int) -> str:
    return f"{DIGITS[n-11]} עשרה"

def two_digits(n: int) -> str:
    if n == 0:
        return ""
    if n < 10:
        return DIGITS[n]
    if 10 < n < 20:
        return teens(n)
    if n == 10:
        return "עשר"
    t, o = divmod(n, 10)
    return TENS[t] if o == 0 else f"{TENS[t]} ו{two_digits(o)}"

def hundreds(n: int) -> str:
    if n < 100: return two_digits(n)
    h, r = divmod(n, 100)
    if h == 1: head = "מאה"
    elif h == 2: head = "מאתיים"
    else: head = f"{DIGITS[h]} מאות"
    return head if r == 0 else f"{head} {two_digits(r)}"

def thousands(k: int) -> str:
    if k == 0: return ""
    if k == 1: return "אלף"
    if k == 2: return "אלפיים"
    if 3 <= k <= 10: return f"{THOUSANDS[k]} אלפים"
    return f"{int_to_hebrew(k)} אלף"

def int_to_hebrew(n: int) -> str:
    if n == 0:
        return "לא אושר עבורך תדר"
    th, r = divmod(n, 1000)
    
    parts = []
    if th:
        parts.append(thousands(th))
    if r:
        parts.append(hundreds(r))
    return " ".join(parts)