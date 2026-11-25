"""Generates the PMO Project Hub canvas app screens as Power Apps YAML (.pa.yaml).

Run:  python3 build_screens.py <src-dir>
Then: pac canvas pack --sources <src-dir> --msapp PMO-Project-Hub.msapp
Control versions match the ones Power Apps Studio used in this environment.
"""
import os
import sys

LABEL = "Label@2.5.1"
BUTTON = "Classic/Button@2.2.0"
RECT = "Rectangle@2.3.0"
ICON = "Classic/Icon@2.5.0"
TEXT = "Classic/TextInput@2.3.2"
DROP = "Classic/DropDown@2.3.1"
DATE = "Classic/DatePicker@2.6.0"
TOGGLE = "Classic/Toggle@2.1.0"
SLIDER = "Classic/Slider@2.1.0"
GALLERY = "Gallery@2.15.0"
GROUP = "GroupContainer@1.5.0"
CHART = "LineChart@2.3.0"
LEGEND = "Legend@2.1.0"

HEADER_H = 64


# ---------------------------------------------------------------- YAML emitter
def fmt(v):
    v = str(v)
    if not v.startswith("="):
        v = "=" + v
    return v


def emit_props(props, ind):
    out = []
    for k, v in props.items():
        v = fmt(v)
        if "\n" in v or ": " in v or " #" in v or v.endswith(":"):
            out.append(f"{ind}{k}: |-")
            for line in v.split("\n"):
                out.append(f"{ind}  {line}")
        else:
            out.append(f"{ind}{k}: {v}")
    return out


def emit_control(c, ind):
    name, ctype, props, children, variant = c
    out = [f"{ind}- {name}:", f"{ind}    Control: {ctype}"]
    if variant:
        out.append(f"{ind}    Variant: {variant}")
    if props:
        out.append(f"{ind}    Properties:")
        out += emit_props(props, ind + "      ")
    if children:
        out.append(f"{ind}    Children:")
        for ch in children:
            out += emit_control(ch, ind + "      ")
    return out


def screen_yaml(name, props, children):
    out = ["Screens:", f"  {name}:", "    Properties:"]
    out += emit_props(props, "      ")
    out.append("    Children:")
    for c in children:
        out += emit_control(c, "      ")
    return "\n".join(out) + "\n"


def C(name, ctype, props=None, children=None, variant=None):
    return (name, ctype, props or {}, children or [], variant)


# ---------------------------------------------------------------- building blocks
def lbl(name, text, x, y, w, h, size=13, color="nfBaseDarker", bold=False, **extra):
    p = {"Text": text, "X": x, "Y": y, "Width": w, "Height": h, "Size": size, "Color": color,
         "Font": "Font.'Segoe UI'"}
    if bold:
        p["FontWeight"] = "FontWeight.Semibold"
    p.update(extra)
    return C(name, LABEL, p)


def rect(name, x, y, w, h, fill, **extra):
    p = {"X": x, "Y": y, "Width": w, "Height": h, "Fill": fill, "BorderColor": "RGBA(0,0,0,0)"}
    p.update(extra)
    return C(name, RECT, p)


def btn(name, text, x, y, w, h, onselect, primary=True, **extra):
    p = {"Text": text, "X": x, "Y": y, "Width": w, "Height": h, "OnSelect": onselect,
         "Size": 13, "FontWeight": "FontWeight.Semibold", "Font": "Font.'Segoe UI'",
         "RadiusTopLeft": 4, "RadiusTopRight": 4, "RadiusBottomLeft": 4, "RadiusBottomRight": 4,
         "FocusedBorderThickness": 3, "FocusedBorderColor": "nfBaseDarkest"}
    if primary:
        p.update({"Fill": "nfBlue", "Color": "Color.White", "HoverFill": "nfNavy", "PressedFill": "nfNavy",
                  "BorderColor": "nfBlue", "DisabledFill": "nfBaseLighter", "DisabledColor": "nfBaseMedium"})
    else:
        p.update({"Fill": "nfPage", "Color": "nfBlue", "HoverFill": "nfInfoBg", "PressedFill": "nfInfoBg",
                  "HoverColor": "nfNavy", "BorderColor": "nfBlue", "BorderThickness": 1,
                  "DisabledFill": "nfPage", "DisabledColor": "nfBaseLight"})
    p.update(extra)
    return C(name, BUTTON, p)


def txt(name, default, x, y, w, h, label, hint="", multiline=False, **extra):
    p = {"Default": default, "X": x, "Y": y, "Width": w, "Height": h, "AccessibleLabel": f'"{label}"',
         "HintText": f'"{hint}"', "Size": 13, "BorderColor": "nfBaseLight", "HoverBorderColor": "nfBlue",
         "FocusedBorderThickness": 3, "Color": "nfBaseDarkest", "Font": "Font.'Segoe UI'"}
    if multiline:
        p["Mode"] = "TextMode.MultiLine"
    p.update(extra)
    return C(name, TEXT, p)


def drop(name, items, x, y, w, h, label, default=None, **extra):
    p = {"Items": items, "X": x, "Y": y, "Width": w, "Height": h, "AccessibleLabel": f'"{label}"',
         "Size": 13, "Fill": "nfPage", "BorderColor": "nfBaseLight", "ChevronBackground": "nfPage",
         "ChevronFill": "nfBaseDarker", "Color": "nfBaseDarkest", "SelectionFill": "nfBlue",
         "Font": "Font.'Segoe UI'"}
    if default is not None:
        p["Default"] = default
    p.update(extra)
    return C(name, DROP, p)


def chip(name, health, x, y, w=104, h=28):
    return lbl(name, health, x, y, w, h, size=12, color="nfBaseDarkest", bold=True,
               Align="Align.Center", Fill=f"HealthBg({health})", BorderColor=f"HealthColor({health})",
               BorderThickness=2)


def header(p):
    """Navy header with nav buttons. p = unique prefix for the screen."""
    def nav(n, text, offset, target):
        return btn(f"{p}Nav{n}", f'"{text}"', f"Parent.Width - {offset}", 12, 120, 40,
                   f"Navigate({target}, ScreenTransition.None)",
                   primary=True, Fill=f"If(App.ActiveScreen = {target}, nfBlue, RGBA(0,0,0,0))",
                   BorderColor="RGBA(0,0,0,0)", HoverFill="nfBlue")
    return [
        rect(f"{p}HdrBar", 0, 0, "Parent.Width", HEADER_H, "nfNavy"),
        lbl(f"{p}HdrTitle", '"PMO Project Hub"', 24, 0, 300, HEADER_H, size=20, color="Color.White", bold=True),
        lbl(f"{p}HdrPMO", 'If(nfIsPMO, "PMO admin", "")', 330, 20, 100, 24, size=11, color="nfBaseDarkest",
            Fill='If(nfIsPMO, nfInfoBg, RGBA(0,0,0,0))', Align="Align.Center"),
        nav("Portfolio", "Portfolio", 560, "scrPortfolio"),
        nav("Analytics", "Analytics", 430, "scrAnalytics"),
        nav("MyWork", "My work", 300, "scrMyWork"),
        lbl(f"{p}HdrDemo", '"Demo · fictitious data"', "Parent.Width - 170", 0, 150, HEADER_H, size=11,
            color="nfAmber", Align="Align.Right"),
    ]


def card(name, x, y, w, h):
    return rect(name, x, y, w, h, "nfPage", BorderColor="nfBaseLighter", BorderThickness=1)


