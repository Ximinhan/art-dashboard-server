
import os
import requests
from slack_sdk import WebClient

slack_token = os.environ.get('SLACK_TOKEN', None)
release_status = requests.get("https://art-dash-server-hackspace-ximhan.apps.artc2023.pc3z.p1.openshiftapps.com/api/v1/release_status").json()
if release_status['alert'] != []:
    response = WebClient(token=slack_token).chat_postMessage(
            channel="#art-bot-monitoring",
            text=''.join([msg['status'] for msg in release_status['alert']]),
            thread_ts=None, username="art-release-bot", link_names=True, attachments=[], icon_emoji=":robot_face:", reply_broadcast=False)
else:
    print("No alert", [msg['status'] for msg in release_status['message']])
