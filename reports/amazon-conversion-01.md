# Amazon Tableau-to-Power-BI conversion test

- **Date:** October 22, 2026
- **Local test:** completed for the implemented scope
- **Result:** editable Power BI project with partial source fidelity
- **Full Tableau parity and business acceptance:** not certified

This is a shareable summary of an authorized local test. Source workbooks,
customer-level data, exported snapshots, generated projects, caches, private
configuration, screenshots, and detailed source-to-target evidence remain
outside source control. This report contains no source formulas or credentials.

## Interaction correction - October 29, 2026

The original generator explicitly disabled chart-to-chart interactions using
blanket `NoFilter` rules. This was an assistant implementation choice, not a
measure limitation or a user-approved requirement. Slicer tests at initial
delivery did not validate chart selections, and the original Markdown review
did not clearly disclose the restriction.

Those rules have now been removed from both pages and the generator corrected.
The main page explicitly cross-filters charts/cards from its analytical charts;
other interactions use normal Power BI defaults. Native testing in an isolated
copy verified that selecting Clothing changes all five country bars and the
monthly trend to independent CSV totals, combines with the Canada slicer, and
returns to baseline when cleared. No measures, visual definitions or model files
were changed.

The October 29 report-author check found zero errors and one warning: existing
Desktop-saved visualContainer 2.14 schemas were unavailable publicly. Those visual
files were preserved rather than silently downgraded; this follow-up is not a
new claim of complete exact-schema validation. The earlier schema results below
describe the original reviewed public-contract delivery.

The original open Desktop session was not reloaded over unsaved changes.
Reopen the updated local project without saving an older in-memory definition
over it. The original timing/token snapshot below is unchanged and excludes
this correction. Full Tableau parity and owner acceptance remain pending.

## Source and implementation

