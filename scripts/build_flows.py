"""Writes the two PMO Project Hub cloud flow definitions into an exported solution folder.

Run: python3 build_flows.py <exported-solution-dir>
Internal SharePoint column names (field_N) come from the CSV import; see BUILD-GUIDE.md section 5a.
"""
import glob
import json
import os
import sys

SITE = "https://contoso.sharepoint.com/sites/SystemsRedesignDemo"
APP_LINK = ("https://apps.powerapps.com/play/e/e2c446bf-f2c7-ea30-a9fa-186d9566b417"
            "/a/3fb3c57a-a192-4e5b-a219-1cb73e980970")
T = {  # SharePoint list GUIDs
    "Projects": "8085c073-810e-4211-9a9c-ca685a249def",
    "Milestones": "4e2a767c-d3a8-4be7-b8a6-1cf564a5425a",
    "StatusUpdates": "599d9ad7-25ce-4a27-82df-19581bfd543c",
    "Risks": "5c16eed3-1a7a-4f8f-91c7-3b4ecdfbc553",
    "ActionItems": "21487070-0ede-4f95-8c7a-694b4bbe5b09",
    "PMOTeam": "c90e6db4-6337-4275-9dd3-644e233008c0",
}
TZ = "Pacific Standard Time"
EMBEDDED = "@parameters('$authentication')"
INVOKER = {"value": "@json(decodeBase64(triggerOutputs().headers['X-MS-APIM-Tokens']))['$ConnectionKey']", "type": "Raw"}


def sp(op, params, run_after, auth=EMBEDDED):
    return {"runAfter": run_after, "type": "OpenApiConnection", "inputs": {
        "host": {"apiId": "/providers/Microsoft.PowerApps/apis/shared_sharepointonline",
                 "connectionName": "shared_sharepointonline", "operationId": op},
        "parameters": dict({"dataset": SITE}, **params), "authentication": auth}}


def od(op, params, run_after):
    a = {"runAfter": run_after, "type": "OpenApiConnection", "inputs": {
        "host": {"apiId": "/providers/Microsoft.PowerApps/apis/shared_onedriveforbusiness",
                 "connectionName": "shared_onedriveforbusiness", "operationId": op},
        "parameters": params, "authentication": INVOKER}}
    if op == "CreateFile":
        a["runtimeConfiguration"] = {"contentTransfer": {"transferMode": "Chunked"}}
    return a


def teams(recipient, html, run_after):
    return {"runAfter": run_after, "type": "OpenApiConnection", "inputs": {
        "host": {"apiId": "/providers/Microsoft.PowerApps/apis/shared_teams",
                 "connectionName": "shared_teams", "operationId": "PostMessageToConversation"},
        "parameters": {"poster": "Flow bot", "location": "Chat with Flow bot",
                       "body/recipient": recipient, "body/messageBody": html},
        "authentication": EMBEDDED}}


def ok(*names):
    return {n: ["Succeeded"] for n in names}


BASE_PARAMS = {"$connections": {"defaultValue": {}, "type": "Object"},
               "$authentication": {"defaultValue": {}, "type": "SecureObject"}}


