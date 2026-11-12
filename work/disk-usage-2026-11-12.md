# Local disk inspection, 2026-11-12

User: «посмотри что на компе занимает много места».

Read-only inspection. No files deleted, applications stopped, Docker resources pruned,
paid calls, commits or pushes. Existing uncommitted product work preserved.
Branch `feat/transport-scenarios-update`, HEAD `986ae0f5ee754b9e98f25e2e608b5bc37cbad507`.

## Method and limits

Used `df -h`, `du -x -k -d 1`, `du -h` for Docker.raw, `ls -lh`,
`tmutil listlocalsnapshots /` and read-only `docker system df`.
Values below are GiB unless explicitly labeled decimal GB. Directory rows can overlap;
do not add parent and child sizes. Sizes changed slightly during the live scan.
macOS privacy restrictions denied some Library/system paths and Trash. This is a
partial inventory, not an exact reconciliation of the entire APFS container.
`diskutil apfs list` failed because the DiskManagement framework was unavailable.
`ps` was denied by the sandbox. Docker socket initially denied, then read access succeeded
with an approved escalation. No local Time Machine snapshots were listed.

Data volume: 460 GiB capacity, 426 GiB used, initially 5.9 GiB available,
6.7 GiB available at final check, 99% capacity reported.

## Largest categories

| Path relative to /Users/andreykuronskin unless absolute | GiB |
| --- | ---: |
| Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw, allocated | about 115 |
| PycharmProjects | 29.8 |
| .android/avd | 27.0 |
| mvideo | 23.4 |
| Applications, JetBrains apps | 21.7 |
| /Applications | 28.0 |
| vibecode | 11.7 |
| keys_champ | 11.2 |
| tander_hack | 10.2 |
| .cache | 8.1 |
| Library/Caches | 7.9 |
| /private/tmp | 8.3 |
| Downloads | 6.7 |
| .codex | 6.1 |

Docker.raw has a 460 GiB apparent maximum size; its allocated size is about 115 GiB.
Do not describe the apparent maximum as actual space consumed.

Docker reports decimal GB, with potentially shared image/cache accounting:

| Category | Total count | Active count | Size GB | Reclaimable GB |
| --- | ---: | ---: | ---: | ---: |
| Images | 161 | 82 | 68.82 | 48.08 |
| Containers | 196 | 47 | 2.899 | 1.364 |
| Local Volumes | 151 | 69 | 40.6 | 5.975 |
| Build Cache | 1168 | 0 | 26.33 | 12.26 |

These reclaimable amounts must not be added into a guaranteed host-space saving.
Volumes can contain important databases even when currently unattached.

## Useful detail

- mvideo/release: 12.7 GiB; mvideo/data: 8.3 GiB.
- PycharmProjects/alphavibe: 10.7 GiB; drone: 5.2 GiB; lct_hack: 5.0 GiB.
- tander_hack/.worktrees: 7.6 GiB; no worktree state inspected.
- Downloads/Telegram Desktop: 5.5 GiB.
- /private/tmp/keys-champ-merge-backup-20261109: 4.3 GiB.
- /private/tmp/plexus-traffic-db: 1.0 GiB.
- .cache/huggingface: 3.8 GiB; .cache/codex-runtimes: 2.0 GiB;
  .cache/receptron-laya: 1.6 GiB; .cache/opencode: 0.7 GiB.
- Library/Caches/com.openai.codex: 2.3 GiB; ms-playwright: 2.1 GiB;
  Google: 2.0 GiB.
- Library/Logs/JetBrains: 1.2 GiB.
- Library/Application Support/Google: 5.8 GiB; trueforge: 5.6 GiB;
  Cursor: 2.6 GiB; Telegram Desktop: 2.1 GiB. These are application data,
  not automatically disposable caches.

Potential next action, only if requested: inspect unused Docker images/build cache,
old Android emulators, temporary backup relevance and regenerable application caches.
No cleanup authorization inferred from this inspection request.

## Authorized cleanup, 2026-11-12

User: «удали тендер хак. ПОчисти докер. Удали андроид эмулятор».

- Stopped the tander_hack Uvicorn server, PID1129, with SIGTERM.
- Removed `/Users/andreykuronskin/tander_hack` including its nested worktrees,
  previously 10.2 GiB. Removed `/Users/andreykuronskin/.android/avd`, containing
  mlcap, wm, wmcap and wmtest emulator definitions, previously 27.0 GiB.
  Verified both paths no longer exist. No running Android emulator was found.
- Ran `docker builder prune --all --force`: reported 26.33 decimal GB reclaimed.
- Ran `docker system prune --all --force` without `--volumes`: reported
  6.766 decimal GB reclaimed. Images decreased from161to35, containers196to47,
  build cache1168to0. All151volumes retained, still40.6decimalGB.
- Final Docker.raw allocated size about70GiB, previously115GiB.
- Final data-volume check: 90,812,148 KiB available, about86.6GiB,
  versus about6.7GiB immediately before cleanup, about80GiB more available.
  Live filesystem activity and asynchronous Docker space reclamation affect deltas.
- Plexus ClickHouse remains healthy. Running container ID lists captured in
  `/tmp/disk-cleanup-running-before.txt` and `/tmp/disk-cleanup-running-after.txt`.
  Compared IDs:29running before,29after, no missing IDs.
  Full Docker cleanup outputs are `/tmp/disk-cleanup-builder.log` and
  `/tmp/disk-cleanup-system.log`.

No unrelated caches, SDK installations or applications deleted. No commit or push.
