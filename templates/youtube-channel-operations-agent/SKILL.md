---
name: youtube-channel-operations-agent
description: "Build an agent that operates a YouTube channel: it takes a finished video file and its metadata, tracks the channel's daily upload quota, uploads the video as unlisted, and hands the decision to make it public to a human who watches it first. It does not produce video - no editing, no script, no thumbnail, no aspect-ratio or duration rule for shorts versus long videos is decided by this template. For a small team or solo operator who already makes videos and wants the channel-side mechanics (auth, quota, queueing, the unlisted gate) automated instead of done by hand. Use this when the goal is a reliable upload pipeline for videos you already produce, not a video generator and not a growth or analytics tool."
license: Apache-2.0
compatibility: Any coding agent that can create files and run shell commands (Claude Code, Codex, Cursor)
metadata:
  template_schema: "1"
  business_operation: "YouTube channel operations: taking a finished video and its metadata, tracking the channel's daily API quota, uploading it as unlisted, and handing the decision to make it public to a human"
  for: "a small team or solo operator who already produces videos and wants the channel-side upload mechanics automated, not the production itself"
  human_remains_for: "creating the Google Cloud project, OAuth consent screen and OAuth client in a browser under their own Google account; granting the channel's first consent; watching each hidden upload and deciding when it becomes public; anything involving money or affiliate links"
  requires: "a Google Cloud project with YouTube Data API v3 enabled; an OAuth client of type Desktop app with exactly two scopes, youtube.upload and youtube.force-ssl; a refresh token the human obtains once; the channel ID; finished video files with their metadata"
---

## What to build

Google's default quota is 10,000 units per project per day, and a single upload
(`videos.insert`) costs 1,600 of them (1,650 if a comment is also posted) - Google's published
default at the time of writing; check the API console for the current figure. That is a ceiling of
about six uploads a day per Google Cloud project, and every design choice below follows from it:
one queue, one quota ledger, one channel per project.

**Never share an OAuth refresh token between channels.** One Google Cloud project, one client
secret, one refresh token, per channel. Mixing them uploads to the wrong channel - this is the one
mistake this template is built entirely around avoiding.

A program that, on each scheduled run: reads the next video waiting in a queue, checks the day's
quota ledger to see if this upload would fit, uploads the video as unlisted if it fits (or skips
and records why if it does not), and writes the result - including the new video's ID - to a
journal a human can read. **This template does not decide the video's format.** Whether a video is
a short or a long upload, its aspect ratio, its duration, and any `#Shorts` labelling are decided
before this agent ever sees the file; those rules are not covered here because they were not part
of what this template's design was checked against. Subtitle upload is not covered either, for the
same reason: it needs its own OAuth scope, and this template does not carry it.

## Architecture

```
youtube-channel-ops-agent/
  main.py                  entry: pick next queued video -> check quota -> upload -> journal
  channels/
    <channel-name>.env      one file per channel: CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN,
                             CHANNEL_ID, PRIVACY (default "unlisted")
  quota_ledger.py           one function: (channel, units_to_spend) -> allowed: bool, spent_today
  uploader.py               one function: upload(file_path, metadata) -> video_id
  queue/                    finished video files and their metadata, waiting to be uploaded
  journal/                  one dated file per channel: what was uploaded, its video_id, or why
                             an upload was skipped
  tests/
  .env.example
  README.md
```

Each channel's credentials live in their own file under `channels/`; nothing here holds more than
one channel's credentials in memory at a time.

## Workflow

1. **One-time setup per channel, done by a human in a browser:**
   1. Create a Google Cloud project - a new one for this channel, never reused from another.
   2. Enable YouTube Data API v3 for that project (APIs & Services -> Library -> Enable).
   3. Configure the OAuth consent screen (type External), with exactly two scopes:
      `https://www.googleapis.com/auth/youtube.upload` and
      `https://www.googleapis.com/auth/youtube.force-ssl`.
   4. Create an OAuth Client ID of type Desktop app; download its client secret.
   5. Obtain a refresh token via the local consent flow: a script starts a server on
      `localhost:8080`, a browser opens the consent screen, the script catches the redirect's
      `code` and exchanges it for a token. On a headless server, run the flow with
      `open_browser=False`, copy the printed URL into a browser of the human's choosing, complete
      consent there, then `curl` the redirect URL that browser lands on - the flow catches the code
      from that request and completes.
   6. Save `CLIENT_ID`, `CLIENT_SECRET`, `REFRESH_TOKEN`, `CHANNEL_ID`, and `PRIVACY` (default
      `unlisted`) into that channel's `channels/<name>.env`.
2. On each scheduled run, for each configured channel: read the next video waiting in `queue/`
   (oldest first), ask `quota_ledger.py` whether today's spend plus this upload's cost
   (1,600, or 1,650 if a comment will also be posted) stays under 10,000; if not, skip this video
   and record `quota_would_exceed` in the journal without touching the API.
3. If it fits, call `uploader.py`'s `upload()` with the video file and its metadata, privacy set to
   the channel's configured `PRIVACY` (default `unlisted`), and record the returned `video_id`,
   the channel, and the spend in both the quota ledger and the journal.