# ---------------------------------------------------------------- App
APP_FORMULAS = """=// ---------- Theme: VA Design System (VADS) neutrals + alert backgrounds ----------
nfBaseDarkest = ColorValue("#1b1b1b");
nfBaseDarker  = ColorValue("#3d4551");
nfBaseDark    = ColorValue("#565c65");
nfBaseMedium  = ColorValue("#71767a");
nfBaseLight   = ColorValue("#a9aeb1");
nfBaseLighter = ColorValue("#dfe1e2");
nfMuted       = ColorValue("#f0f0f0");
nfPage        = ColorValue("#ffffff");
nfInfoBg      = ColorValue("#e7f6f8");
nfErrorBg     = ColorValue("#f4e3db");
nfSuccessBg   = ColorValue("#ecf3ec");
nfWarningBg   = ColorValue("#faf3d1");
// Accents (header, buttons, chart bars)
nfNavy  = ColorValue("#112E51");
nfBlue  = ColorValue("#0071BC");
nfGreen = ColorValue("#2E8540");
nfAmber = ColorValue("#FDB81E");
nfRed   = ColorValue("#CD2026");

// ---------- User + role ----------
nfMe    = Lower(User().Email);
nfIsPMO = !IsBlank(LookUp(PMOTeam, Title = nfMe));

// ---------- Reporting calendar (weeks start Monday) ----------
nfThisWeek   = DateAdd(Today(), -(Weekday(Today(), StartOfWeek.Monday) - 1), TimeUnit.Days);
nfReportWeek = DateAdd(nfThisWeek, -7, TimeUnit.Days);

// ---------- Reusable logic (user-defined functions) ----------
HealthColor(h: Text): Color = Switch(h, "Green", nfGreen, "Yellow", nfAmber, "Red", nfRed, nfBaseDark);
HealthBg(h: Text): Color = Switch(h, "Green", nfSuccessBg, "Yellow", nfWarningBg, "Red", nfErrorBg, nfInfoBg);
// Share of the way from baseline to target (0-1); works whether lower or higher is better
MetricProgress(base: Number, target: Number, current: Number): Number =
    If(base = target, 1, Max(0, Min(1, (base - current) / (base - target))));
// Positive = late, negative = early
SlipDays(planned: DateTime, actualOrForecast: DateTime): Number = DateDiff(planned, actualOrForecast, TimeUnit.Days);
// Share (0-1) shown as a whole percent (Power Fx Text with a percent format does not scale by 100)
Pct(x: Number): Text = Text(Round(x * 100, 0)) & "%";"""

APP_ONSTART = """=Set(varTab, "Overview");
Set(varBusy, false);
ClearCollect(colPeopleRaw, ShowColumns(ActionItems, OwnerName, OwnerEmail));
Collect(colPeopleRaw, {OwnerName: User().FullName, OwnerEmail: nfMe});
ClearCollect(colPeople, Sort(GroupBy(colPeopleRaw, OwnerEmail, OwnerName, Rows), OwnerName))"""

APP_YAML = "App:\n  Properties:\n" + "\n".join(emit_props({
    "Formulas": APP_FORMULAS,
    "OnStart": APP_ONSTART,
    "StartScreen": 'Switch(Param("screen"), "update", scrUpdate, "project", scrProject, scrPortfolio)',
    "Theme": "PowerAppsTheme",
}, "    ")) + "\n"


# ---------------------------------------------------------------- scrPortfolio
def portfolio():
    kw = "(Parent.Width - 48 - 64) / 5"
    kpis = [
        ("Active projects", "Text(CountRows(colProjects))", "nfBaseDarkest"),
        ("On track (green)", 'Pct(CountIf(colProjects, CurrentHealth = "Green") / Max(1, CountRows(colProjects)))', "nfGreen"),
        ("Milestones finished on time", 'With({d: Filter(colMilestones, Status = "Done")}, Pct(CountIf(d, ActualDate <= PlannedDate) / Max(1, CountRows(d))))', "nfBaseDarkest"),
        ("Overdue actions", "Text(CountIf(colOpenActions, DueDate < Today()))", 'If(CountIf(colOpenActions, DueDate < Today()) > 0, nfRed, nfBaseDarkest)'),
        ("Missing last week's update", "Text(CountIf(colProjects, IsBlank(LastUpdateWeek) || LastUpdateWeek < nfReportWeek))", 'If(CountIf(colProjects, IsBlank(LastUpdateWeek) || LastUpdateWeek < nfReportWeek) > 0, nfRed, nfBaseDarkest)'),
    ]
    ch = header("p")
    ch += [
        lbl("lblPortTitle", '"Portfolio"', 24, 76, 400, 36, size=22, color="nfBaseDarkest", bold=True),
        lbl("lblPortSub", 'CountRows(colProjects) & " active improvement projects · as of " & Text(Today(), "mmm d, yyyy")',
            24, 110, 600, 24, color="nfBaseMedium"),
    ]
    for i, (cap, num, col) in enumerate(kpis, start=1):
        x = f"24 + {i - 1} * ({kw} + 16)"
        ch += [
            card(f"kpi{i}Box", x, 146, kw, 92),
            lbl(f"kpi{i}Num", num, f"{x} + 16", 154, f"{kw} - 32", 44, size=28, color=col, bold=True),
            lbl(f"kpi{i}Cap", f'"{cap}"', f"{x} + 16", 198, f"{kw} - 32", 30, size=12, color="nfBaseDark"),
        ]
    ch += [
        drop("drpService", 'Table({Value: "All services"}, Sort(Distinct(colProjects, Service), Value))',
             24, 254, 260, 40, "Filter by service"),
        drop("drpHealth", '["All", "Green", "Yellow", "Red"]', 300, 254, 180, 40, "Filter by health"),
        txt("txtSearch", '""', 496, 254, 320, 40, "Search project or code", hint="Search project or code"),
    ]
    items = """Sort(
    Filter(
        colProjects,
        (drpService.Selected.Value = "All services" || Service = drpService.Selected.Value) &&
        (drpHealth.Selected.Value = "All" || CurrentHealth = drpHealth.Selected.Value) &&
        (IsBlank(txtSearch.Text) || txtSearch.Text in Title || txtSearch.Text in ProjectCode)
    ),
    ProjectCode
)"""
    stale = "IsBlank(ThisItem.LastUpdateWeek) || ThisItem.LastUpdateWeek < nfReportWeek"
    tpl = [
        rect("cardBg", 0, 0, "Parent.TemplateWidth", "Parent.TemplateHeight", "nfPage",
             BorderColor="nfBaseLighter", BorderThickness=1, OnSelect="Select(Parent)"),
        rect("cardAccent", 0, 0, 6, "Parent.TemplateHeight", "HealthColor(ThisItem.CurrentHealth)"),
        lbl("cardCode", 'ThisItem.ProjectCode & " · " & ThisItem.Service', 20, 10, "Parent.TemplateWidth - 160", 22,
            size=12, color="nfBaseMedium", OnSelect="Select(Parent)"),
        lbl("cardTitle", "ThisItem.Title", 20, 32, "Parent.TemplateWidth - 160", 48, size=16, color="nfBaseDarkest",
            bold=True, OnSelect="Select(Parent)", VerticalAlign="VerticalAlign.Top"),
        chip("cardChip", "ThisItem.CurrentHealth", "Parent.TemplateWidth - 124", 14),
        lbl("cardPM", '"PM: " & ThisItem.PMName & " · " & ThisItem.Phase', 20, 80, "Parent.TemplateWidth - 40", 24,
            size=12, color="nfBaseDark", OnSelect="Select(Parent)"),
        rect("cardBarBg", 20, 110, "Parent.TemplateWidth - 40", 8, "nfBaseLighter"),
        rect("cardBar", 20, 110,
             "(Parent.TemplateWidth - 40) * MetricProgress(ThisItem.MetricBaseline, ThisItem.MetricTarget, ThisItem.MetricCurrent)",
             8, "nfBlue"),
        lbl("cardMetric", 'ThisItem.MetricName & ": " & ThisItem.MetricCurrent & " (target " & ThisItem.MetricTarget & ")"',
            20, 122, "Parent.TemplateWidth - 40", 22, size=12, color="nfBaseDarker", OnSelect="Select(Parent)"),
        lbl("cardStale",
            f'If({stale}, "No update for week of " & Text(nfReportWeek, "mmm d"), "Updated week of " & Text(ThisItem.LastUpdateWeek, "mmm d"))',
            20, 144, "Parent.TemplateWidth - 40", 22, size=12, color=f"If({stale}, nfRed, nfBaseMedium)",
            OnSelect="Select(Parent)"),
    ]
    ch.append(C("galProjects", GALLERY, {
        "Items": items, "X": 24, "Y": 306, "Width": "Parent.Width - 48", "Height": "Parent.Height - 322",
        "WrapCount": 2, "TemplateSize": 176, "TemplatePadding": 8, "BorderColor": "RGBA(0,0,0,0)",
        "AccessibleLabel": '"Active projects"',
        "OnSelect": 'Set(varProject, ThisItem); Set(varTab, "Overview"); Navigate(scrProject, ScreenTransition.Fade)',
    }, tpl, variant="Vertical"))
    props = {"Fill": "nfMuted", "OnVisible": """Concurrent(
    ClearCollect(colProjects, Filter(Projects, IsActive = true)),
    ClearCollect(colMilestones, Milestones),
    ClearCollect(colOpenActions, Filter(ActionItems, Status = "Open"))
)"""}
    return screen_yaml("scrPortfolio", props, ch)


