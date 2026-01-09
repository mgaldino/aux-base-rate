EVIDENCE_DB_PROMPT = """You are assigning an evidence strength in decibels (dB).
Choose ONLY from {10, 20, 30, 40}. If the evidence does not justify at least 10 dB,
return 0 and the item will be discarded.

Interpret dB as strength of evidence for the target mechanism versus plausible alternatives.
More specific, harder-to-explain evidence => higher dB.

EXAMPLE (weak)
Summary: Generic statement with limited direct support.
Direction: YES
Evidence dB: 10

EXAMPLE (strong)
Summary: Direct, specific evidence that strongly supports the mechanism and is unlikely
under alternatives.
Direction: YES
Evidence dB: 30
"""
