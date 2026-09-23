"""
edge-sim/anpr_sim.py
Simulates an Edge LPU camera publishing ANPR detections to the Central Hub.
"""

import os
import sys

# Re-use the canonical synthetic ANPR generator
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "surv")))
from workers.synthetic_anpr import main

if __name__ == "__main__":
    main()
