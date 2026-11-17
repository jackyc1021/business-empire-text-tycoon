import random

def rate(level, star):
    progress = .70*((level-1)/99) + .30*((star-1)/4)
    return .65 + .20*progress

def run(n=100000, seed=20261101):
    rng=random.Random(seed)
    for _ in range(n):
        h=rng.uniform(0,16); secs=min(h,8)*3600
        theoretical=rng.uniform(0,1e9)
        level=rng.randint(1,100); star=rng.randint(1,5)
        r=rate(level,star); ad=rng.choice([True,False])
        amount=theoretical*(secs/28800)*r*(2 if ad else 1)
        assert .65-1e-12 <= r <= .85+1e-12
        assert amount <= theoretical*2+1e-6
    assert abs(rate(1,1)-.65)<1e-12
    assert abs(rate(100,5)-.85)<1e-12
    print(f'PASS: {n:,} randomized cases + boundary checks')

if __name__=='__main__': run()
