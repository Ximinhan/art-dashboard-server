
import os
import re
from datetime import date
import requests
import time
from typing import Optional
from slack_sdk import WebClient

slack_token = os.environ.get('SLACK_TOKEN', None)
def post_slack_message(message: str, thread_ts: Optional[str] = None, channel: Optional[str] = "#forum-ocp-release"):
    return WebClient(token=slack_token).chat_postMessage(channel=channel, text=message, thread_ts=thread_ts, username="art-release-bot", link_names=True, attachments=[], icon_emoji=":dancing_robot:", reply_broadcast=False)


# check release need to prepare
releases_needs_prepare = requests.get("https://art-dash-server-hackspace-ximhan.apps.artc2023.pc3z.p1.openshiftapps.com/api/v1/release_prepare_alert").json()
if releases_needs_prepare['releases'] != []:
    release_msg = "\n".join(f"• {msg[0]} : {msg[1]}, latest <https://amd64.ocp.releases.ci.openshift.org/releasestream/{msg[2]}.0-0.nightly/release/{msg[3]}|{msg[3]}> is {msg[4]}" for msg in releases_needs_prepare['releases'])
    post_slack_message(f"We need to prepare the following releases today:\n{release_msg}", thread_ts=None, channel="#ocp-sustaining-art-collaboration")

def get_ga_version():
    """
    Get the latest GA version from https://github.com/openshift/cincinnati-graph-data/tree/master/channels
    The highest version in the fast channel is considered GA.
    """
    headers = {"Authorization": f"token {os.environ['GITHUB_PERSONAL_ACCESS_TOKEN']}"}
    response = requests.get(
        "https://api.github.com/repos/openshift/cincinnati-graph-data/git/trees/master?recursive=1",
        headers=headers
    )

    versions = []

    for data in response.json()['tree']:
        path: str = data['path']

        regex = r"channels/fast-(?P<version>\d+.\d+).yaml"

        if path.startswith("channels/fast"):
            m = re.match(regex, path)
            if m:
                version: str = m.groupdict()['version']
                versions.append(tuple(map(int, version.split("."))))
    ga_version = sorted(versions, key=lambda x: (-x[0], -x[1]))[0]

    return f"{ga_version[0]}.{ga_version[1]}"

print(date.today())
ga_version = get_ga_version()
major, minor = ga_version.split(".")
releases_need_to_ship = []
# loop from ga version to previous until eol release, there is a treak that we look for previous 5 releases, so no need to connect github
start_minor = 12
versions = [f"{major}.{i}" for i in range(start_minor, int(minor) + 1)]
for version in versions:
    release_ship_schedule = requests.get(f"https://art-dash-server-hackspace-ximhan.apps.artc2023.pc3z.p1.openshiftapps.com/api/v1/release_schedule?type=release&branch_version={version}").json()
    print(version)
    print(release_ship_schedule)
    for release in release_ship_schedule["all_ga_tasks"]:
        if date.fromisoformat(release['date_finish']) == (date.today()):
            releases_need_to_ship.append([release['name'].split(' ')[0], release['date_finish']])
            break
print(releases_need_to_ship)

# check and monitor release advisory status, moved to konflux now
# release_status = requests.get("https://art-dash-server-hackspace-ximhan.apps.artc2023.pc3z.p1.openshiftapps.com/api/v1/release_status").json()
# if release_status['alert'] != []:
#     response = post_slack_message(' \n'.join([msg['status'] for msg in release_status['alert']]))
#     print(f"message posted in https://redhat-internal.slack.com/archives/{response['channel']}/p{response['ts'].replace('.', '')}")
#     if release_status['unshipped'] != []:
#         post_slack_message("start monitoring advisory not in shipped live status, interval set to 1 hour ...", thread_ts=response['ts'])
#         duration = 1
#         alert_artist = False
#         while release_status['unshipped'] != []:
#             for item in release_status['unshipped']:
#                 advisory_status_response = requests.get(f"https://art-dash-server-hackspace-ximhan.apps.artc2023.pc3z.p1.openshiftapps.com/api/v1/advisory_activites/?advisory={item['advisory']}").json()
#                 advisory_status = advisory_status_response['data'][-1]['attributes']['added'] if len(advisory_status_response['data']) > 0 else "NEW_FILES"
#                 if advisory_status in ["SHIPPED_LIVE", "DROPPED_NO_SHIP"]:
#                     release_status['unshipped'].remove(item)
#                     post_slack_message(f"{item['note']} status changed to {advisory_status}", thread_ts=response['ts'])
#                     # extra advisory changed to shipped_live
#                     if "extra" in item['note'] and advisory_status == "SHIPPED_LIVE":
#                         if int(item['note'].split(' ')[0].split('.')[1]) < 19:
#                             trigger_jenkins_response = requests.get(f"https://art-dash-server-hackspace-ximhan.apps.artc2023.pc3z.p1.openshiftapps.com/api/v1/trigger_jenkins_job/?assembly={item['note'].split(' ')[0]}").json()
#                             post_slack_message(f"<{trigger_jenkins_response['build_url']}|operator_sdk> job for {item['note'].split(' ')[0]} triggered", thread_ts=response['ts'])

#             print(f"sleeping 1 hours due to {release_status['unshipped']}")
#             time.sleep(3600)
#             duration = duration + 1
#             if duration > 24 and not alert_artist:
#                 post_slack_message("@release-artists those advisories are not all shipped after a day of ship day, please take a look a push them ship as soon as possible", thread_ts=response['ts'])
#                 alert_artist = True
#         post_slack_message("All advisory now in shipped live status, stop monitoring", thread_ts=response['ts'])
# else:
#     print("No alert", [msg['status'] for msg in release_status['message']])

