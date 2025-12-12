# core/util.py
import math

def clamp(v, lo, hi): return max(lo, min(hi, v))

def kinematics_angles_to_actuators(a1_deg, a2_deg, A=0.05416666666/2, B=0.05416666666/2, max_mm=3):
    a1 = math.radians(a1_deg); a2 = math.radians(a2_deg)
    act1 = 180*(A*math.tan(a1) + B*math.tan(a2))
    act2 = 180*(A*math.tan(a1) - B*math.tan(a2))
    return clamp(act1, -max_mm, max_mm)+3, clamp(act2, -max_mm, max_mm)+3