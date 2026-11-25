# PMO Project Hub

A Power Apps + Power Automate solution that gives a facility one place to track every improvement project: weekly status from project managers, live portfolio health for leaders, and automatic follow-up so nothing goes stale.

**[Read the solution brief (PDF)](docs/PMO-Project-Hub-Solution-Brief.pdf)**

## The problem

Improvement teams often run many projects at once, but status lives in emails, spreadsheets and slide decks. Leaders only see the full picture at monthly meetings, by which point a missed milestone or an unaddressed risk has already cost weeks. Project managers rebuild the same report every week, and chasing updates falls on whoever runs the portfolio.

## What it does

Project managers post a 2-minute weekly update that carries last week's answers forward and asks for blockers whenever a project isn't on track. Leaders see portfolio health, schedule slip, risks and progress toward targets in real time. Power Automate handles the follow-up: every Monday it messages anyone missing an update in Teams with a link straight to their form, and with one click it turns any project into a PDF status report filed in SharePoint.

| Screen | What it shows |
|---|---|
| Portfolio | KPIs (on-track %, milestones on time, overdue actions, missing updates) and every project with its health |
| Project | Five tabs: overview, metric trend vs. target, milestone variance, 5×5 risk heat map, status history |
| Weekly update | The 2-minute form, with validation and duplicate-week protection |
| Analytics | Portfolio trends with an auto-written headline |
| My work | Your projects and open actions; every completed action can be undone |

## How it's built

| Part | Details |
|---|---|
| **Power Apps (canvas)** | 5 screens written as Power Fx YAML source. Uses named formulas, user-defined functions, delegation-aware filters, deep links with `Param()`, validation and error handling, and VA Design System colors. |
| **SharePoint Online** | 6 lists (Projects, Milestones, StatusUpdates, Risks, ActionItems, PMOTeam) joined on a numeric `ProjectID`, which keeps filters delegable. |
| **Power Automate: Weekly Update Reminder** | Scheduled Monday 9am. Finds active projects missing last week's update, messages each PM in Teams with a deep link, and sends the PMO a summary. |
| **Power Automate: Status Report** | Called from the app with the Power Apps (V2) trigger. Joins 5 lists into an HTML report, converts it to PDF, saves it to SharePoint and returns the link. |
| **ALM** | App, flows and connection references packaged in one Solution, built and deployed with the Power Platform CLI (`pac canvas pack`, `pac solution import`). |

## Repo layout

```
docs/                 Solution brief (PDF) and the full build guide
seed-data/            Fictitious demo data, one CSV per SharePoint list
scripts/              build_screens.py (generates the app's YAML) and build_flows.py (generates both flows)
src/canvas-app/       Unpacked canvas app source (pac canvas unpack format)
src/solution-unpacked Unpacked solution: app, flows, customizations
solution/             PMO_Project_Hub.zip, ready to import
```

## Try it in your own environment

1. Create a SharePoint site and import each CSV in `seed-data/` as a list (**New → List → From CSV**). See [docs/BUILD-GUIDE.md](docs/BUILD-GUIDE.md) for column types and the internal-name mapping.
2. Import the solution:
   ```bash
   pac solution import --path solution/PMO_Project_Hub.zip --publish-changes
   ```
3. Open the app in Power Apps Studio and point its data sources at your site. Update the site URL in both flows, then turn them on.

To change the app, edit `scripts/build_screens.py`, regenerate the YAML into `src/canvas-app`, and pack it:

```bash
python3 scripts/build_screens.py src/canvas-app
pac canvas pack --sources src/canvas-app --msapp PMO-Project-Hub.msapp
```

## About the data

This is a demo built in a personal Power Platform developer environment. Every project, person and number is fictitious, and no VA systems or data were used. The site URL and email addresses in this repo are placeholders (`contoso.sharepoint.com`, `example.org`).

Built by Kaviya Raja, November 2026.