# ------------------------------------------------------------ Flow A: weekly reminder
def reminder(existing):
    now = f"convertFromUtc(utcNow(), '{TZ}')"
    report_week = f"@formatDateTime(addDays({now}, sub(-7, mod(add(dayOfWeek({now}), 6), 7))), 'yyyy-MM-dd')"
    each = "items('For_each_missing_project')"
    pm_msg = (
        "<p><b>Weekly update reminder</b></p>"
        f"<p>Hi @{{{each}?['field_6']}}, <b>@{{{each}?['field_1']}} · @{{{each}?['Title']}}</b> doesn't have a status "
        "update for the week of @{formatDateTime(outputs('Report_week'), 'MMM d')} yet. It takes about 2 minutes.</p>"
        f"<p><a href=\"@{{outputs('App_link')}}?screen=update&projectId=@{{{each}?['ID']}}\">Post your update now</a></p>"
    )
    n_missing = "length(body('Missing_updates'))"
    n_active = "length(outputs('Get_active_projects')?['body/value'])"
    digest = (
        f"@{{if(greater({n_missing}, 0), "
        f"concat('<p><b>PMO weekly check</b>: ', string({n_missing}), ' of ', string({n_active}), "
        "' active projects are missing the update for the week of ', formatDateTime(outputs('Report_week'), 'MMM d'), "
        "'.</p><ul>', join(body('Digest_lines'), ''), '</ul><p>Project managers with Teams accounts were reminded directly.</p>'), "
        f"concat('<p><b>PMO weekly check</b>: all ', string({n_active}), "
        "' active projects posted their update for the week of ', formatDateTime(outputs('Report_week'), 'MMM d'), '.</p>'))}"
    )
    actions = {
        "Report_week": {"runAfter": {}, "type": "Compose", "inputs": report_week},
        "App_link": {"runAfter": ok("Report_week"), "type": "Compose", "inputs": APP_LINK},
        "Get_active_projects": sp("GetItems", {"table": T["Projects"], "$filter": "field_19 eq 1", "$top": 500},
                                  ok("App_link")),
        "Missing_updates": {"runAfter": ok("Get_active_projects"), "type": "Query", "inputs": {
            "from": "@outputs('Get_active_projects')?['body/value']",
            "where": "@or(empty(item()?['field_18']), less(formatDateTime(item()?['field_18'], 'yyyy-MM-dd'), outputs('Report_week')))"}},
        "For_each_missing_project": {"runAfter": ok("Missing_updates"), "type": "Foreach",
                                     "foreach": "@body('Missing_updates')", "actions": {
            "PM_has_Teams_account": {"runAfter": {}, "type": "If",
                                     "expression": {"not": {"contains": [f"@toLower(coalesce({each}?['field_7'], ''))", "example.org"]}},
                                     "actions": {"Remind_PM_in_Teams": teams(f"@{each}?['field_7']", pm_msg, {})},
                                     "else": {"actions": {}}}}},
        "Digest_lines": {"runAfter": ok("For_each_missing_project"), "type": "Select", "inputs": {
            "from": "@body('Missing_updates')",
            "select": "@concat('<li><a href=\"', outputs('App_link'), '?screen=project&projectId=', item()?['ID'], '\">', "
                      "item()?['field_1'], '</a> ', item()?['Title'], ' (PM: ', item()?['field_6'], ')</li>')"}},
        "Get_PMO_team": sp("GetItems", {"table": T["PMOTeam"]}, ok("Digest_lines")),
        "For_each_PMO_member": {"runAfter": ok("Get_PMO_team"), "type": "Foreach",
                                "foreach": "@outputs('Get_PMO_team')?['body/value']", "actions": {
            "Send_PMO_summary": teams("@items('For_each_PMO_member')?['Title']", digest, {})}},
    }
    rec = {"frequency": "Week", "interval": 1, "timeZone": TZ, "startTime": "2026-11-30T09:00:00",
           "schedule": {"weekDays": ["Monday"], "hours": ["9"], "minutes": [0]}}
    existing["properties"]["definition"] = {
        "$schema": existing["properties"]["definition"]["$schema"], "contentVersion": "1.0.0.0",
        "parameters": BASE_PARAMS,
        "triggers": {"Recurrence": {"recurrence": rec, "evaluatedRecurrence": rec, "type": "Recurrence"}},
        "actions": actions}
    return existing


