#!/usr/bin/env python3
"""Shablon bankini o'qish - Kotlin bilan bir xil fayldan."""
import json, os, struct
import numpy as np

YON = os.path.join(os.path.dirname(__file__), "..", "games", "durak", "profil")


def oqi(nom):
    with open(os.path.join(YON, f"{nom}.bank"), "rb") as f:
        soni, olcham = struct.unpack("<ii", f.read(8))
        v = np.frombuffer(f.read(soni * olcham * 4), dtype="<f4").reshape(soni, olcham)
    nomlar = json.load(open(os.path.join(YON, f"{nom}.names.json")))
    return v, nomlar
