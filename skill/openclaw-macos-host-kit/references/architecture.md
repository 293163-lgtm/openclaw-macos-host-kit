# Architecture

## 1. Why Terminal-hosted exists

On some macOS machines, LaunchAgent-based OpenClaw hosting is fragile in two ways:
- environment variables do not refresh reliably after config/secret changes
- TCC-sensitive capabilities (Accessibility / Screen Recording) are more stable when anchored to Terminal.app than to a background LaunchAgent or versioned Node path

Therefore this skill prefers a Terminal-hosted route when stability matters more than invisible background service purity.

## 2. Host modes

### LaunchAgent mode
Pros:
- background service style
- auto-start friendly

Risks:
- env refresh can be misleading
- TCC anchoring may be brittle depending on host process chain

### Terminal-hosted mode
Pros:
- more stable TCC anchor
- easy to inspect and recover

Tradeoff:
- visible host process model

## 3. Heartbeat mechanism boundary

There are two layers:
1. config cadence / delivery fields
2. runtime heartbeat enable switch

A valid “disable” must handle both layers.

## 4. Desktop packaging principle

Top-level desktop surface should stay small.
Recommended package:
- OpenClaw root
- workspace
- skills
- projects
- curated other shortcuts
- plain-language guide
- heartbeat toggles inside the package

## 5. Permissions boundary

TCC cannot be silently granted by script in a professional/reliable way.
The skill should:
- open the right settings panels
- explain what to enable
- validate behavior after the operator grants permissions
