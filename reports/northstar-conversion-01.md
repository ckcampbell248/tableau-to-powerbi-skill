# Northstar Logistics Tableau-to-Power-BI conversion test

- **Test date:** October 23, 2026
- **Local test:** completed for the implemented scope
- **Result:** editable Power BI project with partial source fidelity
- **Full Tableau parity and business acceptance:** blocked, not certified

This is a shareable summary of an authorized local test, following
[Amazon](amazon-conversion-01.md) and [HR Analytics](hr-conversion-01.md).
Source workbooks, exported data, generated projects, caches, private configuration,
screenshots and detailed evidence remain outside source control. No source
formulas or credentials are included here.

## Interaction correction - October 29, 2026

Blanket `NoFilter` rules have been removed from the page, and the generator now
preserves normal Power BI interactions. Native testing in an isolated Desktop
copy selected Birmingham's current-week on-time bar: four cards matched
independent warehouse totals (435 completed orders, 93.10% on time, 3.56 days
weighted lead time and 18 SLA breaches). The warehouse matrix and time-series
also responded; clearing restored the all-warehouse headline values.

Only page interaction rules changed in the generated project. Visual definitions,
measures, models and cached data were preserved. The report-author follow-up
returned zero errors and one existing unavailable-schema warning for
Desktop-saved visualContainer 2.14 content; it is not a new complete exact-schema
pass. The original validation and timing/token snapshots below exclude this
correction, and G5 acceptance remains pending.

## Source and implementation

