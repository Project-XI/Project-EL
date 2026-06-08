#!/usr/bin/env python3
"""Seed the student registry persistence file with sample records.

Usage:
  python scripts/seed_students.py

This writes `backend/data/students.json` with the sample students defined
in the Gatekeeper registry fixtures.
"""
import json
import os
from backend.src.agents.gatekeeper.registry.registry_store import SAMPLE_STUDENTS

def main():
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    out_path = os.path.join(base, 'backend', 'data', 'students.json')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    serializable = [s.to_dict() for s in SAMPLE_STUDENTS]
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(serializable, f, indent=2)
    print(f"Seeded {len(serializable)} students to {out_path}")

if __name__ == '__main__':
    main()
