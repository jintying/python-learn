def 算接管率(jieguan,licheng):
    """接管次数 ÷ 总里程 × 1000"""
    return jieguan / licheng * 1000

print(f"接管率：{算接管率(3, 100)} 次/千公里")\

for j, l in [(3, 100), (1, 200), (5, 250)]:
    print(f"接管率：{算接管率(j, l)} 次/千公里")