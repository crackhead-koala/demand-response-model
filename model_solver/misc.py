LRD = 8

for t in range(24):
    print('t in', list(range(t, t + LRD if t + LRD < 24 else 24)))
    if t + LRD < 24:
        print('LRD =', LRD)
    else:
        print('LRD =', 24 - t)










