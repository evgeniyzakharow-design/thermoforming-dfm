# Contributing

Issues and pull requests are welcome, especially:

- **numbers with a source** — a rule in `references/rules.md` is only worth having if it
  says where it came from, and disagreements between sources are recorded, not averaged;
- **measurements from real parts** — the thickness model has one calibration knob
  (`grip`) and it is only as good as the parts it has been checked against. A formed part
  with measured wall thickness, sheet, tool and bubble settings is the most valuable
  contribution there is;
- fixes to the tool, with the case that failed.

Before opening a PR:

```bash
pip install -r skills/thermoforming-dfm/requirements.txt
python skills/thermoforming-dfm/scripts/vf_tool.py selftest
```

Keep `SKILL.md` short — detail belongs in `references/`. Do not add a second
implementation of draft or undercut measurement: those come from `mold_tool.py` of the
`dfm` skill, and two implementations would drift apart silently.