# ---------------------------------------------------------------- scrProject
def project():
    ch = header("j")
    ch += [
        btn("btnBackPortfolio", '"← Portfolio"', 24, 76, 140, 36, "Navigate(scrPortfolio, ScreenTransition.Fade)", primary=False),
        lbl("lblProjCode", 'varProject.ProjectCode & " · " & varProject.Service & " · " & varProject.ScorecardDomain',
            24, 118, "Parent.Width - 420", 22, size=12, color="nfBaseMedium"),
        lbl("lblProjTitle", "varProject.Title", 24, 138, "Parent.Width - 420", 36, size=22, color="nfBaseDarkest", bold=True),
        lbl("lblProjMeta",
            '"PM: " & varProject.PMName & " · Sponsor: " & varProject.Sponsor & " · Phase: " & varProject.Phase & " · " & Text(varProject.StartDate, "mmm d") & " – " & Text(varProject.TargetEndDate, "mmm d, yyyy")',
            24, 174, "Parent.Width - 420", 24, size=12, color="nfBaseDark"),
        chip("chipProjHealth", "varProject.CurrentHealth", "Parent.Width - 360", 112, 120, 32),
        btn("btnPostUpdate", '"Post weekly update"', "Parent.Width - 224", 108, 200, 40, "Navigate(scrUpdate, ScreenTransition.Fade)"),
        btn("btnStatusReport", 'If(varBusy, "Building report…", "Status report (PDF)")', "Parent.Width - 224", 154, 200, 40,
            """Set(varBusy, true);
Set(varReport, PMOStatusReport.Run(varProject.ID));
Set(varBusy, false);
If(IsBlank(varReport.reporturl),
   Notify("Couldn't build the report. Try again in a minute.", NotificationType.Error),
   Notify("Report saved to the team's SharePoint (General folder).", NotificationType.Success); Launch(varReport.reporturl))""",
            primary=False, DisplayMode="If(varBusy, DisplayMode.Disabled, DisplayMode.Edit)"),
        C("galTabs", GALLERY, {
            "Items": '["Overview", "Milestones", "Status history", "Risks", "Actions"]',
            "X": 24, "Y": 206, "Width": 800, "Height": 48, "TemplateSize": 150, "TemplatePadding": 0,
            "BorderColor": "RGBA(0,0,0,0)", "AccessibleLabel": '"Project tabs"',
            "OnSelect": "Set(varTab, ThisItem.Value)",
        }, [
            lbl("tabLbl", "ThisItem.Value", 0, 0, "Parent.TemplateWidth", 42, size=14,
                color='If(ThisItem.Value = varTab, nfBlue, nfBaseDark)', Align="Align.Center",
                FontWeight='If(ThisItem.Value = varTab, FontWeight.Bold, FontWeight.Normal)', OnSelect="Select(Parent)"),
            rect("tabLine", 12, 42, "Parent.TemplateWidth - 24", 4, "nfBlue", Visible="ThisItem.Value = varTab"),
        ], variant="Horizontal"),
        rect("tabDivider", 24, 254, "Parent.Width - 48", 1, "nfBaseLighter"),
    ]
    box = {"X": 24, "Y": 264, "Width": "Parent.Width - 48", "Height": "Parent.Height - 280", "Fill": "nfPage",
           "BorderColor": "nfBaseLighter", "BorderThickness": 1}

    # Overview
    half = "Parent.Width / 2"
    ov = [
        lbl("ovObjHead", '"Objective"', 16, 12, f"{half} - 32", 24, size=13, color="nfBaseDarkest", bold=True),
        lbl("ovObj", "varProject.Objective", 16, 36, f"{half} - 32", 64, size=13, color="nfBaseDarker",
            VerticalAlign="VerticalAlign.Top"),
        lbl("ovMetricHead", '"Target metric: " & varProject.MetricName', 16, 108, f"{half} - 32", 24, size=13,
            color="nfBaseDarkest", bold=True),
        lbl("ovMetricTxt",
            '"Baseline " & varProject.MetricBaseline & "  →  now " & varProject.MetricCurrent & "  →  target " & varProject.MetricTarget',
            16, 132, f"{half} - 32", 24, size=13),
        lbl("ovProg",
            'Pct(MetricProgress(varProject.MetricBaseline, varProject.MetricTarget, varProject.MetricCurrent)) & " of the way to target"',
            16, 158, f"{half} - 32", 30, size=16, color="nfBlue", bold=True),
        rect("ovBarBg", 16, 192, f"{half} - 48", 10, "nfBaseLighter"),
        rect("ovBar", 16, 192,
             f"({half} - 48) * MetricProgress(varProject.MetricBaseline, varProject.MetricTarget, varProject.MetricCurrent)",
             10, "nfBlue"),
        lbl("ovHealthHead", '"Weekly health (hover for blockers)"', 16, 220, f"{half} - 32", 24, size=13,
            color="nfBaseDarkest", bold=True),
        C("galHealth", GALLERY, {
            "Items": "colPU", "X": 16, "Y": 246, "Width": f"{half} - 32", "Height": 70, "TemplateSize": 52,
            "TemplatePadding": 2, "BorderColor": "RGBA(0,0,0,0)", "AccessibleLabel": '"Weekly health history"',
        }, [
            lbl("hsCell", '""', 6, 4, 36, 36, Fill="HealthColor(ThisItem.Health)",
                Tooltip='Text(ThisItem.WeekOf, "mmm d") & ": " & ThisItem.Health & If(IsBlank(ThisItem.Blockers), "", " – " & ThisItem.Blockers)'),
            lbl("hsWeek", 'Text(ThisItem.WeekOf, "m/d")', 0, 42, 48, 20, size=10, color="nfBaseMedium", Align="Align.Center"),
        ], variant="Horizontal"),
        lbl("ovChartTitle", 'varProject.MetricName & " by week vs. target"', half, 12, f"{half} - 64", 24, size=13,
            color="nfBaseDarkest", bold=True),
        C("chtMetric", CHART, {
            "Items": "ShowColumns(AddColumns(colPU, Week, Text(WeekOf, \"mmm d\"), Actual, MetricValue, Target, varProject.MetricTarget), Week, Actual, Target)",
            "Items.Labels": "Week", "Items.Series1": "Actual", "Items.Series2": "Target",
            "NumberOfSeries": 2, "X": half, "Y": 40, "Width": f"{half} - 64", "Height": "Parent.Height - 110",
            "ItemColorSet": "[nfBlue, nfBaseLight]", "Color": "nfBaseDarker", "Size": 11, "Font": "Font.'Segoe UI'",
        }),
        C("lgdMetric", LEGEND, {
            "Items": "chtMetric.SeriesLabels", "Items.Value": "Value", "ItemColorSet": "chtMetric.ItemColorSet",
            "X": half, "Y": "Parent.Height - 64", "Width": 360, "Height": 48, "Color": "nfBaseDarker",
            "Font": "Font.'Segoe UI'",
        }),
    ]
    # Milestones
    ms_slip = "SlipDays(ThisItem.PlannedDate, Coalesce(ThisItem.ActualDate, ThisItem.ForecastDate))"
    track = "(Parent.TemplateWidth - 720)"
    ms = [
        lbl("msHead", '"Milestones: planned vs. forecast or actual, with schedule variance"', 16, 8, 700, 28,
            size=13, color="nfBaseDarkest", bold=True),
        C("galMilestones", GALLERY, {
            "Items": "colPM", "X": 16, "Y": 40, "Width": "Parent.Width - 32", "Height": "Parent.Height - 56",
            "TemplateSize": 60, "TemplatePadding": 0, "BorderColor": "RGBA(0,0,0,0)",
            "AccessibleLabel": '"Milestones"',
        }, [
            lbl("msName", 'ThisItem.Sequence & ". " & ThisItem.Title', 8, 6, 330, 26, size=14, color="nfBaseDarkest", bold=True),
            lbl("msDates",
                '"Planned " & Text(ThisItem.PlannedDate, "mmm d") & " · " & If(IsBlank(ThisItem.ActualDate), "Forecast " & Text(ThisItem.ForecastDate, "mmm d"), "Done " & Text(ThisItem.ActualDate, "mmm d"))',
                8, 30, 330, 24, size=12, color="nfBaseDark"),
            lbl("msStatus", "ThisItem.Status", 350, 16, 110, 28, size=12, color="nfBaseDarkest", Align="Align.Center",
                Fill='If(ThisItem.Status = "Done", nfSuccessBg, ThisItem.Status = "In progress", nfInfoBg, nfMuted)'),
            lbl("msVar",
                f'With({{v: {ms_slip}}}, If(v > 0, "+" & v & " days late", v < 0, Abs(v) & " days early", "On time"))',
                476, 16, 200, 28, size=13, bold=True, color=f"If({ms_slip} > 0, nfRed, nfGreen)"),
            rect("msTrack", 700, 29, track, 2, "nfBaseLighter"),
            rect("msDot",
                 f"700 + {track} * DateDiff(varProject.StartDate, ThisItem.PlannedDate) / Max(1, DateDiff(varProject.StartDate, varProject.TargetEndDate)) - 7",
                 23, 14, 14, f'If(ThisItem.Status = "Done", nfGreen, {ms_slip} > 0, nfRed, nfBlue)'),
            rect("msSep", 0, 59, "Parent.TemplateWidth", 1, "nfBaseLighter"),
        ], variant="Vertical"),
    ]
    # Status history
    col3 = "(Parent.TemplateWidth - 48) / 3"
    hist = [
        C("galHistory", GALLERY, {
            "Items": "Sort(colPU, WeekOf, SortOrder.Descending)", "X": 16, "Y": 12, "Width": "Parent.Width - 32",
            "Height": "Parent.Height - 24", "TemplateSize": 128, "TemplatePadding": 0,
            "BorderColor": "RGBA(0,0,0,0)", "AccessibleLabel": '"Status history"',
        }, [
            lbl("hWeek", '"Week of " & Text(ThisItem.WeekOf, "mmm d, yyyy")', 8, 8, 260, 28, size=14,
                color="nfBaseDarkest", bold=True),
            chip("hChip", "ThisItem.Health", 276, 8, 96, 28),
            lbl("hPct", 'ThisItem.PercentComplete & "% complete · " & varProject.MetricName & ": " & ThisItem.MetricValue',
                388, 8, "Parent.TemplateWidth - 400", 28, size=12, color="nfBaseDark"),
            lbl("hAcc", '"Done: " & ThisItem.Accomplishments', 8, 42, col3, 78, size=12,
                VerticalAlign="VerticalAlign.Top"),
            lbl("hNext", '"Next: " & ThisItem.NextSteps', f"16 + {col3}", 42, col3, 78, size=12,
                VerticalAlign="VerticalAlign.Top"),
            lbl("hBlk", '"Blockers: " & If(IsBlank(ThisItem.Blockers), "None", ThisItem.Blockers)', f"24 + 2 * {col3}",
                42, col3, 78, size=12, VerticalAlign="VerticalAlign.Top",
                color="If(IsBlank(ThisItem.Blockers), nfBaseMedium, nfRed)"),
            rect("hSep", 0, 127, "Parent.TemplateWidth", 1, "nfBaseLighter"),
        ], variant="Vertical"),
    ]
    # Risks
    rk = [
        lbl("rkHeatTitle", '"Risk heat map (open risks)"', 16, 8, 320, 28, size=13, color="nfBaseDarkest", bold=True),
        lbl("rkAxisL", '"↑ Likelihood (5 top)"', 16, 36, 300, 20, size=11, color="nfBaseMedium"),
        C("galHeat", GALLERY, {
            "Items": "ForAll(Sequence(25) As s, {L: 5 - RoundDown((s.Value - 1) / 5, 0), I: Mod(s.Value - 1, 5) + 1})",
            "X": 16, "Y": 58, "Width": 300, "Height": 300, "WrapCount": 5, "TemplateSize": 58, "TemplatePadding": 2,
            "BorderColor": "RGBA(0,0,0,0)", "AccessibleLabel": '"Risk heat map, likelihood by impact"',
        }, [
            lbl("hmCell",
                'With({n: CountIf(colPR, Likelihood = ThisItem.L && Impact = ThisItem.I && Status <> "Closed")}, If(n = 0, "", Text(n)))',
                0, 0, "Parent.TemplateWidth", "Parent.TemplateHeight", size=18, color="nfBaseDarkest", bold=True,
                Align="Align.Center",
                Fill='With({score: ThisItem.L * ThisItem.I}, ColorFade(If(score >= 15, nfRed, score >= 8, nfAmber, nfGreen), 0.55))',
                Tooltip='"Likelihood " & ThisItem.L & " × Impact " & ThisItem.I'),
        ], variant="Vertical"),
        lbl("rkAxisI", '"Impact → (5 right)"', 16, 360, 300, 20, size=11, color="nfBaseMedium"),
        lbl("rkListTitle", '"Risks, highest score first"', 340, 8, 400, 28, size=13, color="nfBaseDarkest", bold=True),
        C("galRisks", GALLERY, {
            "Items": "Sort(colPR, RiskScore, SortOrder.Descending)", "X": 340, "Y": 40,
            "Width": "Parent.Width - 356", "Height": "Parent.Height - 180", "TemplateSize": 74, "TemplatePadding": 0,
            "BorderColor": "RGBA(0,0,0,0)", "AccessibleLabel": '"Risk list"',
        }, [
            lbl("rkScore", "ThisItem.RiskScore", 4, 10, 48, 48, size=18, bold=True, color="nfBaseDarkest", Align="Align.Center",
                Fill="If(ThisItem.RiskScore >= 15, nfErrorBg, ThisItem.RiskScore >= 8, nfWarningBg, nfSuccessBg)"),
            lbl("rkTitle", "ThisItem.Title", 64, 6, "Parent.TemplateWidth - 76", 24, size=14, color="nfBaseDarkest", bold=True),
            lbl("rkMeta", '"L" & ThisItem.Likelihood & " × I" & ThisItem.Impact & " · " & ThisItem.Status & " · Owner: " & ThisItem.Owner',
                64, 28, "Parent.TemplateWidth - 76", 20, size=12, color="nfBaseDark"),
            lbl("rkMit", '"Mitigation: " & ThisItem.Mitigation', 64, 48, "Parent.TemplateWidth - 76", 22, size=12),
            rect("rkSep", 0, 73, "Parent.TemplateWidth", 1, "nfBaseLighter"),
        ], variant="Vertical"),
        lbl("rkAddHead", '"Add a risk"', 340, "Parent.Height - 132", 200, 24, size=13, color="nfBaseDarkest", bold=True),
        txt("txtRiskTitle", '""', 340, "Parent.Height - 104", 360, 40, "Risk title", hint="Describe the risk"),
        lbl("lblLik", '"Likelihood " & sldLikelihood.Value', 716, "Parent.Height - 110", 140, 20, size=11),
        C("sldLikelihood", SLIDER, {"Min": 1, "Max": 5, "Default": 3, "X": 716, "Y": "Parent.Height - 90",
                                    "Width": 140, "Height": 32, "AccessibleLabel": '"Likelihood, 1 to 5"',
                                    "ValueFill": "nfBlue", "RailFill": "nfBaseLighter"}),
        lbl("lblImp", '"Impact " & sldImpact.Value', 872, "Parent.Height - 110", 140, 20, size=11),
        C("sldImpact", SLIDER, {"Min": 1, "Max": 5, "Default": 3, "X": 872, "Y": "Parent.Height - 90",
                                "Width": 140, "Height": 32, "AccessibleLabel": '"Impact, 1 to 5"',
                                "ValueFill": "nfBlue", "RailFill": "nfBaseLighter"}),
        txt("txtMitigation", '""', 340, "Parent.Height - 56", 672, 40, "Mitigation", hint="How will you reduce it?"),
        btn("btnAddRisk", '"Add risk"', 1028, "Parent.Height - 56", 140, 40, """Patch(Risks, Defaults(Risks), {
    Title: txtRiskTitle.Text, ProjectID: varProject.ID,
    Likelihood: sldLikelihood.Value, Impact: sldImpact.Value,
    RiskScore: sldLikelihood.Value * sldImpact.Value,
    Mitigation: txtMitigation.Text, Owner: User().FullName, Status: "Open"
});
If(IsEmpty(Errors(Risks)),
   ClearCollect(colPR, Filter(Risks, ProjectID = varProject.ID)); Reset(txtRiskTitle); Reset(txtMitigation);
   Notify("Risk added", NotificationType.Success),
   Notify("Couldn't save: " & First(Errors(Risks)).Message, NotificationType.Error))""",
            DisplayMode="If(IsBlank(Trim(txtRiskTitle.Text)), DisplayMode.Disabled, DisplayMode.Edit)"),
    ]
    # Actions
    ac = [
        lbl("acHead", '"Action items (toggle to mark done; toggle again to undo)"', 16, 8, 500, 28, size=13, color="nfBaseDarkest", bold=True),
        C("galActions", GALLERY, {
            "Items": "Sort(colPA, DueDate, SortOrder.Ascending)", "X": 16, "Y": 40, "Width": "Parent.Width - 32",
            "Height": "Parent.Height - 160", "TemplateSize": 56, "TemplatePadding": 0, "BorderColor": "RGBA(0,0,0,0)",
            "AccessibleLabel": '"Action items"',
        }, [
            C("tglDone", TOGGLE, {
                "Default": 'ThisItem.Status = "Done"', "X": 4, "Y": 10, "Width": 140, "Height": 36,
                "TrueText": '"Done"', "FalseText": '"Open"', "TrueFill": "nfGreen", "FalseFill": "nfBaseLight",
                "AccessibleLabel": '"Mark " & ThisItem.Title & " done"',
                "OnCheck": 'Patch(ActionItems, LookUp(ActionItems, ID = ThisItem.ID), {Status: "Done", CompletedOn: Today()}); ClearCollect(colPA, Filter(ActionItems, ProjectID = varProject.ID)); Notify("Marked done. Toggle it back to reopen.", NotificationType.Success)',
                "OnUncheck": 'Patch(ActionItems, LookUp(ActionItems, ID = ThisItem.ID), {Status: "Open", CompletedOn: Blank()}); ClearCollect(colPA, Filter(ActionItems, ProjectID = varProject.ID)); Notify("Reopened.", NotificationType.Information)',
            }),
            lbl("acTitle", "ThisItem.Title", 156, 4, "Parent.TemplateWidth - 400", 26, size=14, color="nfBaseDarkest", bold=True),
            lbl("acOwner", '"Owner: " & ThisItem.OwnerName', 156, 28, "Parent.TemplateWidth - 400", 22, size=12, color="nfBaseDark"),
            lbl("acDue", 'If(ThisItem.Status = "Done", "Done " & Text(ThisItem.CompletedOn, "mmm d"), "Due " & Text(ThisItem.DueDate, "mmm d"))',
                "Parent.TemplateWidth - 260", 14, 240, 28, size=13, bold=True, Align="Align.Right",
                color='If(ThisItem.Status = "Open" && ThisItem.DueDate < Today(), nfRed, nfBaseDark)'),
            rect("acSep", 0, 55, "Parent.TemplateWidth", 1, "nfBaseLighter"),
        ], variant="Vertical"),
        lbl("acAddHead", '"Assign an action"', 16, "Parent.Height - 112", 200, 24, size=13, color="nfBaseDarkest", bold=True),
        txt("txtActionTitle", '""', 16, "Parent.Height - 84", 420, 40, "Action title", hint="What needs to happen?"),
        drop("drpActionOwner", "colPeople", 452, "Parent.Height - 84", 240, 40, "Action owner",
             default="User().FullName", **{"Items.Value": "OwnerName"}),
        C("dpActionDue", DATE, {"DefaultDate": "DateAdd(Today(), 7, TimeUnit.Days)", "X": 708, "Y": "Parent.Height - 84",
                                "Width": 200, "Height": 40, "AccessibleLabel": '"Due date"', "Size": 13,
                                "BorderColor": "nfBaseLight", "IconBackground": "nfBlue"}),
        btn("btnAddAction", '"Add action"', 924, "Parent.Height - 84", 140, 40, """Patch(ActionItems, Defaults(ActionItems), {
    Title: txtActionTitle.Text, ProjectID: varProject.ID,
    OwnerName: drpActionOwner.Selected.OwnerName, OwnerEmail: Lower(drpActionOwner.Selected.OwnerEmail),
    DueDate: dpActionDue.SelectedDate, Status: "Open"
});
If(IsEmpty(Errors(ActionItems)),
   ClearCollect(colPA, Filter(ActionItems, ProjectID = varProject.ID)); Reset(txtActionTitle);
   Notify("Action assigned to " & drpActionOwner.Selected.OwnerName, NotificationType.Success),
   Notify("Couldn't save: " & First(Errors(ActionItems)).Message, NotificationType.Error))""",
            DisplayMode="If(IsBlank(Trim(txtActionTitle.Text)) || IsBlank(dpActionDue.SelectedDate), DisplayMode.Disabled, DisplayMode.Edit)"),
    ]
    for nm, tab, kids in [("conOverview", "Overview", ov), ("conMilestones", "Milestones", ms),
                          ("conHistory", "Status history", hist), ("conRisks", "Risks", rk), ("conActions", "Actions", ac)]:
        p = dict(box)
        p["Visible"] = f'varTab = "{tab}"'
        ch.append(C(nm, GROUP, p, kids, variant="ManualLayout"))
    props = {"Fill": "nfMuted", "OnVisible": """If(IsBlank(varProject) && !IsBlank(Param("projectId")),
   Set(varProject, LookUp(Projects, ID = Value(Param("projectId")))));
Concurrent(
    ClearCollect(colPM, Sort(Filter(Milestones, ProjectID = varProject.ID), Sequence)),
    ClearCollect(colPU, Sort(Filter(StatusUpdates, ProjectID = varProject.ID), WeekOf, SortOrder.Ascending)),
    ClearCollect(colPR, Filter(Risks, ProjectID = varProject.ID)),
    ClearCollect(colPA, Filter(ActionItems, ProjectID = varProject.ID))
)"""}
    return screen_yaml("scrProject", props, ch)


