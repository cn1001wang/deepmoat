from datetime import datetime

def generate_periods(start_year: int):
    today = datetime.today().strftime("%Y%m%d")
    periods = []

    for y in range(start_year, int(today[:4]) + 1):
        for md in ("0331", "0630", "0930", "1231"):
            p = f"{y}{md}"
            if p <= today:
                periods.append(p)

    return periods
