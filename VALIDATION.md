# Validation record

Validated locally on October 27, 2026 (America/Chicago), using Python 3.11.8 on Windows.

- `python -m unittest discover -s tests -v`: **10 tests passed**.
- Baseline suite: **3/8 scenarios**, **23/30 assertions** passed; five expected failing scenarios detected.
- Improved suite: **8/8 scenarios**, **30/30 assertions** passed.
- Tests verify repeated transcripts match, conversation state isolation, days 30/31, unknown orders, contradictory text detection, input bounds, JSON persistence, dashboard serving, invalid/cross-origin requests, and traversal rejection.
- Browser check: dashboard loaded, baseline evaluation completed via the button, new saved history appeared, and failure filter displayed exactly five failures. Inspected rendered layout and saved `dashboard.png`.
- GitHub connector identified the account as `MANIKANTA-G8`. Repository search found no matching `agent-testing-lab` repository. Connector has no repository creation operation; `gh auth status` reports no signed-in host; browser repository creation redirected to sign-in. **No upload has occurred.**

The included JSON files are actual outputs of the offline simulator. No model or external service was evaluated. JSON export UI and small-screen layout have not received separate browser interaction testing.