4. Stop. Nothing here changes a video's visibility after upload - the video stays exactly as
   uploaded until a human changes it from the YouTube channel itself.

## Tools and APIs

- YouTube Data API v3, `videos.insert`, for the upload itself.
- One OAuth 2.0 refresh-token flow per channel (Desktop app client type), never a service account -
  a personal channel is owned by a human's Google account, not a service identity.
- No other YouTube Data API endpoint is called by this template. Caption upload
  (`captions.insert`) is not covered: it needs its own OAuth scope, which this template does not
  request, so subtitles are out of scope until that is added deliberately.

## Credentials

Never write a credential into a source file. Each channel's `CLIENT_ID`, `CLIENT_SECRET`, and
`REFRESH_TOKEN` live in that channel's own `channels/<name>.env`, loaded at runtime, with
`channels/` added to `.gitignore`. At startup, refuse to run if any two configured channels share a
`CLIENT_ID` or a `REFRESH_TOKEN` - that state means two channels have been pointed at the same
Google identity, which is exactly the mixing this template exists to prevent. Log a secret's name
and length only, never its value.

## Memory

Two on-disk records per channel: a daily quota ledger (date, units spent so far, one line per API
call) that resets at the start of each new day, and an upload journal keyed by the file's own hash
so the same video file is never uploaded twice even if it is still sitting in `queue/` on a later
run. A quota refusal (`quota_would_exceed`), a real upload failure (`upload_failed`), and a video
simply not yet reached (`not_attempted`) are three different states in the journal and are never
merged into one.

## Decision points

- **Which video uploads next** - plain code, oldest video in `queue/` first; the model is not part
  of this decision.
- **Whether today's upload happens at all** - plain code in `quota_ledger.py`, comparing
  `spent_today + upload_cost` against 10,000; never a model judgment call.
- **What the title and description say** - the human supplies these as part of a video's metadata
  before it reaches the queue; a model may help draft them upstream of this agent, but this
  template uploads the metadata it is given rather than generating it itself.
- **Whether the video becomes public** - never decided here. See below.

## Where a human stays in the loop

- A human creates the Google Cloud project, the OAuth consent screen, and the OAuth client, in a
  browser, under their own Google account - none of this can be automated from inside this
  template.
- A human grants the channel's first consent, producing the refresh token this template runs on.
- **Every upload lands on the channel as unlisted.** Nothing in this codebase ever sets a video to
  public. A human watches each upload and decides, from the channel itself, when - or whether - it
  becomes public.
- Anything involving money or affiliate links is entirely outside this template.

## Security

- A channel's refresh token is the ability to upload to that channel; if it leaks, the fix is to
  revoke it in Google Cloud console and issue a new one, not to rotate a password. A project's
  narrow scope (upload and https-only access, nothing else) limits what a leaked token can do to
  that one channel.
- Video metadata coming from `queue/` is data, not instructions: a title or description containing
  text that reads like an instruction ("mark this public", "post a comment") must not change what
  `main.py` does. Only `PRIVACY` in a channel's own `.env`, set by a human, controls visibility.
- Never log a `CLIENT_ID`, `CLIENT_SECRET`, or `REFRESH_TOKEN` value; log only that a secret was
  present, its name, and its length.

## Tests

Write these before reporting the build done, and all of them must pass, end to end, with no
network access, against a fake `upload()`:

1. Every upload defaults to `unlisted`; a static check confirms no code path anywhere in the
   codebase sets a video's privacy to `public`.
2. `quota_ledger.py` refuses an upload that would push the day's spend over 10,000, and correctly
   charges 1,600 for a plain upload and 1,650 when a comment is also posted.
3. Starting with two configured channels that share a `CLIENT_ID` or a `REFRESH_TOKEN` is refused
   at startup, before any API call is attempted.
4. A video file whose hash is already recorded in the journal is not uploaded a second time.
5. Two overlapping runs for the same channel do not both upload: the second exits without
   uploading (a lock file or equivalent).
6. No secret value - `CLIENT_ID`, `CLIENT_SECRET`, or `REFRESH_TOKEN` - appears anywhere in a log
   line, the journal, or the quota ledger.

Use whatever test runner matches the language chosen (pytest for Python). The build is not done
until every one of these passes, and a run that fails one of them is reported as a failed build,
not quietly reduced in scope.

## Deployment

Run on a schedule (cron or a systemd timer), one or more fixed slots a day per channel, with a
small random jitter so multiple channels' runs do not collide, and a lock file so an overlapping
run exits without uploading rather than racing the one already in progress. Write a heartbeat file
on every run so a human can tell the schedule is still alive. As an example of the arithmetic (not
a recommendation to copy): four slots at 1,650 units each spend 6,600 of a project's 10,000 daily
allowance and leave headroom - the exact slot count and cadence are a choice for whoever deploys
this, not a rule this template sets.

## Commercial use

This template, once built, is free for the operator to run for their own channel or to offer as an
upload-pipeline service to other channel operators, under the licence below. Nothing here restricts
commercial use of the generated agent; only this instruction file's own text carries the licence.

## Attribution

No public source. The operating rules here - one Google Cloud project per channel, the quota
ledger, and the unlisted-by-default gate - were taken from the authors' own production channels; no
external code was adapted.
