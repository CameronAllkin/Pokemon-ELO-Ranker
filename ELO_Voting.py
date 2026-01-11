import json
import random
import math
import os

DATA_LOC = "data/pokemon.json"
LIST_LOC = "data/pokemon.txt"
EXP_RATE = 0.2
CAND_TOP = 0.1


# DATA

def load_data(items):
    if os.path.exists(DATA_LOC):
        with open(DATA_LOC) as f:
            return json.load(f)
    
    return {name: {"rating": 1000, "rounds": 0} for name in items}

def save_data(data):
    with open(DATA_LOC, "w") as f:
        json.dump(data, f, indent=2)


def load_list():
    with open(LIST_LOC) as f:
        return [line.strip().lower() for line in f.readlines()]



# ELO

def expected_score(a, b):
    return 1 / (1 + math.pow(10, (b - a) / 400))

def k_factor(r):
    if r < 5: return 100
    elif r < 20: return 50
    elif r < 50: return 30
    else: return 10

def update_elo(items, a, b, winner):
    ar = items[a]["rating"]
    br = items[b]["rating"]

    ae = expected_score(ar, br)
    be = 1-ae

    if winner == a: asr, bsr = 1, 0
    else: asr, bsr = 0, 1

    ka = k_factor(items[a]["rounds"])
    kb = k_factor(items[b]["rounds"])

    items[a]["rating"] += ka * (asr - ae)
    items[b]["rating"] += kb * (bsr - be)
    items[a]["rounds"] += 1
    items[b]["rounds"] += 1



# Item Selection

def select_pair(items, init=None):
    names = list(items.keys())
    if random.random() < EXP_RATE:
        if init != None: return [init, random.choice([name for name in names if name != init])]
        else: return random.sample(names, 2)

    a = init
    if init == None:
        r = random.random()
        if r < 0.25: canditate = sorted(names, key=lambda x : items[x]["rounds"])
        elif r < 0.5: canditate = sorted(names, key=lambda x : items[x]["rating"])
        elif r < 0.75: canditate = sorted(names, key=lambda x : items[x]["rounds"], reverse=True)
        else: canditate = sorted(names, key=lambda x : items[x]["rating"], reverse=True)
        a = random.choice(canditate[:math.ceil(len(canditate)/CAND_TOP)])
    ar = items[a]["rating"]

    if random.random() > CAND_TOP:
        canditate = sorted([name for name in names if name != a], 
                           key=lambda x: abs(items[x]["rating"] - ar))
    else: 
        canditate = sorted([name for name in names if name != a], 
                           key=lambda x: abs(items[x]["rating"] - ar), reverse=True)

    b = random.choice(canditate[:math.ceil(len(canditate)*CAND_TOP)])
    return a, b



# Voting

def voting(items):
    try: 
        while True:
            os.system("cls")
            a, b = select_pair(items)

            print(f" - Vote - \n\n1) {a}\n2) {b}\ns) skip\n")
            vote = input().strip().lower()
            
            if vote == "1":
                update_elo(items, a, b, a)
            elif vote == "2":
                update_elo(items, a, b, b)
            elif vote == "s":
                continue
            else:
                continue

            save_data(items)
    except KeyboardInterrupt:
        save_data(items)

            

# Ranking

def show_ranking(items, top=10, bottom=10):
    os.system("cls")
    ranked = sorted(items.items(), key=lambda x: x[1]["rating"], reverse=True)
    length = len(ranked)
    strlen = len(str(length))

    print(" - Ranking - \n")
    for i, (name, data) in enumerate(ranked[:top]):
        print(f"{i+1:{strlen}d}. {name:20s} {data["rating"]:10.2f}")
    print("...")
    for i, (name, data) in enumerate(ranked[-bottom:]):
        print(f"{len(ranked)-bottom+i+1:{strlen}d}. {name:20s} {data["rating"]:10.2f}")
    input()



# Main

def main_loop():
    while True:
        os.system("cls")
        l = load_list()
        d = load_data(l)
        print(" - ELO Voting - \n\n1) Vote\n2) Ranking\n")
        c = input().strip().lower()
        if c == "1":
            voting(d)
        elif c == "2":
            show_ranking(d)

# main_loop()

