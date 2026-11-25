# PMO Project Hub — Power Apps build guide

**What it is:** One place for every improvement project at the facility. Project managers post a 2-minute weekly status update. Leaders see portfolio health, schedule slips, risk exposure and progress toward each project's target metric, without asking anyone for a slide deck.

**Stack (standard connectors only):** Canvas app · 6 SharePoint Online lists · 2 Power Automate flows (one scheduled, one called from the app) · Teams · OneDrive · Office 365 Users. Everything lives in **one Solution** with environment variables.

**Data skills this shows (use these in captions):**
| Skill | Where it shows up |
|---|---|
| **Relational data model** | 6 lists joined on `ProjectID`; latest values copied onto the project for fast reads (denormalized) |
| **Data quality at capture** | Validation, required blockers when not Green, one update per project per week (no duplicates), last week's update copied forward |
| **Analysis** | Schedule variance (days), % milestones on time, progress to target (works whether lower or higher is better), risk score = likelihood × impact |
| **Visualization** | Metric trend line vs. target, 8-week portfolio health trend (stacked bars), 5×5 risk heat map, portfolio Gantt with a "today" line |
| **Reporting** | One-click PDF status report built by a flow from 5 lists |
| **Data monitoring** | "Missing update" flags and a Friday reminder flow with a deep link straight to the right form |

**Time:** ~7–9 h with this guide. Core = Sections 1–5 + Flow A. Flow B (PDF), the Analytics screen extras and Section 8 are worth it if time allows.

---

## 1. SharePoint lists + seed data (≈1 h)

Seed files are in `seed-data/`. **First**, open each CSV in Excel and Find & Replace: `YOUR_EMAIL` → your sign-in email (**lowercase**), `YOUR_NAME` → your display name. You're the PM on 3 projects (PRJ-101, 105, 108) and own several action items, so "My work" has content.

On your **Systems Redesign (Demo)** SharePoint site: **+ New → List → Blank list**. Add columns **in this exact order** (the paste depends on it).

- **Date columns:** *Date and time* → turn **off** "Include time". These are date-only, which avoids time-zone shifts.
- **Multi-line columns:** **Plain text**.
- **Number columns:** decimals as noted.

> **Why `ProjectID` numbers instead of SharePoint Lookup columns?** Number filters are fully **delegable** (they run on the server, so they scale past 2,000 rows), and `Patch` stays simple. The relationships are enforced in the app. Mention this in a caption; it shows you understand SharePoint's limits.

### `Projects`
| # | Column | Type |
|---|---|---|
| 1 | Title | (exists) — project name |
| 2 | ProjectCode | Single line |
| 3 | Service | Single line |
| 4 | ScorecardDomain | Single line |
| 5 | Priority | Single line |
| 6 | Phase | Single line |
| 7 | PMName | Single line |
| 8 | PMEmail | Single line |
| 9 | Sponsor | Single line |
| 10 | StartDate | Date only |
| 11 | TargetEndDate | Date only |
| 12 | Objective | Multiple lines (plain) |
| 13 | MetricName | Single line |
| 14 | MetricBaseline | Number (1 decimal) |
| 15 | MetricTarget | Number (1 decimal) |
| 16 | MetricCurrent | Number (1 decimal) |
| 17 | CurrentHealth | Single line |
| 18 | PercentComplete | Number (0 decimals) |
| 19 | LastUpdateWeek | Date only |
| 20 | IsActive | Yes/No (default Yes) |

### `Milestones`
| Column | Type |
|---|---|
| Title | (exists) |
| ProjectID | Number |
| Sequence | Number |
| PlannedDate | Date only |
| ForecastDate | Date only |
| ActualDate | Date only |
| Status | Single line |

### `StatusUpdates`
| Column | Type |
|---|---|
| Title | (exists) |
| ProjectID | Number |
| WeekOf | Date only |
| Health | Single line |
| PercentComplete | Number (0) |
| MetricValue | Number (1 decimal) |
| Accomplishments | Multiple lines (plain) |
| NextSteps | Multiple lines (plain) |
| Blockers | Multiple lines (plain) |
| SubmittedBy | Single line |

### `Risks`
| Column | Type |
|---|---|
| Title | (exists) |
| ProjectID | Number |
| Likelihood | Number (0) |
| Impact | Number (0) |
| RiskScore | Number (0) |
| Mitigation | Multiple lines (plain) |
| Owner | Single line |
| Status | Single line |

### `ActionItems`
| Column | Type |
|---|---|
| Title | (exists) |
| ProjectID | Number |
| OwnerName | Single line |
| OwnerEmail | Single line |
| DueDate | Date only |
| Status | Single line |
| CompletedOn | Date only |

### `PMOTeam`
Title only, holding the lowercase emails of PMO staff (people who can see admin features).

### Indexes (scale talking point)
*List settings → Indexed columns → Create a new index:* **ProjectID** on Milestones, StatusUpdates, Risks and ActionItems. Also **IsActive** and **PMEmail** on Projects, and **OwnerEmail** and **Status** on ActionItems.

### Paste the data
Do **Projects first**: in Excel, copy all data rows (not the header) → in the list, **Edit in grid view** → click the first cell → paste → **Exit grid view**. Check that **Projects has IDs 1–10 in order**, because every child row points at those IDs. If they're off, delete the list, recreate it, and paste once. Then paste the other lists in any order.

If Yes/No didn't paste: set **IsActive = No** for PRJ-109 and PRJ-110 by hand.

---

## 2. Solution (≈10 min)

