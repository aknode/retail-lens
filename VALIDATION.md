# Release validation

Validated on Python 3.12 in a Linux authoring environment. Windows instructions are provided but were not executed on Windows.

- Loaded all 541,909 source rows; retained 534,129 after documented cleaning.
- Verified foreign keys, source-row reconciliation and gross minus returns equals net.
- Browser: all report tabs, SQL inspection, export and country-filter revenue update.

Automated tests pass; see `validation/unit-test-results.txt`. Browser workflows passed in headless Chromium at 1440px desktop and 390px mobile, with no uncaught JavaScript errors or page-level horizontal overflow. Internal screenshots were visually inspected and are not part of the release.

Static Python undefined/unused-name checks passed. JavaScript syntax checks and formatting completed. Each repository includes a CI workflow, but GitHub-hosted CI was not executed here. Docker files are provided but Docker images were not built. No public deployment was performed.