# ---------------------------------------------------------------- scrUpdate
def update():
    rx = "Parent.Width / 2 + 12"
    rw = "Parent.Width / 2 - 36"
    lw = "Parent.Width / 2 - 48"
    exists = 'LookUp(colPU, Text(WeekOf, "yyyy-mm-dd") = Text(dpWeek.SelectedDate, "yyyy-mm-dd"))'
    ch = header("u")
    ch += [
        btn("btnUpdBack", '"← Project"', 24, 76, 130, 36, "Navigate(scrProject, ScreenTransition.Fade)", primary=False),
        lbl("lblFor", '"Weekly update · " & varProject.ProjectCode & " " & varProject.Title', 24, 118, "Parent.Width - 48", 34,
            size=20, color="nfBaseDarkest", bold=True),
        lbl("lblUpdHint", '"Last week\'s values are filled in. Change only what moved; takes about 2 minutes."', 24, 152,
            "Parent.Width - 48", 24, size=12, color="nfBaseMedium"),
        card("updCard", 24, 184, "Parent.Width - 48", "Parent.Height - 200"),
        lbl("lblWeek", '"Week of (Monday)"', 40, 196, lw, 22, size=13, bold=True),
        C("dpWeek", DATE, {"DefaultDate": "nfReportWeek", "X": 40, "Y": 220, "Width": 240, "Height": 40,
                           "AccessibleLabel": '"Week of (Monday)"', "Size": 13, "BorderColor": "nfBaseLight",
                           "IconBackground": "nfBlue"}),
        lbl("lblExisting", '"An update already exists for this week; saving will replace it."', 40, 264, lw, 28,
            size=12, color="nfBaseDarkest", Fill="nfWarningBg", PaddingLeft=8, Visible=f"!IsBlank({exists})"),
        lbl("lblHealth", '"Overall health"', 40, 300, lw, 22, size=13, bold=True),
        drop("drpUpdHealth", '["Green", "Yellow", "Red"]', 40, 324, 240, 40, "Overall health",
             default='Coalesce(varLast.Health, "Green")'),
        chip("chipUpdHealth", "drpUpdHealth.Selected.Value", 296, 330, 104, 28),
        lbl("lblPct", '"Percent complete: " & sldPercent.Value & "%"', 40, 376, lw, 22, size=13, bold=True),
        C("sldPercent", SLIDER, {"Min": 0, "Max": 100, "Default": "Coalesce(varLast.PercentComplete, 0)", "X": 40,
                                 "Y": 400, "Width": 400, "Height": 36, "AccessibleLabel": '"Percent complete"',
                                 "ValueFill": "nfBlue", "RailFill": "nfBaseLighter"}),
        lbl("lblMetric", 'varProject.MetricName & " this week (target " & varProject.MetricTarget & ")"', 40, 448, lw, 22,
            size=13, bold=True),
        txt("txtMetric", "Coalesce(varLast.MetricValue, varProject.MetricBaseline)", 40, 472, 240, 40,
            "Metric value this week", Format="TextFormat.Number"),
        lbl("lblAcc", '"Accomplishments (required)"', rx, 196, rw, 22, size=13, bold=True),
        txt("txtAcc", '""', rx, 220, rw, 110, "Accomplishments", hint="What got done this week?", multiline=True),
        lbl("lblNext", '"Next steps"', rx, 340, rw, 22, size=13, bold=True),
        txt("txtNext", 'Coalesce(varLast.NextSteps, "")', rx, 364, rw, 90, "Next steps", multiline=True),
        lbl("lblBlockers", '"Blockers (required if Yellow or Red)"', rx, 464, rw, 22, size=13, bold=True,
            color='If(drpUpdHealth.Selected.Value <> "Green" && Len(Trim(txtBlockers.Text)) < 5, nfRed, nfBaseDarker)'),
        txt("txtBlockers", '""', rx, 488, rw, 90, "Blockers", hint="What is in the way, and what help do you need?",
            multiline=True),
        lbl("lblReq", 'If(btnSubmitUpdate.DisplayMode = DisplayMode.Disabled, "To submit: add accomplishments and a metric value, and describe blockers if health is not Green.", "")',
            40, "Parent.Height - 76", "Parent.Width - 400", 40, size=12, color="nfBaseDark"),
        btn("btnCancelUpdate", '"Cancel"', "Parent.Width - 340", "Parent.Height - 80", 130, 44,
            "Navigate(scrProject, ScreenTransition.Fade)", primary=False),
        btn("btnSubmitUpdate", '"Submit update"', "Parent.Width - 196", "Parent.Height - 80", 160, 44, f"""With(
    {{wExisting: {exists}}},
    Patch(
        StatusUpdates,
        If(IsBlank(wExisting), Defaults(StatusUpdates), wExisting),
        {{
            Title: varProject.ProjectCode & " week of " & Text(dpWeek.SelectedDate, "m/d/yyyy"),
            ProjectID: varProject.ID, WeekOf: dpWeek.SelectedDate,
            Health: drpUpdHealth.Selected.Value, PercentComplete: sldPercent.Value,
            MetricValue: Value(txtMetric.Text),
            Accomplishments: txtAcc.Text, NextSteps: txtNext.Text, Blockers: txtBlockers.Text,
            SubmittedBy: User().FullName
        }}
    )
);
If(
    IsEmpty(Errors(StatusUpdates)),
    If(IsBlank(varProject.LastUpdateWeek) || dpWeek.SelectedDate >= varProject.LastUpdateWeek,
       Patch(Projects, LookUp(Projects, ID = varProject.ID), {{
           CurrentHealth: drpUpdHealth.Selected.Value, PercentComplete: sldPercent.Value,
           MetricCurrent: Value(txtMetric.Text), LastUpdateWeek: dpWeek.SelectedDate }}));
    Set(varProject, LookUp(Projects, ID = varProject.ID));
    Reset(txtAcc); Reset(txtBlockers);
    Notify("Update saved. Thank you!", NotificationType.Success);
    Navigate(scrProject, ScreenTransition.Fade),
    Notify("Couldn't save: " & First(Errors(StatusUpdates)).Message, NotificationType.Error)
)""", DisplayMode="""If(
    IsBlank(dpWeek.SelectedDate) || IsBlank(txtMetric.Text) || IsBlank(Trim(txtAcc.Text)) ||
    (drpUpdHealth.Selected.Value <> "Green" && Len(Trim(txtBlockers.Text)) < 5),
    DisplayMode.Disabled, DisplayMode.Edit
)"""),
    ]
    props = {"Fill": "nfMuted", "OnVisible": """If(IsBlank(varProject) && !IsBlank(Param("projectId")),
   Set(varProject, LookUp(Projects, ID = Value(Param("projectId")))));
ClearCollect(colPU, Sort(Filter(StatusUpdates, ProjectID = varProject.ID), WeekOf, SortOrder.Ascending));
Set(varLast, Last(colPU));
Reset(drpUpdHealth); Reset(sldPercent); Reset(txtMetric); Reset(txtNext)"""}
    return screen_yaml("scrUpdate", props, ch)


