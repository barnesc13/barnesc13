# RuneScape contribution quest log

The profile image is generated from this account's public GitHub contribution calendar, including private contribution aggregates only when GitHub already exposes them publicly. The updater never reads private repository details, requests a PAT, or requires a custom secret.

## Automatic refresh

The `Update RuneScape quest log` GitHub Actions workflow runs daily at **07:17 UTC** and whenever the generator, tests, or workflow change on `main`. GitHub schedules are best-effort and can be delayed. Run it on demand from **Actions → Update RuneScape quest log → Run workflow**, with branch `main`.

GitHub-hosted Ubuntu runners and Python's standard library are sufficient. The built-in, short-lived `GITHUB_TOKEN` commits only `assets/questlog.svg` and `assets/questlog-data.json`. No self-hosted runner, external action service, paid API, or dependency installation is needed. Private-repository jobs use the account's normal GitHub Actions allowance.

## What the numbers mean

- **Contributions**: the sum of GitHub's exact daily contribution counts, not a commit-only count.
- **Active days**: dates with at least one contribution.
- **Best streak**: the longest sequence of active dates within the displayed window.
- **Current streak**: consecutive active dates ending today, or yesterday if the partial current day still has zero contributions. A second zero ends the streak.
- **Window**: 182 consecutive GitHub calendar dates (26 weeks), ending on the UTC run date. The current day is partial. Each column contains seven consecutive days; it is not a Sunday-aligned GitHub calendar.

GitHub assigns each underlying contribution to a calendar date using its own contribution-date rules; the updater does not reinterpret commit timestamps.

All four statistics, dates, tile heights, colors, and accessible descriptions are generated together. The world art and quest-log styling stay deterministic. Each day tile includes its exact ISO date and contribution count in its SVG title.

## Local checks and replay

```sh
python3 -m unittest discover -s tests -v
python3 scripts/generate_questlog.py --username barnesc13
```

To reproduce the existing real-data snapshot without network access:

```sh
python3 scripts/generate_questlog.py --input assets/questlog-data.json
```

The daily workflow never uses offline replay or fallback data. If GitHub blocks a request, changes its HTML, omits a date, or stops providing exact counts, the run fails and preserves the last valid image. The public calendar is an HTML interface rather than a versioned API; its parser may need maintenance if GitHub changes it.

## Profile visibility

The image displays in this repository's README for people with access. A GitHub profile README appears to public visitors only when GitHub's profile repository requirements are met, including a public repository matching the username. This workflow does not change repository visibility or access settings.