The user supplied the
[Northstar Logistics Operations Control Tower Tableau Public sample](https://public.tableau.com/app/profile/karen.biltcliffe/viz/NorthstarLogisticsOperationsControlTowerBusinessDashboard/OperationsControlTower)
by Karen Biltcliffe. Public availability is not permission to redistribute its
workbook, data or artwork; none is included here.

The local result contains:

- An editable PBIP, TMDL semantic model, six typed Power Query M Import
  partitions and data-bound enhanced PBIR report definitions.
- One **1800 x 1000 page with 25 distinct native visuals**.
- **Six tables, 31 declared business columns, 63 measures and four active
  single-direction warehouse/date relationships.** Six additional internal
  engine RowNumber columns are not counted as business fields.
- An approved **450-row, 18-column** physical snapshot: five warehouses across
  90 dates, 1 January-31 March 2026.
- A derived 2,700-row delay-reason fact, produced by unpivoting six reason counts,
  not additional physical source records.
- Native Reporting date, Region and Warehouse slicers; daily KPIs and changes;
  daily 30-day trends; warehouse/period comparisons; two-period reason
  composition; weekly impacts; a proposed warehouse performance-watch matrix.

This was agent-guided authoring using the migration and Power BI skills/tools,
not automatic conversion by the analyzer. No Fabric publication, remote Tableau
source execution, external geocoding or arbitrary source SQL execution occurred.
The model uses an authorized local snapshot, not a live upstream connection.
Source Tableau build was **2026.2.1 (20262.26.0708.1337)**, workbook format **18.1**.

## Functional-first rationale and source semantics

The general functional-first approach accepted after Amazon prioritizes editable
native visuals, correct grain/window arithmetic, working controls and tested
persistence over pixel copying. It does not imply acceptance of Northstar-specific
substitutions or full parity. In particular, the clearly labeled all-warehouse
comparison matrix is a proposed replacement for ranked narrative/driver prose,
not an approved equivalent.

Important reviewed semantics:

- Reporting date defaults to **19 February 2026**, not the extract maximum.
- On-time rates use completed-order denominators. Lead time is weighted by
  completed orders rather than averaging warehouse/day averages.
- Last/prior seven-day windows are inclusive, adjacent and non-overlapping.
  The default 30-day window is 21 January-19 February.
- Headline and weekly warehouse backlog use averages. The upper backlog
  sparkline uses a sum; the lower 30-day panel uses an average.
- Lead-time changes use hours and rate changes use percentage points.
  Relative daily changes use the prior-day denominator.
- The source delay chart actually retains **both last and prior seven-day
  periods**, despite its last-seven-days title. The native chart labels both.
- Window filtering intersects daily chart context rather than repeating
  a full-window total at every date.
- Missing observations and zero denominators retain the required BLANK behavior.
- Source map flags are formatting metadata, not geographic visuals.
- The unused source start-date parameter is retained as named M metadata.

## Validation results

| Check | Recorded result |
|---|---|
| Independent numeric regression | **4,095 assertions across 65 contexts passed** |
| Expected BLANK assertions | 1,081 matched |
| Numeric threshold | Absolute tolerance `1e-8`; maximum error approximately `3.419486915845482e-14` |
| Independent reason-category checks | All 12 period/reason counts matched |
| Source integrity | 450 unique warehouse-day keys; completed and reason counts reconcile |
| Daily grain | 30 nonblank points, correct endpoints, zero daily-total discrepancy |
| Native card checks | 20 passed, including repeated reopened baseline |
| Native controls | Reporting date, Region and Warehouse exercised |
| Exact official-schema validation | 34 documents, 16 trusted schemas, zero failures |
| Report-author validation | Zero errors and warnings |
| Persistence | Full refresh, confirmed native Save, graceful close and cached-data reopen |
| Rendering | Final page and default reporting date reviewed |

The 65 regression contexts combine five anchor dates with 13 scopes: all
warehouses, each warehouse, each region, an empty scope and a mismatched
region/warehouse intersection. Independent CSV/Decimal arithmetic checks the
numeric measures and both reason periods.

The raw regression failure count was JSON null because DAX COUNTROWS returns
BLANK for an empty failure table. That specific result means **zero failures**;
the raw evidence was retained rather than silently rewritten.

The source-to-target ledger contains **302 decisions**: 293 inventoried objects
plus nine physical fields missed by top-level inventory. Reconciliation identified
94 top-level calculations and 169 exact worksheet-local repeats, totaling
263 occurrences rather than 263 unique definitions. All detected feature classes
and seven top-level sections were reviewed. Source/export hashes were unchanged.

### Validation gates

| Gate | Status | Boundary |
|---|---|---|
| G1: coverage/privacy | Passed | All inventoried/discovered objects and detected features have decisions |
| G2: model | Passed | Native parse, refresh, references and cached-data reopen verified |
| G3: schemas/bindings | Passed | Exact public schemas and 25 unique visual files checked |
| G4: Desktop lifecycle | Passed | Native controls, rendering, Save, close and reopen tested |
| G5: Tableau parity/acceptance | **Blocked** | Executed Tableau references and owner acceptance absent |

Tests used Power BI Desktop **2.159.883.0**. Native Save can upgrade PBIR
contracts; after Save/Close, the deterministic generator restored reviewed public
visualContainer 2.11 content. The final project was schema-validated, reopened
without refresh and its cached data/rendering checked. The model cache was
77,585 bytes. The temporary regression table was removed before Save.

### Automation caveats

The reporting-date dropdown virtualizes off-screen options. An attempted
20 February selection was unavailable, and an attempted value setter did not
change data; **that case was not counted as passed**. The visible 7 January
selection changed four independently calculated cards correctly. Final PBIR
generation restored 19 February and reopened cards confirmed that default.
Region and Warehouse were restored to All.

A stale duplicate Save accessibility element initially did not persist changes.
The current toolbar Save succeeded; bridge saved-state evidence, files and
cached-data reopen independently confirmed persistence. These limitations are
recorded rather than concealed as successful checks.

## Limitations and pending acceptance

- Exact layout, device variants, typography, colors and artwork are not
  pixel-matched or owner-accepted.
- Source ranked Performance Watch and Primary Driver narratives are not
  recreated. The proposed all-warehouse matrix is not certified equivalent.
- Arrow glyphs, conditional performance colors and three reference lines
  (two 95% on-time lines and one zero SLA line) are not recreated.
- Eight bitmap resources and 16 bitmap zone occurrences are not copied;
  redistribution/styling approval is absent.
- Exact per-worksheet filter order/scope and quantitative rank filtering
  require executed Tableau comparisons.
- Reporting-date selection is restricted to the 90 snapshot dates rather
  than the broader source parameter domain.
- Some system, date-flag, constant-axis and authoring helpers are not exposed
  as standalone target fields; their blocked decisions remain in the ledger.

Normal Power BI chart interactions are enabled. No source actions were present,
so a missing Tableau highlight action is not invented. Independent extract
arithmetic is not proof of executed Tableau, visual or filter-order parity.
An acceptance owner must provide authorized reference outputs and accept or
reject the documented substitutions before full migration acceptance.

## Timing and AI token usage

Scope is the Northstar request only. The recorded interval is
**2026-10-23T20:37:49.318Z** through
**2026-10-23T21:06:46.353409+00:00**.

| Measurement | Recorded value |
|---|---:|
| Elapsed wall-clock time | **28m 57s (1,737 seconds)** |
| Available usage records | 75 |
| Input tokens | 10,445,637 |
| Output tokens | 75,645 |
| **Input + output** | **10,521,282** |
| Cache reads, included in input | 10,119,195 |
| Cache writes, included in input | 294,435 |
| Input excluding cache reads | 326,442 |

These are session usage counters, including repeated cached context. Cache
reads/writes must not be added again. Wall-clock time includes waits, source
review, debugging, validation and review writing, not just active computation.
This explicit cutoff excludes later verification, final-response tokens and
the subsequent Git/documentation work; it is not a dollar-cost estimate.

## Local deliverable and evidence

On the originating machine, the ignored project is under
`migrations\northstar-conversion-01\Northstar`, opened through `Northstar.pbip`.
Keep its report/model folders together. Refresh reads the approved local CSV
through the **Data Folder** M parameter; relocation requires updating that path.
There is no live upstream or incremental refresh configuration.

The ignored run contains its full review, 302-object ledger, coverage analysis,
independent references, executed DAX/results, schema checks, provenance, native
interaction/save/reopen evidence and final preview. These are not bundled here,
so the repository alone cannot reproduce or independently verify the private run.
