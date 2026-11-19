"""Figure for the W1-J blocker: log density of J in tau_alpha, and the tail plateau of 1/2 log I_m. Reads runs/W/W1J/{propriety,checks}.json."""
import json
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
r = json.load(open("runs/W/W1J/propriety.json")); ch = json.load(open("runs/W/W1J/checks.json"))
f, ax = plt.subplots(1, 2, figsize=(9, 3.5))
t = [x["tau_alpha"] for x in r["profile_tau_alpha"]]
ax[0].loglog(t, [x["log_density_in_tau_given_w"] for x in r["profile_tau_alpha"]], "o-", color="tab:green", label="hyperprior + J potential")
ax[0].loglog(t, [abs(x["log_hyperprior"]) + 0.1 for x in r["profile_tau_alpha"]], "s--", color="tab:red", label="|hyperprior| alone, +0.1")
ax[0].set_xlabel(r"$\tau_\alpha$"); ax[0].set_ylabel("log density in $\\tau_\\alpha$, up to a constant"); ax[0].legend(fontsize=8)
ax[0].set_title("J rises without bound in $\\tau_\\alpha$", fontsize=9)
d = ch["d_tail_behaviour"]
ax[1].plot(d["c_grid"], d["half_log_I_m"], "o-", color="tab:green"); ax[1].axhline(d["limit_half_log_sum_a2"], ls=":", color="k")
ax[1].set_xlabel("capability $c$ of one model, others fixed"); ax[1].set_ylabel(r"$\frac{1}{2}\log I_m$")
ax[1].set_title("tails plateau at $\\frac{1}{2}\\log\\sum_b a_b^2$ (dotted)", fontsize=9)
f.tight_layout(); f.savefig("runs/W/W1J/fig_J_propriety.png", dpi=110)
