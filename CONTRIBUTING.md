# Contributing

Thanks for helping improve J.A.R.V.I.S.

## What we want

- focused plugins
- safer defaults
- clearer docs
- smaller, testable changes

## Before you open a PR

1. Run the tests:
   ```bash
   python -m unittest discover -s tests
   ```
2. Make sure new config values are documented.
3. Keep new plugins self-contained and registered through `register_plugin()`.
4. Prefer feature flags for optional behavior.

## Plugin guidelines

- Keep plugin functions short and explicit.
- Avoid broad side effects on import.
- Use env-backed limits instead of hardcoded values.
- Add tests for new behavior when possible.

## Good issue ideas

- new plugin ideas
- demo improvements
- docs cleanup
- better defaults for first-run setup
- safer installer flows

## PR style

- One logical change per PR.
- Explain the user value first.
- Show how to test it.
