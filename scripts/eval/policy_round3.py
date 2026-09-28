"""
Round 3, part D: evaluate a two-matcher selection policy offline, from the
Round 2 rows (no new matching). Policy 'P_agree', fixed before looking at its
result:
  1. both arms have a non-degenerate model with >= 15 inliers and agree within
     3 px -> ACCEPT (confirmed); report the arm with more inliers
  2. exactly one arm has a non-degenerate model with >= 15 inliers -> ACCEPT
     but mark UNCONFIRMED; report that arm
  3. otherwise -> REJECT (no registration returned)
Scored on the ground-truth families by split: an accepted answer is right if
its grid error <= 2 px. Compared with each arm alone under the same >= 15
inlier gate.
"""
import json
import numpy as np
import pandas as pd
from common import RESULTS_DIR, map_disagreement_px, save_json
from analyze_round3 import load_run

df = pd.read_csv(RESULTS_DIR / "round_2.csv")
df = df[(df.status == "OK") & df.family.str[:2].isin(["F3", "F4", "F5", "F6"])]
rows = []
for iid, g in df.groupby("id"):
    r = {a: g[g.arm == a].iloc[0] for a in g.arm}
    ok = {a: (pd.notna(x.grid_err_px) and x.n_inliers >= 15 and str(x.degenerate).lower() != "true")
          for a, x in r.items()}
    shape = (744, 248) if iid.startswith("F5") else (1024, 1024)
    H = {a: load_run(iid, a)[0] for a in r}
    agree = map_disagreement_px(H["M1_disk_lightglue"], H["M2_sift_flann"], shape) \
        if all(h is not None for h in H.values()) else None
    fam, split = g.family.iloc[0], g.split.iloc[0]
    if all(ok.values()) and agree is not None and agree <= 3:
        pick = max(r, key=lambda a: r[a].n_inliers); status = "CONFIRMED"
    elif sum(ok.values()) == 1:
        pick = [a for a in ok if ok[a]][0]; status = "UNCONFIRMED"
    elif all(ok.values()):
        pick = max(r, key=lambda a: r[a].n_inliers); status = "DISAGREE"
    else:
        pick, status = None, "REJECT"
    for name, choice, st in (("P_agree", pick, status),
                             ("DISK_alone", "M1_disk_lightglue" if ok["M1_disk_lightglue"] else None, None),
                             ("SIFT_alone", "M2_sift_flann" if ok["M2_sift_flann"] else None, None)):
        err = r[choice].grid_err_px if choice else None
        rows.append({"id": iid, "family": fam, "split": split, "policy": name, "status": st or ("ACCEPT" if choice else "REJECT"),
                     "accepted": choice is not None, "right": bool(choice and err <= 2.0),
                     "subpixel": bool(choice and err < 1.0)})
t = pd.DataFrame(rows)
out = {}
for (pol, split), g in t.groupby(["policy", "split"]):
    a = g[g.accepted]
    out[f"{pol} | {split}"] = {"instances": len(g), "accepted": int(len(a)), "right": int(a.right.sum()),
                               "wrong_accepted": int((~a.right).sum()), "subpixel": int(a.subpixel.sum()),
                               "success_rate": round(float(g.right.mean()), 3),
                               "precision": round(float(a.right.mean()), 3) if len(a) else None}
fam = t.groupby(["policy", "family"]).agg(right=("right", "sum"), n=("id", "size"),
                                          wrong=("accepted", lambda s: 0)).reset_index()
wrong = t[t.accepted & ~t.right].groupby(["policy", "family"]).size()
fam["wrong_accepted"] = [int(wrong.get((p, f), 0)) for p, f in zip(fam.policy, fam.family)]
out["by_family"] = fam.drop(columns="wrong").to_dict(orient="records")
out["status_counts_P_agree"] = {f"{k[0]} right={k[1]}": int(v) for k, v in t[t.policy == "P_agree"].groupby(["status", "right"]).size().items()}
save_json(RESULTS_DIR / "round_3_policy.json", out)
print(json.dumps(out, indent=1))
