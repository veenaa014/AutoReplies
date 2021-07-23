import os
import logging
import urllib

BOT_TOKEN = os.environ["BOT_TOKEN"]

SLACK_URL = "https://slack.com/api/chat.postMessage"


def lambda_handler(data, context):
    """Handle an incoming HTTP request from a Slack chat-bot.
    """
    slack_event = data['event']

    if "bot_id" in slack_event:
        logging.warn("Ignore bot event")
    else:
        text = slack_event["text"]
        channel_id = slack_event["channel"]

        data = urllib.parse.urlencode(
            (
                ("token", BOT_TOKEN),
                ("channel", channel_id),
                ("text", text)
            )
        )
        data = data.encode("ascii")
        request = urllib.request.Request(
            SLACK_URL,
            data=data,
            method="POST"
        )
        request.add_header(
            "Content-Type",
            "application/x-www-form-urlencoded"
        )
        urllib.request.urlopen(request).read()
    return "200 OK"