The user supplied the
[Amazon Sales Overview #VOTD Tableau Public sample](https://public.tableau.com/app/profile/mila.kholodii/viz/AmazonSalesOverview_17899965275850/AmaonSalesPerformance)
by Mila Kholodii, along with two other samples. Amazon was tested first.
Public availability is not permission to redistribute the workbook or artwork;
neither is included here.

The local result contains:

- An editable PBIP with TMDL semantic-model definitions, typed Power Query M
  Import partitions, and enhanced PBIR report definitions.
- Three tables, 34 explicit target measures, and one Date relationship.
- Two report pages with 19 native visuals: Amazon Sales Performance and
  Top 10 Products, retaining the worksheet absent from the source dashboard.
- A 100,000-row authorized local snapshot, preserving the source fact grain
  rather than introducing speculative Product/Customer joins.
- Working Year/Quarter/Month and Country controls, defaulting to Month and All.
- Dynamic trend grain, full-history trends, exact count/currency presentation,
  and cancellation changes explicitly displayed in percentage points.
- Source-derived dark/orange styling without copying original artwork.

This was agent-guided authoring using the available Tableau-to-Power-BI and
Microsoft Power BI authoring skills/tools, not an automatic conversion performed
by the repository's analyzer. No Fabric publication was performed.

## Approach rationale and scope

The test prioritized a **functional-first, editable project**:

1. Preserve the authorized source data and grain in a working semantic model.
2. Implement and independently test calculations and key controls.
3. Deliver editable, data-bound native Power BI visuals.
4. Verify schemas, rendering, refresh, and save/reopen persistence.

It did not pursue a pixel-for-pixel reconstruction. Native Power BI visuals and
source-derived styling were used, with remaining differences recorded explicitly.
Unresolved artwork rights justified not copying assets, but did not prevent closer
layout/styling work. Differences between Tableau and Power BI require individual
implementation and review; they do not establish that closer parity is impossible.

This was initially an assistant scoping decision rather than a previously agreed
visual acceptance criterion. The user subsequently confirmed that the approach
was acceptable and requested that the reasoning be documented. Acceptance of the
approach does not certify full parity, establish artwork rights, or approve
individual feature exclusions or semantic substitutions.

Numeric, schema, and lifecycle checks establish confidence in the implemented
scope, **not visual parity**.

## Validation results

| Check | Recorded result |
|---|---|
| Unfiltered period-KPI assertions | 45/45 passed |
| Country-by-period assertions, five countries | 225/225 passed |
| Total numeric KPI assertions | **270/270 passed** |
| Percentage-point presentation scaling | 3/3 passed |
| Exact official-schema validation | 29 project documents; zero failures |
| Report-author CLI validation | Zero errors; zero warnings |
| Date relationship integrity | Zero unmatched source date rows |
| Real Desktop controls | All three periods and Country filtering exercised; defaults restored |
| Persistence | Native Save, clean Close, and Reopen verified; all imported rows persisted |
| Rendering | Both pages reviewed; maximum Year sales value fits without clipping |

The numeric thresholds were engineering checks: exact counts, absolute tolerance
of `1e-6` for money/average-order values, and `1e-9` for ratios/changes. These were
not owner-approved Tableau parity tolerances.

### Validation gates

| Gate | Status | Boundary |
|---|---|---|
| G1: inventory coverage/privacy | Passed | Explicit decisions for 97 inventoried objects plus five discovered physical fields; all detected feature classes reviewed for this bounded revision |
| G2: TMDL/model | Passed | Implemented model and authorized snapshot validated |
| G3: schemas/references | Passed | Final authored public format validated against exact official schemas |
| G4: Desktop lifecycle | Passed | Open, refresh, save, close, and reopen verified |
| G5: Tableau parity/business acceptance | **Blocked, not waived** | Executed Tableau comparisons, agreed tolerances, and owner acceptance outstanding |

### Desktop serialization caveat

Power BI Desktop **2.159.883.0** can save visual files using `visualContainer`
**2.14.0**, whose public Microsoft schema returned HTTP 404 during the test.
Those transient files were not certified against a different schema.

Following native Save/Close, the deterministic report generator restored actual
reviewed **2.11.0** content. That same-path project was reopened, rendered, and
verified, and the final authored files passed exact-schema validation.
Native parameter/format resolution can mark the report dirty after opening;
future Desktop saves may again emit the newer format.

## Known limitations

- Original background/logo artwork was not copied; redistribution rights remain
  unresolved.
- The source canvas PDF-export button was not implemented. Its initial
  classification as a reset button was corrected after source inspection.
  Desktop's manual PDF export is an alternative, not an approved equivalent.
- Original conditional triangles and red/green indicators were not implemented.
- Exact typography, text, spacing, borders, geometry, and artwork were not
  pixel-matched; no complete side-by-side visual-parity pass was performed.
- Some row-level helpers have aggregate target counterparts rather than
  equivalent exposed columns; specific source helper decisions remain under review.
- Percent-of-total addressing/filter order, source-wide/cross-page Country scope,
  and exact ranking/tie behavior require executed Tableau reference tests.
- No security policy was inferred; future context filters/RLS need review.
- No live upstream connection or unattended refresh setup. The original delivery
  was local only. On October 29, the existing Amazon report in Tableau Migrations
  was updated in place; cloud PBIR readback confirmed two pages, zero disabled
  interaction overrides and 30 explicit filtering interactions. Its existing
  model was preserved, and a cloud query returned current sales of 1,451,073.77.
  Browser rendering was not verified because sign-in was required. Further
  automated publication was cancelled; the user will publish from Desktop.
  Reopen the corrected local PBIP before publishing; an older Desktop window
  can still hold the previous, disabled interaction settings.

## Inventory lessons

- The 134 reported calculation occurrences were duplicated heuristics, not
  unique formulas. There were 33 unique top-level definitions including the
  parameter; 34 target measures do not imply one-to-one formula conversion.
- Fourteen map metadata occurrences did not mean 14 map visuals; Country was
  a bar chart.
- Five physical fields missing from top-level inventory were retained.
- Eleven table-scoped global MAX-date LOD definitions were missed by the
  analyzer's FIXED/INCLUDE/EXCLUDE-only detection and explicitly reviewed.
- An 11-element shared-view section duplicated an existing period-filter field;
  it was classified rather than silently discarded.

These findings are observations about this test, not analyzer fixes. The
inventory remains heuristic and does not prove universal source completeness.

## Timing and AI token usage

Measurements come from the local session's recorded model-usage counters.
All timestamps are **October 22, 2026, EDT (UTC-04:00)**. Durations are rounded
to the nearest second.

| Scope | Start | End | Elapsed |
|---|---|---|---|
| Amazon test, including assessment/setup | 12:28:35.646 | 13:43:49.639 | **1 h 15 min 14 sec** |
| Conversion after "let's proceed" | 12:48:08.957 | 13:43:49.639 | **55 min 41 sec** |
| Entire conversation through delivery | 12:11:01.118 | 13:43:49.639 | **1 h 32 min 49 sec** |
| Entire conversation through usage question | 12:11:01.118 | 13:59:46.700 | **1 h 48 min 46 sec** |

Elapsed time includes tool execution, testing, troubleshooting, and waiting
between messages; it is not continuous model-compute time or human labor.

### Primary scope: Amazon test including assessment/setup

**193 recorded calls**, reported as **GPT-6.1 Sol** (`gpt-6.1-sol`).

| Category | Tokens |
|---|---:|
| Total input/context | 26,739,476 |
| Cache reads, included in input | 25,569,574 |
| Input excluding cache reads | 1,169,902 |
| Cache writes, included in input excluding cache reads | 1,156,932 |
| Output | 128,928 |
| **Total input + output** | **26,868,404** |

Approximately **95.6% of input tokens were cache reads**. Context is processed
repeatedly across calls; these are not 26 million tokens of newly written
material. Cache counts are input breakdowns, not additional tokens to add.

### Totals by scope

| Scope | Calls | Input | Output | Input + output |
|---|---:|---:|---:|---:|
| Amazon test including assessment/setup | 193 | 26,739,476 | 128,928 | **26,868,404** |
| Conversion after "let's proceed" | 162 | 24,495,427 | 116,410 | **24,611,837** |
| Entire conversation through delivery | 197 | 26,831,450 | 129,456 | **26,960,906** |
| Entire conversation through usage question | 199 | 26,940,824 | 129,779 | **27,070,603** |

Scopes overlap and must not be added together. Totals exclude later documentation
and Git work. They are token measurements, **not a dollar-cost estimate**;
provider/subscription and cache billing rules must be considered separately.

## Local deliverable and evidence

On the originating machine, the final project is under
`migrations\amazon-conversion-01\Amazon`, opened through its `Amazon.pbip`.
Keep the report/model folders together. Refresh uses the authorized local CSV
through a non-secret Data File parameter; moving it requires updating that path.
The calendar currently spans 2020-2024. Credentials belong in Desktop's credential
store, not in project files.

The ignored local run contains the full Markdown review, 102-object ledger,
independent/live numeric results, DAX assertions, schema registry, report manifest,
Desktop status, provenance, and screenshot evidence. These are not bundled with
this shareable report, so this repository alone cannot reproduce or independently
verify the private local run.

## Conclusion

The implemented-scope test produced a working editable project with documented
partial fidelity. Full accepted migration remains a separate gate requiring
executed Tableau comparisons, feature/substitution decisions, licensing review,
and business acceptance.
