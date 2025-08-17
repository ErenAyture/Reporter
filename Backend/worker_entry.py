# BACKEND/worker_entry.py
from celery_app import celery_app

# Run with:  python -m celery -A worker_entry worker --loglevel=info
import os
os.environ["MPLBACKEND"] = "Agg"   # <- 100 % non-GUI backend

import matplotlib                  # happens AFTER the env var
matplotlib.use("Agg", force=True)  # belt-and-suspenders
import matplotlib.pyplot as plt
plt.ioff()                         # disable interactive state