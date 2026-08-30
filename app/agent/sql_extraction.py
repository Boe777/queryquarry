import re

_FENCE = re.compile(r"```(?:sql)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)
_LEADING_LABEL = re.compile(r"^\s*(sql|query|answer)\s*:\s*", re.IGNORECASE)


def extract_sql(raw: str) -> str:
    text = raw.strip()

    fenced = _FENCE.search(text)
    if fenced:
        text = fenced.group(1)

    text = _LEADING_LABEL.sub("", text.strip())

    return text.strip().rstrip(";").strip()