make.powerapps.com → your environment (**Kaviya Raja's Environment**) → **Solutions → + New solution**
- Display name **PMO Project Hub** · Publisher **+ New publisher** (your name, prefix `kr`) · Version **1.0.0.0**

Inside the solution: **+ New → More → Environment variable** → **PMO App Link** (Text, leave empty for now).

**Create everything from inside this solution:** *+ New → App → Canvas app* and *+ New → Automation → Cloud flow*.

---

## 3. App foundation (≈30 min)

1. **+ New → App → Canvas app** → name **PMO Project Hub**, format **Tablet**.
2. **Settings:**
   - Search "environment variables" → turn **on** *Automatically create environment variables when adding data sources*.
   - **General → Data row limit → 2000**.
   - Search "user-defined functions" → make sure it's **on** (needed for the functions below).
3. **Add data:** SharePoint → your site → all 6 lists. Also add **Office 365 Users**.
4. Use **Classic** controls (in the Insert pane, expand *Classic*). Rename every control in the Tree view with prefixes (`scr gal lbl btn txt drp cmb dp sld rect`).

### App.Formulas
```powerfx
// ---------- Theme: VA Design System (VADS) neutrals + alert backgrounds ----------
// Source: design.va.gov/foundation/color-palette
nfBaseDarkest = ColorValue("#1b1b1b");   // vads-color-base-darkest: headings
nfBaseDarker  = ColorValue("#3d4551");   // vads-color-base-darker: body text
nfBaseDark    = ColorValue("#565c65");   // vads-color-base-dark: secondary text, icons
nfBaseMedium  = ColorValue("#71767a");   // vads-color-base-medium: secondary text
nfBaseLight   = ColorValue("#a9aeb1");   // vads-color-base-light: borders, disabled
nfBaseLighter = ColorValue("#dfe1e2");   // vads-color-base-lighter: dividers
nfMuted       = ColorValue("#f0f0f0");   // vads-color-background-muted: subtle panels
nfPage        = ColorValue("#ffffff");   // vads-color-background: page
nfInfoBg      = ColorValue("#e7f6f8");   // info alert background (cyan-5)
nfErrorBg     = ColorValue("#f4e3db");   // error alert background (red-warm-10)
nfSuccessBg   = ColorValue("#ecf3ec");   // success alert background (green-cool-5)
nfWarningBg   = ColorValue("#faf3d1");   // warning alert background (yellow-5)

// Accents (header, buttons, chart bars): saturated, used sparingly
nfNavy  = ColorValue("#112E51");
nfBlue  = ColorValue("#0071BC");
nfGreen = ColorValue("#2E8540");
nfAmber = ColorValue("#FDB81E");   // always with dark text
nfRed   = ColorValue("#CD2026");
nfGray  = nfBaseDark;               // older formulas below still say nfGray
nfLight = nfMuted;                  // older formulas below still say nfLight

// ---------- User + role ----------
nfMe    = Lower(User().Email);
nfIsPMO = !IsBlank(LookUp(PMOTeam, Title = nfMe));

// ---------- Reporting calendar (weeks start Monday) ----------
nfThisWeek   = DateAdd(Today(), -(Weekday(Today(), StartOfWeek.Monday) - 1), TimeUnit.Days);
nfReportWeek = DateAdd(nfThisWeek, -7, TimeUnit.Days);   // updates are due for last week

// ---------- Reusable logic (user-defined functions) ----------
HealthColor(h: Text): Color = Switch(h, "Green", nfGreen, "Yellow", nfAmber, "Red", nfRed, nfGray);
HealthInk(h: Text): Color = If(h = "Yellow", nfBaseDarkest, Color.White);
// Status chips and banners use the VADS alert backgrounds with dark text (high contrast, calm look)
HealthBg(h: Text): Color = Switch(h, "Green", nfSuccessBg, "Yellow", nfWarningBg, "Red", nfErrorBg, nfInfoBg);

// Share of the way from baseline to target (0-1). Works whether lower or higher is better.
MetricProgress(base: Number, target: Number, current: Number): Number =
    If(base = target, 1, Max(0, Min(1, (base - current) / (base - target))));

// Positive = late, negative = early
SlipDays(planned: Date, actualOrForecast: Date): Number = DateDiff(planned, actualOrForecast, TimeUnit.Days);
```

### App.OnStart
```powerfx
Set(varTab, "Overview");
Set(varBusy, false)
```

### App.StartScreen (deep links from Teams open the right screen)
```powerfx
Switch(Param("screen"), "update", scrUpdate, "project", scrProject, scrPortfolio)
```

### Header (build once, copy to every screen)
- `rectHeader`: Width `Parent.Width`, Height 64, Fill `nfNavy`
- `lblAppName`: `"PMO Project Hub"`, White, Size 20, Bold
- Nav buttons (transparent fill, white text): **Portfolio** → `Navigate(scrPortfolio)` · **Analytics** → `Navigate(scrAnalytics)` · **My work** → `Navigate(scrMyWork)`
- `lblDemo`: `"Demo · fictitious data"`, Color `nfAmber`, Size 11

---

## 4. Screens (≈4–5 h)

### 4.1 `scrPortfolio` — the executive landing page
**OnVisible:**
```powerfx
Concurrent(
    ClearCollect(colProjects, Filter(Projects, IsActive = true)),
    ClearCollect(colMilestones, Milestones),
    ClearCollect(colOpenActions, Filter(ActionItems, Status = "Open"))
)
```

**KPI tiles** (5 rounded rectangles, big number Size 32, caption Size 13):
| Caption | Number formula |
|---|---|
| Active projects | `CountRows(colProjects)` |
| On track (green) | `Text(CountIf(colProjects, CurrentHealth = "Green") / Max(1, CountRows(colProjects)), "0%")` |
| Milestones finished on time | `With({d: Filter(colMilestones, Status = "Done")}, Text(CountIf(d, ActualDate <= PlannedDate) / Max(1, CountRows(d)), "0%"))` |
| Overdue actions | `CountIf(colOpenActions, DueDate < Today())` → Color `If(Value(Self.Text) > 0, nfRed, nfNavy)` |
| Missing last week's update | `CountIf(colProjects, IsBlank(LastUpdateWeek) \|\| LastUpdateWeek < nfReportWeek)` |

**Filters:**
- `drpService` Items: `Table({Value: "All services"}, Sort(Distinct(colProjects, Service), Value))`
- `drpHealth` Items: `["All", "Green", "Yellow", "Red"]`
- `txtSearch` HintText `"Search project or code"`

**`galProjects`** (vertical, WrapCount 2, TemplateSize ≈ 170) **Items:**
```powerfx
Sort(
    Filter(
        colProjects,
        (drpService.Selected.Value = "All services" || Service = drpService.Selected.Value) &&
        (drpHealth.Selected.Value = "All" || CurrentHealth = drpHealth.Selected.Value) &&
        (IsBlank(txtSearch.Text) || txtSearch.Text in Title || txtSearch.Text in ProjectCode)
    ),
    ProjectCode
)
```
Card template:
- `ThisItem.ProjectCode & " · " & ThisItem.Service` (Size 12, gray) and `ThisItem.Title` (Size 16, bold)
- **Health chip (VADS alert style):** rectangle Fill `HealthBg(ThisItem.CurrentHealth)`, BorderColor `HealthColor(ThisItem.CurrentHealth)`, BorderThickness 2 + label Text `ThisItem.CurrentHealth`, Color `nfBaseDarkest`
- **Card itself:** Fill `nfPage`, BorderColor `nfBaseLighter`; screen Fill `nfMuted`; body text Color `nfBaseDarker`, secondary text `nfBaseMedium`
- `"PM: " & ThisItem.PMName & " · " & ThisItem.Phase`
- **Metric progress bar:** a gray background rectangle (Width `Parent.TemplateWidth - 48`, Height 8) plus a blue rectangle on top with Width:
```powerfx
(Parent.TemplateWidth - 48) * MetricProgress(ThisItem.MetricBaseline, ThisItem.MetricTarget, ThisItem.MetricCurrent)
```
- Metric label: `ThisItem.MetricName & ": " & ThisItem.MetricCurrent & " (target " & ThisItem.MetricTarget & ")"`
- **Stale flag:**
```powerfx
// Text
If(IsBlank(ThisItem.LastUpdateWeek) || ThisItem.LastUpdateWeek < nfReportWeek,
   "No update for week of " & Text(nfReportWeek, "mmm d"),
   "Updated week of " & Text(ThisItem.LastUpdateWeek, "mmm d"))
// Color
If(IsBlank(ThisItem.LastUpdateWeek) || ThisItem.LastUpdateWeek < nfReportWeek, nfRed, nfGray)
```
- **OnSelect:** `Set(varProject, ThisItem); Set(varTab, "Overview"); Navigate(scrProject, ScreenTransition.Fade)`

### 4.2 `scrProject` — one project, five tabs
**OnVisible:**
```powerfx
If(IsBlank(varProject) && !IsBlank(Param("projectId")),
   Set(varProject, LookUp(Projects, ID = Value(Param("projectId")))));
Concurrent(
    ClearCollect(colPM, Sort(Filter(Milestones, ProjectID = varProject.ID), Sequence)),
    ClearCollect(colPU, Sort(Filter(StatusUpdates, ProjectID = varProject.ID), WeekOf, SortOrder.Ascending)),
    ClearCollect(colPR, Filter(Risks, ProjectID = varProject.ID)),
    ClearCollect(colPA, Filter(ActionItems, ProjectID = varProject.ID))
)
```
Top band: `varProject.ProjectCode & " · " & varProject.Title`, PM, sponsor, phase, health chip (same formulas as the card, using `varProject`).

Buttons on the right:
- **Post weekly update** → `Navigate(scrUpdate)`
- **Status report (PDF)** → see Flow B (Section 5)

**Tabs:** a horizontal gallery `galTabs` with Items `["Overview", "Milestones", "Status history", "Risks", "Actions"]`, OnSelect `Set(varTab, ThisItem.Value)`, and an underline rectangle Visible `ThisItem.Value = varTab`. Put each tab's controls in its own **container** with Visible `varTab = "Overview"` (etc.).

**Overview tab**
- `varProject.Objective`
- Metric card: `"Baseline " & varProject.MetricBaseline & " → now " & varProject.MetricCurrent & " → target " & varProject.MetricTarget` and `Text(MetricProgress(varProject.MetricBaseline, varProject.MetricTarget, varProject.MetricCurrent), "0%") & " of the way to target"`
- **`chtMetric`** (Classic → *Line chart*) Items, a 2-series chart (actual vs. target):
```powerfx
ShowColumns(
    AddColumns(colPU, Week, Text(WeekOf, "mmm d"), Target, varProject.MetricTarget),
    Week, MetricValue, Target
)
```
  Set NumberOfSeries `2`. Title: `varProject.MetricName & " by week"`.
- **Health strip:** horizontal gallery of `colPU`, a 28×28 square Fill `HealthColor(ThisItem.Health)`, a label `Text(ThisItem.WeekOf, "m/d")`. Tooltip `ThisItem.Health & ": " & ThisItem.Blockers`.

**Milestones tab** — `galMilestones` Items `colPM`:
- Name, `"Planned " & Text(ThisItem.PlannedDate, "mmm d")`, `If(IsBlank(ThisItem.ActualDate), "Forecast " & Text(ThisItem.ForecastDate, "mmm d"), "Done " & Text(ThisItem.ActualDate, "mmm d"))`, Status
- **Variance badge:**
```powerfx
// Text
With({v: SlipDays(ThisItem.PlannedDate, Coalesce(ThisItem.ActualDate, ThisItem.ForecastDate))},
     If(v > 0, "+" & v & " days late", v < 0, Abs(v) & " days early", "On time"))
// Color
If(SlipDays(ThisItem.PlannedDate, Coalesce(ThisItem.ActualDate, ThisItem.ForecastDate)) > 0, nfRed, nfGreen)
```
- **Mini timeline:** inside each row, a 6×6 rotated-look diamond (use an icon or a small square) at X:
```powerfx
300 + 400 * DateDiff(varProject.StartDate, ThisItem.PlannedDate) / Max(1, DateDiff(varProject.StartDate, varProject.TargetEndDate))
```

**Status history tab** — `galHistory` Items `Sort(colPU, WeekOf, SortOrder.Descending)`: week, health chip, % complete, metric value, accomplishments, next steps, blockers.

**Risks tab** — the **5×5 heat map** (`galHeat`, vertical, **WrapCount 5**, TemplateSize 56, Width 300):
```powerfx
// Items: 25 cells, top row = likelihood 5
ForAll(Sequence(25) As s, {L: 5 - RoundDown((s.Value - 1) / 5, 0), I: Mod(s.Value - 1, 5) + 1})
```
- Cell rectangle Fill:
```powerfx
With({score: ThisItem.L * ThisItem.I},
     ColorFade(If(score >= 15, nfRed, score >= 8, nfAmber, nfGreen), 0.55))
```
- Count label: `With({n: CountIf(colPR, Likelihood = ThisItem.L && Impact = ThisItem.I && Status <> "Closed")}, If(n = 0, "", Text(n)))`, Size 18, bold
- Axis labels outside the gallery: `"Likelihood ↑"` (rotated 270) and `"Impact →"`

Next to it: `galRisks` Items `Sort(colPR, RiskScore, SortOrder.Descending)` showing title, `"Score " & ThisItem.RiskScore`, mitigation, owner, status.

**Add risk** (small form): `txtRiskTitle`, `sldLikelihood` (1–5), `sldImpact` (1–5), `txtMitigation` → `btnAddRisk`:
```powerfx
Patch(Risks, Defaults(Risks), {
    Title: txtRiskTitle.Text, ProjectID: varProject.ID,
    Likelihood: sldLikelihood.Value, Impact: sldImpact.Value,
    RiskScore: sldLikelihood.Value * sldImpact.Value,
    Mitigation: txtMitigation.Text, Owner: User().FullName, Status: "Open"
});
If(IsEmpty(Errors(Risks)),
   ClearCollect(colPR, Filter(Risks, ProjectID = varProject.ID)); Reset(txtRiskTitle); Reset(txtMitigation);
   Notify("Risk added", NotificationType.Success),
   Notify("Couldn't save: " & First(Errors(Risks)).Message, NotificationType.Error))
```

**Actions tab** — `galActions` Items `Sort(colPA, DueDate, SortOrder.Ascending)`:
- Checkbox `chkDone`: Default `ThisItem.Status = "Done"`, **OnCheck:**
```powerfx
Patch(ActionItems, LookUp(ActionItems, ID = ThisItem.ID), {Status: "Done", CompletedOn: Today()})
```
  **OnUncheck:** `Patch(ActionItems, LookUp(ActionItems, ID = ThisItem.ID), {Status: "Open", CompletedOn: Blank()})`
- Due label Color: `If(ThisItem.Status = "Open" && ThisItem.DueDate < Today(), nfRed, nfGray)`

**Add action:** `txtActionTitle`, `cmbActionOwner` (Items `If(Len(Self.SearchText) >= 2, Office365Users.SearchUserV2({searchTerm: Self.SearchText, top: 10}).value)`, DisplayFields `["DisplayName"]`, SearchFields `["DisplayName"]`, SelectMultiple false), `dpActionDue` → `btnAddAction`:
```powerfx
Patch(ActionItems, Defaults(ActionItems), {
    Title: txtActionTitle.Text, ProjectID: varProject.ID,
    OwnerName: cmbActionOwner.Selected.DisplayName, OwnerEmail: Lower(cmbActionOwner.Selected.Mail),
    DueDate: dpActionDue.SelectedDate, Status: "Open"
});
If(IsEmpty(Errors(ActionItems)),
   ClearCollect(colPA, Filter(ActionItems, ProjectID = varProject.ID)); Reset(txtActionTitle); Reset(cmbActionOwner);
   Notify("Action assigned to " & cmbActionOwner.Selected.DisplayName, NotificationType.Success),
   Notify("Couldn't save: " & First(Errors(ActionItems)).Message, NotificationType.Error))
```
DisplayMode: `If(IsBlank(txtActionTitle.Text) || IsBlank(cmbActionOwner.Selected.Mail) || IsBlank(dpActionDue.SelectedDate), DisplayMode.Disabled, DisplayMode.Edit)`

### 4.3 `scrUpdate` — the 2-minute weekly update (data quality built in)
**OnVisible** (copies last week forward so PMs only change what moved):
```powerfx
If(IsBlank(varProject) && !IsBlank(Param("projectId")),
   Set(varProject, LookUp(Projects, ID = Value(Param("projectId")))));
ClearCollect(colPU, Sort(Filter(StatusUpdates, ProjectID = varProject.ID), WeekOf, SortOrder.Ascending));
Set(varLast, Last(colPU))
```
| Control | Properties |
|---|---|
| `lblFor` | `"Weekly update · " & varProject.ProjectCode & " " & varProject.Title` |
| `dpWeek` (Date picker) | DefaultDate `nfReportWeek` · label `"Week of (Monday)"` |
| `lblExisting` | Visible `!IsBlank(LookUp(colPU, Text(WeekOf, "yyyy-mm-dd") = Text(dpWeek.SelectedDate, "yyyy-mm-dd")))` · Text `"An update already exists for this week — saving will replace it."` |
| `radHealth` (Radio, horizontal) | Items `["Green", "Yellow", "Red"]` · Default `Coalesce(varLast.Health, "Green")` |
| `sldPercent` | Min 0 · Max 100 · Default `Coalesce(varLast.PercentComplete, 0)` |
| `txtMetric` | Format `TextFormat.Number` · Default `Coalesce(varLast.MetricValue, varProject.MetricBaseline)` · label `varProject.MetricName & " this week"` |
| `txtAcc` / `txtNext` / `txtBlockers` | multi-line · `txtNext` Default `Coalesce(varLast.NextSteps, "")` · `txtBlockers` label `"Blockers (required if Yellow or Red)"` |

**`btnSubmitUpdate`** DisplayMode (validation):
```powerfx
If(
    IsBlank(dpWeek.SelectedDate) || IsBlank(txtMetric.Text) || IsBlank(Trim(txtAcc.Text)) ||
    (radHealth.Selected.Value <> "Green" && Len(Trim(txtBlockers.Text)) < 5),
    DisplayMode.Disabled, DisplayMode.Edit
)
```
**OnSelect** (insert or update, so there's never a duplicate week; then keeps the project's latest values in sync):
```powerfx
With(
    {wExisting: LookUp(colPU, Text(WeekOf, "yyyy-mm-dd") = Text(dpWeek.SelectedDate, "yyyy-mm-dd"))},
    Patch(
        StatusUpdates,
        If(IsBlank(wExisting), Defaults(StatusUpdates), LookUp(StatusUpdates, ID = wExisting.ID)),
        {
            Title: varProject.ProjectCode & " week of " & Text(dpWeek.SelectedDate, "m/d/yyyy"),
            ProjectID: varProject.ID, WeekOf: dpWeek.SelectedDate,
            Health: radHealth.Selected.Value, PercentComplete: sldPercent.Value,
            MetricValue: Value(txtMetric.Text),
            Accomplishments: txtAcc.Text, NextSteps: txtNext.Text, Blockers: txtBlockers.Text,
            SubmittedBy: User().FullName
        }
    )
);
If(
    IsEmpty(Errors(StatusUpdates)),
    If(IsBlank(varProject.LastUpdateWeek) || dpWeek.SelectedDate >= varProject.LastUpdateWeek,
       Patch(Projects, LookUp(Projects, ID = varProject.ID), {
           CurrentHealth: radHealth.Selected.Value, PercentComplete: sldPercent.Value,
           MetricCurrent: Value(txtMetric.Text), LastUpdateWeek: dpWeek.SelectedDate }));
    Set(varProject, LookUp(Projects, ID = varProject.ID));
    Reset(txtAcc); Reset(txtBlockers);
    Notify("Update saved. Thank you!", NotificationType.Success);
    Navigate(scrProject, ScreenTransition.Fade),
    Notify("Couldn't save: " & First(Errors(StatusUpdates)).Message, NotificationType.Error)
)
```

### 4.4 `scrAnalytics` — the data showcase
**OnVisible:**
```powerfx
ClearCollect(colAllUpdates, StatusUpdates);
ClearCollect(colAllRisks, Filter(Risks, Status = "Open"));
ClearCollect(colProjects, Filter(Projects, IsActive = true));
ClearCollect(colMilestones, Milestones);
// 8-week portfolio health trend
ClearCollect(
    colTrend,
    AddColumns(
        Sort(Distinct(colAllUpdates, WeekOf), Value) As w,
        Week, Text(w.Value, "mmm d"),
        G, CountIf(colAllUpdates, WeekOf = w.Value && Health = "Green"),
        Y, CountIf(colAllUpdates, WeekOf = w.Value && Health = "Yellow"),
        R, CountIf(colAllUpdates, WeekOf = w.Value && Health = "Red")
    )
);
Set(varTrendMax, Max(1, Max(colTrend, G + Y + R)));
// Schedule slip per project (worst milestone)
ClearCollect(
    colSlip,
    AddColumns(
        colProjects As pr,
        Slip, Max(Filter(colMilestones, ProjectID = pr.ID), SlipDays(PlannedDate, Coalesce(ActualDate, ForecastDate))),
        Progress, MetricProgress(pr.MetricBaseline, pr.MetricTarget, pr.MetricCurrent)
    )
);
Set(varGStart, Min(colProjects, StartDate));
Set(varGEnd, Max(colProjects, TargetEndDate))
```

Four panels (2×2). Each gets a **title that states the finding**, not just the topic:

**A. Health trend (stacked bars built from a gallery)** — `galTrend`, horizontal, Items `colTrend`, TemplateSize 72:
- `rectG`: Height `160 * ThisItem.G / varTrendMax` · Y `190 - Self.Height` · Fill `nfGreen`
- `rectY`: Height `160 * ThisItem.Y / varTrendMax` · Y `rectG.Y - Self.Height` · Fill `nfAmber`
- `rectR`: Height `160 * ThisItem.R / varTrendMax` · Y `rectY.Y - Self.Height` · Fill `nfRed`
- `lblWeek`: `ThisItem.Week` at Y 196
- Panel title: `"Portfolio health, last " & CountRows(colTrend) & " weeks"`

**B. Progress to target** — `galProgress` Items `Sort(colSlip, Progress, SortOrder.Descending)`:
- Name label (Width 220), a bar with Width `300 * ThisItem.Progress` and Fill `HealthColor(ThisItem.CurrentHealth)`, then `Text(ThisItem.Progress, "0%")`

**C. Schedule slip** — `galSlip` Items `Sort(colSlip, Slip, SortOrder.Descending)`:
- Bar Width `Min(300, 8 * Max(0, ThisItem.Slip))`, Fill `If(ThisItem.Slip > 7, nfRed, ThisItem.Slip > 0, nfAmber, nfGreen)`
- Label `If(ThisItem.Slip > 0, "+" & ThisItem.Slip & " days", "On schedule")`

**D. Portfolio Gantt** — `galGantt` Items `Sort(colProjects, StartDate)`, TemplateSize 36:
- `lblGName`: `ThisItem.ProjectCode` (Width 90)
- `rectBar`: X `100 + (Parent.TemplateWidth - 120) * DateDiff(varGStart, ThisItem.StartDate) / DateDiff(varGStart, varGEnd)` · Width `(Parent.TemplateWidth - 120) * DateDiff(ThisItem.StartDate, ThisItem.TargetEndDate) / DateDiff(varGStart, varGEnd)` · Height 18 · Fill `ColorFade(HealthColor(ThisItem.CurrentHealth), 0.3)`
- **Today line** (a 2 px rectangle *outside* the gallery, on top): X `galGantt.X + 100 + (galGantt.Width - 120) * DateDiff(varGStart, Today()) / DateDiff(varGStart, varGEnd)` · Y `galGantt.Y` · Height `galGantt.Height` · Fill `nfNavy`

**Portfolio risk heat map** (if space allows): copy `galHeat` from the Risks tab and change `colPR` to `colAllRisks`.

**Auto-written headline** (`lblInsight`, top of the screen, Size 16). This is "communicate concisely" in one line:
```powerfx
CountIf(colProjects, CurrentHealth = "Green") & " of " & CountRows(colProjects) & " active projects are on track. " &
"Furthest behind: " & First(Sort(colSlip, Slip, SortOrder.Descending)).ProjectCode &
" (+" & First(Sort(colSlip, Slip, SortOrder.Descending)).Slip & " days). " &
CountRows(Filter(colAllRisks, RiskScore >= 15)) & " open high risks."
```

### 4.5 `scrMyWork` — everyone's personal view
- **My projects:** `Filter(Projects, PMEmail = nfMe && IsActive = true)`, each with the stale flag plus a **Post update** button (`Set(varProject, ThisItem); Navigate(scrUpdate)`).
- **My open actions:** `Sort(Filter(ActionItems, OwnerEmail = nfMe && Status = "Open"), DueDate)`, using the same checkbox as the Actions tab, with overdue items in red.

---

## 5a. Internal column names (needed for flow filters)

The lists were created with SharePoint's **Import from CSV**, which gives columns internal names like `field_1`. **Power Apps is unaffected** (it uses the display names, so every formula above works as written). **Power Automate is different:** in *Filter Query* and *Order By* boxes, and in `item()?['…']` expressions, use the internal name. Dynamic-content chips you pick from the panel handle this for you.

| List | Display name → internal name |
|---|---|
| Projects | ProjectCode `field_1` · Service `field_2` · ScorecardDomain `field_3` · Priority `field_4` · Phase `field_5` · PMName `field_6` · PMEmail `field_7` · Sponsor `field_8` · StartDate `field_9` · TargetEndDate `field_10` · Objective `field_11` · MetricName `field_12` · MetricBaseline `field_13` · MetricTarget `field_14` · MetricCurrent `field_15` · CurrentHealth `field_16` · PercentComplete `field_17` · LastUpdateWeek `field_18` · IsActive `field_19` |
| Milestones | ProjectID `field_1` · Sequence `field_2` · PlannedDate `field_3` · ForecastDate `field_4` · ActualDate `field_5` · Status `field_6` |
| StatusUpdates | ProjectID `field_1` · WeekOf `field_2` · Health `field_3` · PercentComplete `field_4` · MetricValue `field_5` · Accomplishments `field_6` · NextSteps `field_7` · Blockers `field_8` · SubmittedBy `field_9` |
| Risks | ProjectID `field_1` · Likelihood `field_2` · Impact `field_3` · RiskScore `field_4` · Mitigation `field_5` · Owner `field_6` · Status `field_7` |
| ActionItems | ProjectID `field_1` · OwnerName `field_2` · OwnerEmail `field_3` · DueDate `field_4` · Status `field_5` · CompletedOn `field_6` |
| PMOTeam | Title only |

Examples: Flow B's `ProjectID eq 3` becomes `field_1 eq 3`; `Order By WeekOf desc` becomes `field_2 desc`; `item()?['PlannedDate']` becomes `item()?['field_3']`.

## 5. Power Automate flows (≈1.5–2 h)

Create both **inside the solution**. Whenever an action asks for the SharePoint site or list, pick the **environment variable** at the bottom of the dropdown.

Get the app link first: **Save + Publish** the app → solution → app → **Details** → copy the **Web link** → paste it as the value of the **PMO App Link** environment variable.

### Flow A — `PMO Weekly Update Reminder` (scheduled)
1. **Recurrence:** every 1 week, on **Friday**, at 10:00, time zone Pacific.
2. **SharePoint · Get items** (Projects) · Filter Query: `IsActive eq 1`
3. **Compose** `Report week Monday` (expression):
   `formatDateTime(addDays(startOfDay(convertFromUtc(utcNow(), 'Pacific Standard Time')), sub(1, dayOfWeek(convertFromUtc(utcNow(), 'Pacific Standard Time')))), 'yyyy-MM-dd')`
   *(On a Friday that gives the Monday of the **current** week. PMs are reminded to post this week's update before the weekend.)*
4. **Apply to each** (value from Get items) → **Condition** (Advanced mode):
   `@and(not(contains(items('Apply_to_each')?['PMEmail'], 'example.org')), or(empty(items('Apply_to_each')?['LastUpdateWeek']), less(items('Apply_to_each')?['LastUpdateWeek'], outputs('Report_week_Monday'))))`
   - **If yes → Teams · Post message in a chat or channel** (Flow bot · Chat with Flow bot · Recipient = `PMEmail`):
   > Hi! **[ProjectCode] [Title]** doesn't have a status update for this week yet. It takes 2 minutes: [Post update](`@{parameters('PMO App Link (kr_PMOAppLink)')}&screen=update&projectId=@{items('Apply_to_each')?['ID']}`)

   Insert the env var from dynamic content rather than typing its name. If your web link has no `?` in it, use `?screen=` instead of `&screen=`.
5. **Test → Manually.** You'll get one Teams reminder for each of your 3 projects (none has this week's update yet). Click a link: it should open straight on that project's update form. **Screenshot that.**

### Flow B — `PMO Status Report` (called from the app, returns a PDF link)
1. **Trigger:** *Power Apps (V2)* → add input **Number** named `ProjectID`.
2. **SharePoint · Get item** (Projects, Id = `ProjectID`) → rename to `Get project`.
3. **SharePoint · Get items** (StatusUpdates) → Filter `ProjectID eq @{triggerBody()['number']}` · Order By `WeekOf desc` · Top Count `1` → rename `Get latest update`.
4. **Get items** (Milestones) Filter `ProjectID eq …` Order By `Sequence` → **Data operation · Select** (Map: `Milestone` = Title, `Planned` = `formatDateTime(item()?['PlannedDate'], 'MMM d')`, `Forecast or actual` = `formatDateTime(coalesce(item()?['ActualDate'], item()?['ForecastDate']), 'MMM d')`, `Status` = Status) → **Create HTML table** (from Select).
5. **Get items** (Risks) Filter `ProjectID eq … and Status eq 'Open'` → Select (Risk, Score, Mitigation) → Create HTML table.
6. **Get items** (ActionItems) Filter `ProjectID eq … and Status eq 'Open'` → Select (Action, Owner, Due) → Create HTML table.
7. **Compose** `Report HTML`:
```html
<html><body style="font-family:Segoe UI,Arial,sans-serif;color:#1b1b1b;margin:32px">
<h1 style="color:#112E51;margin-bottom:4px">@{body('Get_project')?['ProjectCode']} · @{body('Get_project')?['Title']}</h1>
<p>PM: @{body('Get_project')?['PMName']} · Sponsor: @{body('Get_project')?['Sponsor']} · Phase: @{body('Get_project')?['Phase']}</p>
<p><b>Health:</b> @{first(body('Get_latest_update')?['value'])?['Health']} · <b>Week of:</b> @{formatDateTime(first(body('Get_latest_update')?['value'])?['WeekOf'], 'MMM d, yyyy')} · <b>Complete:</b> @{first(body('Get_latest_update')?['value'])?['PercentComplete']}%</p>
<h2 style="color:#112E51">Metric</h2>
<p>@{body('Get_project')?['MetricName']}: baseline @{body('Get_project')?['MetricBaseline']} → now @{body('Get_project')?['MetricCurrent']} → target @{body('Get_project')?['MetricTarget']}</p>
<h2 style="color:#112E51">This week</h2>
<p><b>Accomplishments:</b> @{first(body('Get_latest_update')?['value'])?['Accomplishments']}</p>
<p><b>Next steps:</b> @{first(body('Get_latest_update')?['value'])?['NextSteps']}</p>
<p><b>Blockers:</b> @{first(body('Get_latest_update')?['value'])?['Blockers']}</p>
<h2 style="color:#112E51">Milestones</h2>@{body('Create_HTML_table_milestones')}
<h2 style="color:#112E51">Open risks</h2>@{body('Create_HTML_table_risks')}
<h2 style="color:#112E51">Open actions</h2>@{body('Create_HTML_table_actions')}
<p style="color:#5B616B;font-size:11px">Generated by PMO Project Hub · demo data</p>
</body></html>
```
   *(Rename the three Create HTML table actions to match the names in the expressions.)*
8. **OneDrive for Business · Create file** → Folder `/PMO Reports` · Name `@{body('Get_project')?['ProjectCode']}-@{formatDateTime(utcNow(),'yyyy-MM-dd')}.html` · Content = `Report HTML` output.
9. **OneDrive for Business · Convert file** → File = *Id* from Create file · Target type **PDF**.
10. **OneDrive for Business · Create file** → same folder, name ending `.pdf`, content = *File content* from Convert file.
11. **OneDrive for Business · Create share link** → File = the PDF's Id · Link type View · Scope Organization.
12. **Respond to a Power App or flow** → Text output **reporturl** = the share link's *Web URL*.

**In the app** (`scrProject`): **Add data → Power Automate → PMO Status Report**. Then the button:
- **OnSelect:**
```powerfx
Set(varBusy, true);
Set(varReport, PMOStatusReport.Run(varProject.ID));
Set(varBusy, false);
Launch(varReport.reporturl)
```
- **DisplayMode:** `If(varBusy, DisplayMode.Disabled, DisplayMode.Edit)` · **Text:** `If(varBusy, "Building report…", "Status report (PDF)")`

*(If IntelliSense shows the flow under a slightly different name, use that one.)*

---

## 6. Quality pass (≈45 min)
- **App checker** (stethoscope icon): clear *Formulas* and *Accessibility*.
- **Section 508:**
  - Every input has an AccessibleLabel; decorative shapes have TabIndex -1.
  - Health is always **text + color**; Yellow uses navy text.
  - Visible focus (FocusedBorderThickness 3).
  - Body text ≥ 14; buttons ≥ 44 px tall.
- **Live monitor** (Studio → *Advanced tools → Monitor*): open Portfolio and Project, then screenshot the network calls showing the filtered, delegated SharePoint requests. This is your **troubleshooting** evidence, which the posting names.
- **Solution checker:** Solutions → PMO Project Hub → Solution checker → Run → screenshot.

## 7. ALM: export (≈15 min)
**Publish all customizations → Export solution →** version **1.1.0.0** → **Managed** → Export. Screenshot the solution objects list (app, 2 flows, env vars, connection references) and the export dialog.

Caption: *"SharePoint lists live outside the solution; on import to Test/Prod only the environment variables change."*

## 8. Stretch (only if core is solid)
- **Run it in Teams:** Solution → app → *Add to Teams*, or in the **Improvement Triage** channel: **+ → Power Apps → PMO Project Hub**. Screenshot it inside Teams.
- **Component library:** turn the header into a component with a `ScreenTitle` input.
- **Data-quality panel** on Analytics:
  - Milestones past their planned date with no actual and status not Done: `CountIf(colMilestones, IsBlank(ActualDate) && PlannedDate < Today() && Status <> "Done")`
  - Open actions with no owner email
  - Projects missing an update for 2+ weeks

---

## 9. Test script (also goes in the Launch Kit)
| # | Test | Expected |
|---|---|---|
| 1 | Portfolio loads | 8 active projects; KPIs filled; PRJ-106 + PRJ-108 flagged "No update" |
| 2 | Filter Service + Health, search "PRJ-10" | Cards filter instantly |
| 3 | Open PRJ-103 → Overview | Metric line vs. target; Yellow/Red health strip |
| 4 | Milestones tab | Late milestones show "+N days late" in red |
| 5 | Risks tab | Heat map counts match the risk list |
| 6 | Post update with Yellow + empty blockers | Submit disabled |
| 7 | Post update for a week that already has one | Warning shown; saving replaces it (no duplicate row) |
| 8 | Post update for PRJ-108 | Card no longer stale; Analytics trend includes it |
| 9 | Add action assigned to yourself | Shows in My work |
| 10 | Status report (PDF) | Button shows "Building report…", then a PDF opens with all sections |
| 11 | Run Flow A manually | Teams message for PRJ-108; link opens its update form |
| 12 | Keyboard-only: post an update | Every control reachable, focus visible |

## 10. Screenshot shot list
| # | Screenshot | Caption idea | Criteria |
|---|---|---|---|
| 1 | Portfolio | "Portfolio health at a glance: KPIs, filters, and stale-update flags computed from weekly data." | C, D |
| 2 | Project → Overview (metric chart) | "Each project tracks its own improvement metric against target; progress math works whether lower or higher is better." | A, C |
| 3 | Risks heat map | "Risk exposure = likelihood × impact, visualized as a 5×5 heat map." | A, C |
| 4 | Weekly update form | "2-minute update: copies last week forward, prevents duplicate weeks, requires blockers when not green." | D, A |
| 5 | Analytics (all 4 panels + headline) | "Portfolio analytics with an auto-written headline for executives." | C, A |
| 6 | Teams reminder + update form it opened | "Friday flow nudges PMs in Teams; a deep link opens the exact form." | B, A |
| 7 | PDF status report | "One click turns 5 lists into a formatted status report." | C, B |
| 8 | Solution objects + checker + Monitor | "Built as a solution (env vars, connection refs); Live monitor used to verify delegation." | A |

Footer on every image: *"Demo built in a personal M365 developer tenant with fictitious data."*

---

## Troubleshooting
- **Red error on `AddColumns(... Week, ...)` or `ShowColumns`:** older apps need quoted names (`"Week"`).
- **UDF errors (`HealthColor` not recognized):** turn on *User-defined functions* in Settings → Updates, then reload Studio. Fallback: paste the `Switch(...)` inline.
- **Line chart shows nothing:** the first column must be the label (`Week`); set NumberOfSeries to 2.
- **Dates off by a day:** the column was created with "Include time". Recreate it as Date only.
- **Blue delegation underline on `ClearCollect(colAllUpdates, StatusUpdates)`:** expected; the row limit is 2000. For a facility-wide rollout, aggregate in Power BI or with a scheduled flow (say so in a caption).
- **Flow B fails at Convert file:** wait about 10 seconds after Create file (add a *Delay*), or check the OneDrive folder exists.
- **Paste me any error message** and I'll give you the fix.
