import sys, time; sys.path.insert(0, "runs")
import w3_calibrate as W
t=time.time(); df, scores, el, pat, pooled, names = W.setup()
print("setup ok", round(time.time()-t,1), "s; pooled S =", pooled["capability"].shape)