# ------------------------------------------------------------ Flow B: status report
def report(existing):
    pid = "triggerBody()['number']"
    P = "outputs('Get_project')?['body']"
    U = "first(outputs('Get_latest_update')?['body/value'])"
    slip = ("div(sub(ticks(coalesce(item()?['field_5'], item()?['field_4'])), ticks(item()?['field_3'])), 864000000000)")
    ms_row = ("@concat('<tr><td>', item()?['Title'], '</td><td>', formatDateTime(item()?['field_3'], 'MMM d'), '</td><td>', "
              "if(empty(item()?['field_5']), concat('Forecast ', formatDateTime(item()?['field_4'], 'MMM d')), "
              "concat('Done ', formatDateTime(item()?['field_5'], 'MMM d'))), '</td><td>', item()?['field_6'], "
              f"'</td><td style=\"font-weight:600;color:', if(greater({slip}, 0), '#CD2026', '#2E8540'), '\">', "
              f"if(greater({slip}, 0), concat('+', string({slip}), ' days'), 'On time'), '</td></tr>')")
    risk_row = ("@concat('<tr><td style=\"font-weight:600\">', string(item()?['field_4']), '</td><td>', item()?['Title'], "
                "'</td><td>', item()?['field_5'], '</td><td>', item()?['field_6'], '</td><td>', item()?['field_7'], '</td></tr>')")
    act_row = ("@concat('<tr><td>', item()?['Title'], '</td><td>', item()?['field_2'], '</td><td style=\"', "
               "if(less(ticks(item()?['field_4']), ticks(utcNow())), 'color:#CD2026;font-weight:600', ''), '\">', "
               "formatDateTime(item()?['field_4'], 'MMM d'), "
               "if(less(ticks(item()?['field_4']), ticks(utcNow())), ' (overdue)', ''), '</td></tr>')")
    b, t, c = (f"float(string({P}?['field_13']))", f"float(string({P}?['field_14']))", f"float(string({P}?['field_15']))")
    progress = f"if(equals({b}, {t}), 100, mul(100, max(0, min(1, div(sub({b}, {c}), sub({b}, {t}))))))"
    health = f"{P}?['field_16']"
    hbg = f"if(equals({health}, 'Green'), '#ecf3ec', if(equals({health}, 'Yellow'), '#faf3d1', '#f4e3db'))"
    hbd = f"if(equals({health}, 'Green'), '#2E8540', if(equals({health}, 'Yellow'), '#FDB81E', '#CD2026'))"
    css = ("body{font-family:'Segoe UI',Arial,sans-serif;color:#3d4551;margin:32px;font-size:13px}"
           "h1{color:#112E51;margin:0 0 4px;font-size:22px}h2{color:#1b1b1b;font-size:15px;margin:22px 0 8px;"
           "border-bottom:1px solid #dfe1e2;padding-bottom:4px}.muted{color:#71767a}"
           ".chip{display:inline-block;padding:3px 12px;font-weight:600;color:#1b1b1b}"
           "table{border-collapse:collapse;width:100%}th{background:#f0f0f0;text-align:left;color:#1b1b1b}"
           "th,td{padding:6px 8px;border-bottom:1px solid #dfe1e2;vertical-align:top;font-size:12px}"
           "h2,table{page-break-inside:avoid}h2{page-break-after:avoid}"
           ".bar{background:#dfe1e2;height:10px;width:100%}.fill{background:#0071BC;height:10px}"
           ".grid{display:flex;gap:16px}.grid div{flex:1;background:#f0f0f0;padding:10px}")
    html = (
        f"<!DOCTYPE html><html><head><meta charset=\"utf-8\"><style>{css}</style></head><body>"
        "<div class=\"muted\">PMO Project Hub · Weekly status report · "
        f"@{{formatDateTime(convertFromUtc(utcNow(), '{TZ}'), 'MMM d, yyyy')}} · Demo, fictitious data</div>"
        f"<h1>@{{{P}?['field_1']}} · @{{{P}?['Title']}}</h1>"
        f"<div>PM: @{{{P}?['field_6']}} · Sponsor: @{{{P}?['field_8']}} · Phase: @{{{P}?['field_5']}} · "
        f"@{{{P}?['field_2']}} · @{{{P}?['field_3']}}</div>"
        f"<p><span class=\"chip\" style=\"background:@{{{hbg}}};border:2px solid @{{{hbd}}}\">@{{{health}}}</span>"
        f" &nbsp; @{{{P}?['field_17']}}% complete</p>"
        f"<h2>Target metric: @{{{P}?['field_12']}}</h2>"
        f"<p>Baseline @{{{P}?['field_13']}} → now <b>@{{{P}?['field_15']}}</b> → target @{{{P}?['field_14']}} · "
        f"<b>@{{formatNumber({progress}, '0')}}% of the way to target</b></p>"
        f"<div class=\"bar\"><div class=\"fill\" style=\"width:@{{formatNumber({progress}, '0')}}%\"></div></div>"
        f"<h2>Latest update (week of @{{formatDateTime({U}?['field_2'], 'MMM d')}})</h2>"
        f"<div class=\"grid\"><div><b>Done</b><br>@{{{U}?['field_6']}}</div><div><b>Next</b><br>@{{{U}?['field_7']}}</div>"
        f"<div><b>Blockers</b><br>@{{coalesce({U}?['field_8'], 'None')}}</div></div>"
        "<h2>Milestones</h2><table><tr><th>Milestone</th><th>Planned</th><th>Forecast / actual</th><th>Status</th>"
        "<th>Variance</th></tr>@{join(body('Milestone_rows'), '')}</table>"
        "<h2>Open risks (score = likelihood × impact)</h2><table><tr><th>Score</th><th>Risk</th><th>Mitigation</th>"
        "<th>Owner</th><th>Status</th></tr>@{join(body('Risk_rows'), '')}</table>"
        "<h2>Open actions</h2><table><tr><th>Action</th><th>Owner</th><th>Due</th></tr>"
        "@{join(body('Action_rows'), '')}</table>"
        "<p class=\"muted\" style=\"margin-top:24px\">Generated by Power Automate from SharePoint lists "
        "(Projects, StatusUpdates, Milestones, Risks, ActionItems).</p></body></html>"
    )
    filt = f"field_1 eq @{{{pid}}}"
    actions = {
        "Get_project": sp("GetItem", {"table": T["Projects"], "id": f"@{pid}"}, {}),
        "Get_latest_update": sp("GetItems", {"table": T["StatusUpdates"], "$filter": filt, "$orderby": "field_2 desc",
                                              "$top": 1}, ok("Get_project")),
        "Get_milestones": sp("GetItems", {"table": T["Milestones"], "$filter": filt, "$orderby": "field_2 asc"},
                             ok("Get_latest_update")),
        "Get_open_risks": sp("GetItems", {"table": T["Risks"], "$filter": f"{filt} and field_7 ne 'Closed'",
                                          "$orderby": "field_4 desc"}, ok("Get_milestones")),
        "Get_open_actions": sp("GetItems", {"table": T["ActionItems"], "$filter": f"{filt} and field_5 eq 'Open'",
                                            "$orderby": "field_4 asc"}, ok("Get_open_risks")),
        "Milestone_rows": {"runAfter": ok("Get_open_actions"), "type": "Select",
                           "inputs": {"from": "@outputs('Get_milestones')?['body/value']", "select": ms_row}},
        "Risk_rows": {"runAfter": ok("Milestone_rows"), "type": "Select",
                      "inputs": {"from": "@outputs('Get_open_risks')?['body/value']", "select": risk_row}},
        "Action_rows": {"runAfter": ok("Risk_rows"), "type": "Select",
                        "inputs": {"from": "@outputs('Get_open_actions')?['body/value']", "select": act_row}},
        "Report_HTML": {"runAfter": ok("Action_rows"), "type": "Compose", "inputs": html},
        "Report_name": {"runAfter": ok("Report_HTML"), "type": "Compose",
                        "inputs": f"@{{{P}?['field_1']}} status report @{{formatDateTime(convertFromUtc(utcNow(), '{TZ}'), 'yyyy-MM-dd HHmm')}}"},
        "Create_HTML_file": od("CreateFile", {"folderPath": "/PMO Reports",
                                              "name": "@{outputs('Report_name')}.html",
                                              "body": "@outputs('Report_HTML')"}, ok("Report_name")),
        "Convert_to_PDF": od("ConvertFile", {"id": "@body('Create_HTML_file')?['Id']", "type": "PDF"},
                             ok("Create_HTML_file")),
        "Save_PDF_to_team_site": sp("CreateFile", {"folderPath": "/Shared Documents/General",
                                                   "name": "@{outputs('Report_name')}.pdf",
                                                   "body": "@body('Convert_to_PDF')"}, ok("Convert_to_PDF")),
        "Respond_to_the_app": {"runAfter": ok("Save_PDF_to_team_site"), "type": "Response", "kind": "PowerApp",
                               "inputs": {"statusCode": 200, "body": {
                                   "reporturl": f"@{{concat('{SITE}/Shared%20Documents/Forms/AllItems.aspx?id=', uriComponent(concat('/sites/SystemsRedesignDemo/Shared Documents/General/', outputs('Report_name'), '.pdf')), '&parent=', uriComponent('/sites/SystemsRedesignDemo/Shared Documents/General'))}}"},
                                   "schema": {"type": "object", "properties": {"reporturl": {
                                       "title": "reporturl", "x-ms-dynamically-added": True, "type": "string"}}}}},
        "Delete_temp_HTML": od("DeleteFile", {"id": "@body('Create_HTML_file')?['Id']"}, ok("Respond_to_the_app")),
    }
    props = existing["properties"]
    props["connectionReferences"]["shared_sharepointonline"] = {
        "runtimeSource": "embedded",
        "connection": {"connectionReferenceLogicalName": "kr_sharedsharepointonline_b8320"},
        "api": {"name": "shared_sharepointonline"}}
    props["definition"] = {
        "$schema": props["definition"]["$schema"], "contentVersion": "1.0.0.0", "parameters": BASE_PARAMS,
        "triggers": {"manual": {"type": "Request", "kind": "PowerAppV2", "inputs": {"schema": {
            "type": "object",
            "properties": {"number": {"title": "ProjectID", "type": "number", "x-ms-dynamically-added": True,
                                      "description": "ID of the project in the Projects list",
                                      "x-ms-content-hint": "NUMBER"}},
            "required": ["number"]}}}},
        "actions": actions}
    return existing


def main(sol):
    for f in glob.glob(os.path.join(sol, "Workflows", "*.json")):
        d = json.load(open(f))
        if "PMOWeeklyUpdateReminder" in f:
            d = reminder(d)
        elif "PMOStatusReport" in f:
            d = report(d)
        json.dump(d, open(f, "w"), indent=2, ensure_ascii=False)
        print("wrote", os.path.basename(f))


if __name__ == "__main__":
    main(sys.argv[1])