# ---------------------------------------------------------------- scrAnalytics
def analytics():
    pw = "(Parent.Width - 64) / 2"
    ph = "(Parent.Height - 140 - 32) / 2"
    x2 = f"40 + {pw}"
    y2 = f"140 + {ph} + 16"
    ch = header("a")
    ch += [
        lbl("lblInsight", """CountIf(colProjects, CurrentHealth = "Green") & " of " & CountRows(colProjects) & " active projects are on track. " &
"Furthest behind: " & First(Sort(colSlip, Slip, SortOrder.Descending)).ProjectCode &
" (+" & First(Sort(colSlip, Slip, SortOrder.Descending)).Slip & " days). " &
CountRows(Filter(colAllRisks, RiskScore >= 15)) & " open high risks." """.strip(),
            24, 76, "Parent.Width - 48", 52, size=17, color="nfBaseDarkest", bold=True, Fill="nfInfoBg", PaddingLeft=16),
        # A: health trend
        card("pnlTrend", 24, 140, pw, ph),
        lbl("lblTrendTitle", '"Portfolio health, last " & CountRows(colTrend) & " weeks"', 40, 148, f"{pw} - 32", 26,
            size=14, color="nfBaseDarkest", bold=True),
        lbl("lblTrendKey", '"Stacked: green (bottom), yellow, red = projects reporting each week"', 40, 172, f"{pw} - 32",
            20, size=11, color="nfBaseMedium"),
        C("galTrend", GALLERY, {
            "Items": "colTrend", "X": 40, "Y": 196, "Width": f"{pw} - 32", "Height": f"{ph} - 64", "TemplateSize": 64,
            "TemplatePadding": 0, "BorderColor": "RGBA(0,0,0,0)", "AccessibleLabel": '"Weekly portfolio health trend"',
        }, [
            rect("trG", 12, "Parent.TemplateHeight - 24 - Self.Height", 40,
                 "(Parent.TemplateHeight - 44) * ThisItem.G / Max(1, varTrendMax)", "nfGreen"),
            rect("trY", 12, "trG.Y - Self.Height", 40, "(Parent.TemplateHeight - 44) * ThisItem.Y / Max(1, varTrendMax)", "nfAmber"),
            rect("trR", 12, "trY.Y - Self.Height", 40, "(Parent.TemplateHeight - 44) * ThisItem.R / Max(1, varTrendMax)", "nfRed"),
            lbl("trWeek", "ThisItem.Week", 0, "Parent.TemplateHeight - 22", 64, 20, size=10, color="nfBaseMedium",
                Align="Align.Center"),
        ], variant="Horizontal"),
        # B: progress to target
        card("pnlProgress", x2, 140, pw, ph),
        lbl("lblProgTitle", '"Progress to target metric"', f"{x2} + 16", 148, f"{pw} - 32", 26, size=14,
            color="nfBaseDarkest", bold=True),
        C("galProgress", GALLERY, {
            "Items": "Sort(colSlip, Progress, SortOrder.Descending)", "X": f"{x2} + 16", "Y": 178,
            "Width": f"{pw} - 32", "Height": f"{ph} - 46", "TemplateSize": 30, "TemplatePadding": 0,
            "BorderColor": "RGBA(0,0,0,0)", "AccessibleLabel": '"Progress to target by project"',
        }, [
            lbl("pgCode", "ThisItem.ProjectCode", 0, 2, 80, 26, size=12, bold=True),
            rect("pgBg", 84, 10, "Parent.TemplateWidth - 150", 10, "nfBaseLighter"),
            rect("pgBar", 84, 10, "(Parent.TemplateWidth - 150) * ThisItem.Progress", 10, "HealthColor(ThisItem.CurrentHealth)"),
            lbl("pgPct", 'Pct(ThisItem.Progress)', "Parent.TemplateWidth - 60", 2, 60, 26, size=12, Align="Align.Right"),
        ], variant="Vertical"),
        # C: schedule slip
        card("pnlSlip", 24, y2, pw, ph),
        lbl("lblSlipTitle", '"Schedule slip (worst milestone per project)"', 40, f"{y2} + 8", f"{pw} - 32", 26,
            size=14, color="nfBaseDarkest", bold=True),
        C("galSlip", GALLERY, {
            "Items": "Sort(colSlip, Slip, SortOrder.Descending)", "X": 40, "Y": f"{y2} + 38", "Width": f"{pw} - 32",
            "Height": f"{ph} - 46", "TemplateSize": 30, "TemplatePadding": 0, "BorderColor": "RGBA(0,0,0,0)",
            "AccessibleLabel": '"Schedule slip by project"',
        }, [
            lbl("slCode", "ThisItem.ProjectCode", 0, 2, 80, 26, size=12, bold=True),
            rect("slBar", 84, 9, "Min(Parent.TemplateWidth - 220, 8 * Max(0, ThisItem.Slip))", 12,
                 "If(ThisItem.Slip > 7, nfRed, ThisItem.Slip > 0, nfAmber, nfGreen)"),
            lbl("slTxt", 'If(ThisItem.Slip > 0, "+" & ThisItem.Slip & " days", "On schedule")',
                "92 + Min(Parent.TemplateWidth - 220, 8 * Max(0, ThisItem.Slip))", 2, 120, 26, size=12),
        ], variant="Vertical"),
        # D: Gantt
        card("pnlGantt", x2, y2, pw, ph),
        lbl("lblGanttTitle", '"Portfolio timeline (dark line = today)"', f"{x2} + 16", f"{y2} + 8", f"{pw} - 32", 26,
            size=14, color="nfBaseDarkest", bold=True),
        C("galGantt", GALLERY, {
            "Items": "Sort(colProjects, StartDate)", "X": f"{x2} + 16", "Y": f"{y2} + 38", "Width": f"{pw} - 32",
            "Height": f"{ph} - 46", "TemplateSize": 30, "TemplatePadding": 0, "BorderColor": "RGBA(0,0,0,0)",
            "AccessibleLabel": '"Portfolio timeline"',
        }, [
            lbl("gnCode", "ThisItem.ProjectCode", 0, 2, 90, 26, size=12, bold=True),
            rect("gnBar",
                 "100 + (Parent.TemplateWidth - 120) * DateDiff(varGStart, ThisItem.StartDate) / Max(1, DateDiff(varGStart, varGEnd))",
                 7,
                 "(Parent.TemplateWidth - 120) * DateDiff(ThisItem.StartDate, ThisItem.TargetEndDate) / Max(1, DateDiff(varGStart, varGEnd))",
                 16, "ColorFade(HealthColor(ThisItem.CurrentHealth), 0.3)"),
        ], variant="Vertical"),
        rect("gnToday",
             "galGantt.X + 100 + (galGantt.Width - 120) * DateDiff(varGStart, Today()) / Max(1, DateDiff(varGStart, varGEnd))",
             "galGantt.Y", 2, "galGantt.Height", "nfNavy"),
    ]
    props = {"Fill": "nfMuted", "OnVisible": """ClearCollect(colAllUpdates, StatusUpdates);
ClearCollect(colAllRisks, Filter(Risks, Status = "Open" || Status = "Mitigated"));
ClearCollect(colProjects, Filter(Projects, IsActive = true));
ClearCollect(colMilestones, Milestones);
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
ClearCollect(
    colSlip,
    AddColumns(
        colProjects As pr,
        Slip, Coalesce(Max(Filter(colMilestones, ProjectID = pr.ID), SlipDays(PlannedDate, Coalesce(ActualDate, ForecastDate))), 0),
        Progress, MetricProgress(pr.MetricBaseline, pr.MetricTarget, pr.MetricCurrent)
    )
);
Set(varGStart, Min(colProjects, StartDate));
Set(varGEnd, Max(colProjects, TargetEndDate))"""}
    return screen_yaml("scrAnalytics", props, ch)


