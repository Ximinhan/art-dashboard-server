
import os
import requests
from typing import Optional
import time
from slack_sdk import WebClient

slack_token = os.environ.get('SLACK_TOKEN', None)
def post_slack_message(message: str, thread_ts: Optional[str] = None,):
    response = WebClient(token=slack_token).chat_postMessage(
                channel="#forum-ocp-release",
                text=message,
                thread_ts=thread_ts, username="art-release-bot", link_names=True, attachments=[], icon_emoji=":dancing_robot:", reply_broadcast=False)
    return response
release_status = requests.get("https://art-dash-server-hackspace-ximhan.apps.artc2023.pc3z.p1.openshiftapps.com/api/v1/release_status").json()
if release_status['alert'] != []:
    response = post_slack_message(' \n'.join([msg['status'] for msg in release_status['alert']]))
    print(f"message posted in https://redhat-internal.slack.com/archives/{response['channel']}/p{response['ts'].replace('.', '')}")
    if release_status['unshipped'] != []:
        post_slack_message("start monitoring advisory not in shipped live status, interval set to 1 hour ...", thread_ts=response['ts'])
        while release_status['unshipped'] != []:
            for item in release_status['unshipped']:
                # check ad status
                advisory_status_response = requests.get(f"https://art-dash-server-hackspace-ximhan.apps.artc2023.pc3z.p1.openshiftapps.com/api/v1/advisory_activites/?advisory={item['advisory']}").json()
                errata_activity = advisory_status_response['data']
                if len(errata_activity) > 0:
                    advisory_status = errata_activity[-1]['attributes']['added']
                else:
                    advisory_status = "NEW_FILES"
                if advisory_status == "SHIPPED_LIVE" or advisory_status == "DROPPED_NO_SHIP":
                    release_status['unshipped'].remove(item)
                    post_slack_message(f"{item['note']} status changed to {advisory_status}", thread_ts=response['ts'])
                    # update original message
            # sleep 1 hours
            print(f"sleeping 1 hours due to {release_status['unshipped']}")
            time.sleep(3600)
        post_slack_message("All advisory now in shipped live status, stop monitoring", thread_ts=response['ts'])
else:
    print("No alert", [msg['status'] for msg in release_status['message']])
