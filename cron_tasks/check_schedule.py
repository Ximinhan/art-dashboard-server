
import os
import requests
import time
from slack_sdk import WebClient

slack_token = os.environ.get('SLACK_TOKEN', None)
release_status = requests.get("https://art-dash-server-hackspace-ximhan.apps.artc2023.pc3z.p1.openshiftapps.com/api/v1/release_status").json()
if release_status['alert'] != []:
    response = WebClient(token=slack_token).chat_postMessage(
            channel="#art-bot-monitoring",
            text=' \n'.join([msg['status'] for msg in release_status['alert']]),
            thread_ts=None, username="art-release-bot", link_names=True, attachments=[], icon_emoji=":dancing_robot:", reply_broadcast=False)
    print(f"message posted in https://redhat-internal.slack.com/archives/{response['channel']}/p{response['ts'].replace('.', '')}")
    if release_status['unshipped'] != []:
        while release_status['unshipped'] != []:
            for ad, msg in release_status['unshipped'].items():
                # check ad status
                advisory_status_response = requests.get(f"https://art-dash-server-hackspace-ximhan.apps.artc2023.pc3z.p1.openshiftapps.com/api/v1/advisory_activites/?advisory={ad}").json()
                advisory_status = advisory_status_response['data'][-1]['attributes']['added']
                if advisory_status == "SHIPPED_LIVE" or advisory_status == "DROPPED_NO_SHIP":
                    release_status['unshipped'].pop(ad)
                    response = WebClient(token=slack_token).chat_postMessage(
                        channel="#art-bot-monitoring",
                        text=f"{msg} status changed to {advisory_status}",
                        thread_ts=response['ts'], username="art-release-bot", link_names=True, attachments=[], icon_emoji=":dancing_robot:", reply_broadcast=False)
            # sleep 6 hours
            time.sleep(21600)
else:
    print("No alert", [msg['status'] for msg in release_status['message']])
