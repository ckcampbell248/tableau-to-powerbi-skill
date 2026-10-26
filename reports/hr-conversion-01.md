# HR Analytics Tableau-to-Power-BI conversion test

- **Test date:** October 23, 2026
- **Local test:** completed for the implemented scope
- **Result:** editable Power BI project with partial source fidelity
- **Full Tableau parity and business acceptance:** blocked, not certified

This is a shareable summary of an authorized local test, following the
[Amazon test](amazon-conversion-01.md). Source workbooks, employee-level data,
exported snapshots, generated projects, caches, private configuration, screenshots
and detailed evidence remain outside source control. No source formulas,
individual employee/manager identities or credentials are included here.

## Source and implementation

The user supplied the
[HR Analytics Dashboard Tableau Public sample](https://public.tableau.com/app/profile/oyedele.samuel/viz/HRAnalytics_17575255034700/Dashboard1)
by Oyedele Samuel. Public availability does not establish permission to
redistribute its workbook, data or artwork; none is included here.

The local result contains:

- An editable PBIP, TMDL semantic model, typed Power Query M Import partitions
  and data-bound enhanced PBIR report definitions.
- Three 1560 x 960 pages: Overview, Performance and Business Sales.
- **55 distinct visuals, 15 tables, 49 measures and nine active single-direction
  relationships.**
- Five approved source tables totaling **497,032 physical rows**: 7,500 employee
  rows, 150 store rows, two 236,591-row employee-month facts and a 16,200-row
  store-department-month fact. Separate grains avoid employee-to-sales fanout.
- Native category/metric field parameters; workforce, department, store-type,
  year and ranking controls; hire-date and observation-date ranges.
- Workforce and compensation summaries, performance comparisons, monthly
  observations, sales/target trends and proposed native ranking/location views.

Authoring was agent-guided using the available migration and Power BI skills
and tools, not automatic conversion by the analyzer. No Fabric publication,
external geocoding, inferred RLS policy or arbitrary source SQL execution occurred.
The model uses authorized local snapshots, not a live Tableau/upstream connection.
Source Tableau build was **2025.2.0 (20252.25.0903.1422)**, workbook format **18.1**.

## Functional-first rationale

The user accepted the general functional-first approach after Amazon: prioritize
editable native visuals, correct model grain/calculations, working controls and
tested persistence rather than pixel-identical reproduction. HR retains the
source aspect ratio but uses a new native layout and does not copy bitmap artwork.

That acceptance is not approval of HR-specific semantic substitutions, artwork
rights or full parity. Proposed city-summary and ranking replacements, missing
controls and source action differences remain explicit blockers.

Employee headcount and compensation retain employee grain. Monthly averages
retain observation grain, while sales retain business grain. Observation dates
do not redefine historical headcount or hire-date cohorts. The exit-rate measure
is a former/all-employee ratio, not historical monthly turnover. Source three-year
age bins and raw delivery/waste scales were retained.

## Validation results

| Check | Recorded result |
|---|---|
| Independent aggregate/metric assertions | 883 passed |
| Store-ranking checks | 96 passed across 32 contexts |
| Total regression assertions | **979 passed**, including 108 expected BLANKs |
| Numeric threshold | Absolute tolerance `1e-6`; maximum aggregate error approximately `1.23e-11` |
| Measure coverage | All 49 measures exercised |
| Additional date/integrity checks | 11 passed |
| Native hire-date cards | Four independently calculated rendered values matched |
| Observation-date interaction | Changed to 2024, rendering reviewed and reference totals checked |
| Exact official-schema validation | 66 documents, 16 trusted schemas, zero failures |
| Report-author validation | Zero errors and warnings |
| Native controls | Field parameters, metric/ranking controls and filters exercised |
| Persistence | Full refresh, native Save, graceful close and cached-data reopen verified |
| Rendering | All three final pages reviewed; defaults and date ranges restored |

The source-to-target ledger records **220 decisions**: 216 inventory objects,
two physical Department fields and two worksheet-local constant helpers missed
by structural inventory. No exclusions or semantic replacements have invented
owner approval. Source and exported-data hashes were verified unchanged.

### Validation gates

| Gate | Status | Boundary |
|---|---|---|
| G1: coverage/privacy | Passed | Reviewed source objects and detected features have explicit decisions |
| G2: model | Passed | Native parse, refresh and implemented model references verified |
| G3: schemas/bindings | Passed | Exact public schemas and 55 unique visual files checked |
| G4: Desktop lifecycle | Passed | Open, refresh, controls, Save, close and cached reopen tested |
| G5: Tableau parity/acceptance | **Blocked** | Executed Tableau outputs and HR-specific owner approvals absent |

Tests used Power BI Desktop **2.159.883.0**. Native Save can emit an unpublished
visualContainer 2.14 contract. After Save/Close, the deterministic generator
restored reviewed public 2.11 content; that project was validated, reopened and
rendered. The saved model cache was 6,280,374 bytes, and reopened counts/KPIs were
checked without refresh. Field-parameter resolution can mark Desktop dirty;
no extra Save was performed merely to clear that indicator.

Testing corrected conflicting format strings, column/measure name collisions,
ranking context and blank-candidate defects, age-bin ordering and a duplicated
visual generator key. Final source-control reconciliation added both date ranges.

## Limitations and pending acceptance

- Exact typography, colors, geometry, artwork and device-layout parity remain
  unverified; the native layout is not a pixel copy.
- The geographic map is replaced by a proposed offline city summary. This is not
  an approved equivalent; no external geocoding was used.
- The source top-11 employee filter and named exclusion are not reproduced.
  Native top-ten competition ranking retains ties (11 members in this snapshot).
- Source rank/index addressing, filter order, partitioning and tie behavior still
  require executed Tableau comparisons. Matching membership is not row-order parity.
- Three source brush/highlight actions are not recreated. Native chart-to-chart
  filtering is disabled.
- The source Manager_Name filter and hard-coded null-name replacement are not
  implemented. No substitute person was invented.
- Native page tabs/manual export are not approved equivalents for source canvas
  buttons. Some source authoring/system/constant-axis helpers remain blocked.
- Additional native filters and date controls do not establish identical
  source per-worksheet filter scope.

Independent CSV comparisons validate the implemented arithmetic, not executed
Tableau semantics. An acceptance owner must review the gaps, provide authorized
Tableau outputs and agree semantic/visual tolerances before full migration acceptance.

## Timing and AI token usage

Scope is the HR request only, excluding Amazon and later Git/documentation work.
The recorded interval is **2026-10-23T19:22:07.330Z** through
**2026-10-23T20:25:37.767609+00:00**.

| Measurement | Recorded value |
|---|---:|
| Elapsed wall-clock time | **1h 3m 30s** |
| Recorded model-usage calls | 186 |
| Input tokens | 27,994,621 |
| Output tokens | 133,597 |
| **Input + output** | **28,128,218** |
| Cache reads, included in input | 27,114,187 |
| Cache writes, included in input | 851,015 |
| Input excluding cache reads | 880,434 |

Recorded model: `gpt-6.1-sol`. Repeated cached context counts on each request;
cache reads/writes are breakdowns, not additional tokens to add. Elapsed time
includes source review, authoring, debugging, validation, waiting and review
writing, not just file generation. This is a cutoff snapshot, excluding subsequent
work and final-response tokens, not a dollar-cost estimate.

## Local deliverable and evidence

On the originating machine, the ignored project is under
`migrations\hr-conversion-01\HRAnalytics`, opened through `HRAnalytics.pbip`.
Keep its report/model folders together. Refresh reads the five approved CSV
snapshots through the **Data Folder** M parameter; relocation requires updating
that local path.

The ignored run contains its full review, 220-object ledger, source inventory,
independent references, executed DAX/results, schema checks, provenance, UI
interaction evidence and redacted previews. These are not bundled here, so the
repository alone cannot reproduce or independently verify the private local run.
Unredacted previews and employee-level data must not be redistributed without
confirming rights and privacy requirements.
