---
name: frontend-ux
description: >
  Use when designing or building frontend user interfaces, review workstations,
  dashboards, loading states, error handling, accessibility, responsiveness,
  and state management for ComplianceOS.
---

# Frontend UX & UI Skill

## When to Use

- Building or modifying the 3-Pane Review Workstation (`index.html`).
- Adding new UI components, dashboards, or admin views.
- Designing responsive layouts, dark modes, or visual themes.
- Implementing loading skeletons, error states, and optimistic UI updates.
- Enhancing accessibility (WCAG AAA contrast, keyboard navigation, ARIA roles).

## 3-Pane Review Workstation Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Top Navigation Header                             │
│   Dashboard | Requests | Review Workstation | Snapshots & Diffs | Reports   │
└─────────────────────────────────────────────────────────────────────────────┘
┌─────────────────────┬───────────────────────────┬───────────────────────────┐
│     Pane 1 (Left)   │      Pane 2 (Center)      │      Pane 3 (Right)       │
│   Claim Directory   │   Inspector & Stepper     │   Evidence & Document     │
│                     │                           │                           │
│ • Claim List        │ • Selected Claim Details  │ • Original Document View  │
│ • Status Filters    │ • Decision Buttons        │ • PDF / Text Viewer       │
│ • Search / Filter   │ • Threaded Comments       │ • Pinned Evidence Chunks  │
│ • Verdict Badges    │ • Confidence Score Gauge  │ • Citation Highlights     │
└─────────────────────┴───────────────────────────┴───────────────────────────┘
```

## Key UX Principles

1. **Information Hierarchy**: Critical decision elements (verdict, confidence score, evidence context) must be visible without scrolling.
2. **Optimistic UI Updates**: Immediately render decision state changes (`Accept`, `Reject`, `Needs Revision`) before API response confirmation, rolling back gracefully on network errors.
3. **Loading & Skeleton States**: Display pulsing skeleton placeholders during async fetches (document loading, vector retrieval).
4. **Keyboard Accessibility**: Support full keyboard navigation (`j`/`k` to navigate claims, `a` to accept, `r` to reject, `c` to focus comment box).
5. **Dark Mode & Contrast**: High-contrast slate theme with curated status colors (Emerald for `SUPPORTED`, Amber for `PARTIAL`, Rose for `UNSUPPORTED`).

## Checklist

- [ ] Interactive elements have explicit IDs and ARIA labels.
- [ ] Responsive design functions cleanly across desktop and tablet viewports.
- [ ] Error boundaries display descriptive, actionable messages.
- [ ] Optimistic state updates roll back on failed network requests.
- [ ] Keyboard shortcuts are documented and non-conflicting.

## References

- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [CODING_STANDARD.md](../../CODING_STANDARD.md)
