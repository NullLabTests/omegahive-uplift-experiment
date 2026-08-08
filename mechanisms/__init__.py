"""Cognitive mechanisms, added to the hive one at a time by the uplift loop.

Every module in this directory is auto-registered by hive/hooks.py if it
defines NAME and HOOKS. Mechanisms may wrap the AtomSpace, retrieval, or the
planning loop. They may NEVER touch loop/ or eval_ecology/ internals.
"""
