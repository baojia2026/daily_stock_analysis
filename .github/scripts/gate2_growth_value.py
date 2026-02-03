def gate2_priority(funda):
    if funda is None or len(funda) < 2:
        return 0

    row = funda.iloc[-1]

    growth = row.get("净利润同比", 0)
    pe = row.get("市盈率", 100)

    if growth <= 0:
        return 0

    if growth > 30 and pe < 20:
        return 3    # 右下角 ⭐⭐⭐
    if growth > 20:
        return 2
    if growth > 10:
        return 1
    return 0