# ---------------------------------------------------------------- scrMyWork
def mywork():
    half = "(Parent.Width - 64) / 2"
    stale = "IsBlank(ThisItem.LastUpdateWeek) || ThisItem.LastUpdateWeek < nfReportWeek"
    ch = header("m")
    ch += [
        lbl("lblMyTitle", '"My work"', 24, 76, 400, 36, size=22, color="nfBaseDarkest", bold=True),
        lbl("lblMySub", '"Projects you manage and actions assigned to you, " & User().FullName', 24, 110, 700, 24,
            color="nfBaseMedium"),
        card("pnlMyProj", 24, 144, half, "Parent.Height - 160"),
        lbl("lblMyProjHead", '"My projects"', 40, 152, f"{half} - 32", 28, size=15, color="nfBaseDarkest", bold=True),
        C("galMyProj", GALLERY, {
            "Items": "Filter(Projects, PMEmail = nfMe && IsActive = true)", "X": 40, "Y": 184,
            "Width": f"{half} - 32", "Height": "Parent.Height - 216", "TemplateSize": 112, "TemplatePadding": 0,
            "BorderColor": "RGBA(0,0,0,0)", "AccessibleLabel": '"My projects"',
        }, [
            lbl("mpTitle", 'ThisItem.ProjectCode & " · " & ThisItem.Title', 0, 6, "Parent.TemplateWidth - 130", 48,
                size=14, color="nfBaseDarkest", bold=True, VerticalAlign="VerticalAlign.Top"),
            chip("mpChip", "ThisItem.CurrentHealth", "Parent.TemplateWidth - 112", 8),
            lbl("mpStale",
                f'If({stale}, "No update for week of " & Text(nfReportWeek, "mmm d"), "Updated week of " & Text(ThisItem.LastUpdateWeek, "mmm d"))',
                0, 54, "Parent.TemplateWidth - 300", 24, size=12, color=f"If({stale}, nfRed, nfBaseMedium)"),
            btn("mpOpen", '"Open"', "Parent.TemplateWidth - 284", 60, 120, 36,
                'Set(varProject, ThisItem); Set(varTab, "Overview"); Navigate(scrProject, ScreenTransition.Fade)', primary=False),
            btn("mpUpdate", '"Post update"', "Parent.TemplateWidth - 152", 60, 150, 36,
                "Set(varProject, ThisItem); Navigate(scrUpdate, ScreenTransition.Fade)"),
            rect("mpSep", 0, 111, "Parent.TemplateWidth", 1, "nfBaseLighter"),
        ], variant="Vertical"),
        card("pnlMyAct", f"40 + {half}", 144, half, "Parent.Height - 160"),
        lbl("lblMyActHead", '"My open actions"', f"56 + {half}", 152, f"{half} - 32", 28, size=15,
            color="nfBaseDarkest", bold=True),
        C("galMyActions", GALLERY, {
            "Items": 'Sort(Filter(ActionItems, OwnerEmail = nfMe && Status = "Open"), DueDate, SortOrder.Ascending)',
            "X": f"56 + {half}", "Y": 184, "Width": f"{half} - 32", "Height": "(Parent.Height - 216) * 0.55", "TemplateSize": 64,
            "TemplatePadding": 0, "BorderColor": "RGBA(0,0,0,0)", "AccessibleLabel": '"My open actions"',
        }, [
            C("tglMyDone", TOGGLE, {
                "Default": "false", "X": 0, "Y": 14, "Width": 140, "Height": 36, "TrueText": '"Done"',
                "FalseText": '"Open"', "TrueFill": "nfGreen", "FalseFill": "nfBaseLight",
                "AccessibleLabel": '"Mark " & ThisItem.Title & " done"',
                "OnCheck": 'Patch(ActionItems, LookUp(ActionItems, ID = ThisItem.ID), {Status: "Done", CompletedOn: Today()}); Notify("Marked done. It moved to Completed below, where you can undo it.", NotificationType.Success)',
            }),
            lbl("maTitle", "ThisItem.Title", 152, 6, "Parent.TemplateWidth - 230", 26, size=13, color="nfBaseDarkest", bold=True),
            lbl("maProj", 'LookUp(Projects, ID = ThisItem.ProjectID).ProjectCode', 152, 32, 200, 22, size=12, color="nfBaseDark"),
            lbl("maDue", '"Due " & Text(ThisItem.DueDate, "mmm d")', "Parent.TemplateWidth - 110", 18, 110, 28, size=13,
                bold=True, Align="Align.Right", color="If(ThisItem.DueDate < Today(), nfRed, nfBaseDark)"),
            rect("maSep", 0, 63, "Parent.TemplateWidth", 1, "nfBaseLighter"),
        ], variant="Vertical"),
        lbl("lblMyDoneHead", '"Completed: click Undo to reopen"', f"56 + {half}",
            "184 + (Parent.Height - 216) * 0.55 + 8", f"{half} - 32", 26, size=13, color="nfBaseDarkest", bold=True),
        C("galMyDone", GALLERY, {
            "Items": 'Sort(Filter(ActionItems, OwnerEmail = nfMe && Status = "Done"), CompletedOn, SortOrder.Descending)',
            "X": f"56 + {half}", "Y": "184 + (Parent.Height - 216) * 0.55 + 38", "Width": f"{half} - 32",
            "Height": "(Parent.Height - 216) * 0.45 - 46", "TemplateSize": 48, "TemplatePadding": 0,
            "BorderColor": "RGBA(0,0,0,0)", "AccessibleLabel": '"My completed actions"',
        }, [
            lbl("mdTitle", 'ThisItem.Title', 0, 4, "Parent.TemplateWidth - 140", 22, size=12, color="nfBaseDark"),
            lbl("mdWhen", '"Done " & Text(ThisItem.CompletedOn, "mmm d")', 0, 24, 200, 20, size=11, color="nfBaseMedium"),
            btn("mdUndo", '"Undo"', "Parent.TemplateWidth - 112", 6, 100, 34,
                'Patch(ActionItems, LookUp(ActionItems, ID = ThisItem.ID), {Status: "Open", CompletedOn: Blank()}); Notify("Reopened: " & ThisItem.Title, NotificationType.Information)',
                primary=False),
            rect("mdSep", 0, 47, "Parent.TemplateWidth", 1, "nfBaseLighter"),
        ], variant="Vertical"),
    ]
    props = {"Fill": "nfMuted", "OnVisible": "Refresh(ActionItems); Refresh(Projects)"}
    return screen_yaml("scrMyWork", props, ch)


# ---------------------------------------------------------------- write
HEADER_COMMENT = ""


def main(src):
    srcdir = os.path.join(src, "Src")
    for f in os.listdir(srcdir):
        if f.endswith(".pa.yaml") and f not in ("_EditorState.pa.yaml",):
            os.remove(os.path.join(srcdir, f))
    files = {
        "App.pa.yaml": APP_YAML,
        "scrPortfolio.pa.yaml": portfolio(),
        "scrProject.pa.yaml": project(),
        "scrUpdate.pa.yaml": update(),
        "scrAnalytics.pa.yaml": analytics(),
        "scrMyWork.pa.yaml": mywork(),
    }
    for name, body in files.items():
        with open(os.path.join(srcdir, name), "w") as fh:
            fh.write(body)
    with open(os.path.join(srcdir, "_EditorState.pa.yaml"), "w") as fh:
        fh.write("EditorState:\n  ScreensOrder:\n" + "".join(
            f"    - {s}\n" for s in ["scrPortfolio", "scrProject", "scrUpdate", "scrAnalytics", "scrMyWork"]))
    print("wrote", ", ".join(files))


if __name__ == "__main__":
    main(sys.argv[1])
