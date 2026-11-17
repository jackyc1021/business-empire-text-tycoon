#!/usr/bin/env python3
"""Regression checks for candidate diminishing-return math; not runtime game tests."""
import math
P=[1.0,1.1,1.15,1.2,1.3]
Q=[.7,.8,.85,.9,.95,1.0]
for q in Q:
    gains=[(lv+1)**q-lv**q for lv in range(1,101)]
    if q < 1:
        assert all(gains[i+1] < gains[i] for i in range(len(gains)-1)), q
    else:
        assert all(abs(gains[i+1]-gains[i]) < 1e-12 for i in range(len(gains)-1)), q
for p in P:
    costs=[(lv+1)**p for lv in range(1,101)]
    assert all(costs[i+1] > costs[i] for i in range(len(costs)-1))
print('PASS: diminishing marginal income and monotonic candidate costs')
