from datetime import datetime
import calendar

print("January 2026 Calendar:")
print("=" * 40)
for day in range(5, 13):
    d = datetime(2026, 1, day)
    day_name = calendar.day_name[d.weekday()]
    is_trading = day_name not in ['Saturday', 'Sunday']
    marker = "✅ TRADING" if is_trading else "❌ CLOSED"
    print(f"{d.strftime('%Y-%m-%d')} = {day_name:9s} {marker}")
