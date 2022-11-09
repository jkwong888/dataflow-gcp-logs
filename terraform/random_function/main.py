import functions_framework
from concurrent import futures
from typing import Callable
from datetime import datetime
import random
import os
import time
import json
from google.cloud import pubsub_v1
import urllib.request
from flask import jsonify


URLS = [
    "https://www.yahoo.com/",
    "https://www.facebook.com/",
    "https://www.amazon.com/",
    "https://www.apple.com/",
    "https://www.netflix.com/",
    "https://www.google.com/",
    "https://www.twitter.com/",
    "https://www.microsoft.com/",
    "https://www.gmail.com/",
    "https://www.youtube.com/",
    "https://cloud.google.com/",
    "https://www.slack.com/",
    "https://www.reddit.com/",
    "https://www.instagram.com/",
    "https://www.tiktok.com/",
    "https://www.weather.com/",
    "https://www.wikipedia.org/",
    "https://www.paypal.com/",
    "https://www.bing.com/",
    "https://www.twitch.tv/",
    "https://www.duckduckgo.com/",
    "https://www.stackoverflow.com/",
    "https://www.zoom.us/",
    "https://www.shopify.com/",
    "https://www.github.com/",
    "https://www.salesforce.com/",
]

def getProjectId():
    url = "http://metadata.google.internal/computeMetadata/v1/project/project-id"
    req = urllib.request.Request(url)
    req.add_header("Metadata-Flavor", "Google")
    project_id = urllib.request.urlopen(req).read().decode()

    return project_id

def randomReview():
    randomRating = random.randint(1, 10)
    randomUrlIndex = random.randint(0, len(URLS) - 1)
    output = {
        "url": URLS[randomUrlIndex], 
        "review": randomRating / 2,
        "post_time": round(time.time()*1000)    
    }

    return output

def publish_message(publisher: pubsub_v1.PublisherClient, topic_path: str, message: str, future_callback: Callable[[pubsub_v1.publisher.futures.Future], str]) -> pubsub_v1.publisher.futures.Future:
    data = json.dumps(message).encode("utf-8")
    future = publisher.publish(topic_path, data)

    future.add_done_callback(future_callback)

    return future

@functions_framework.http
def randomgen(request):
    project_id = os.environ["PROJECT_ID"]
    if project_id is None:
        project_id = getProjectId()
    
    topic_id = os.environ["TOPIC_ID"]
    randomNum = random.randint(1, 60)

    allMessages = []
    publish_futures = []
    batch_settings = pubsub_v1.types.BatchSettings(
        # 2 MiB. Default to 3 MiB. Must be less than 4 MiB gRPC's per-message limit.
        max_bytes=2 * 1024 * 1024,
        # 100 ms. Default to 50 ms.
        max_latency=0.1,
        # Default to 1000.
        max_messages=100,
    )

    with pubsub_v1.PublisherClient(batch_settings) as publisher:
        topic_path = publisher.topic_path(project_id, topic_id)

        for i in range(randomNum):
            publish_futures.append(publish_message(publisher, 
                topic_path, 
                randomReview(), 
                lambda future: allMessages.append(future.result())))
            randomSleep = random.random() 
            time.sleep(randomSleep)
        
        futures.wait(publish_futures, return_when=futures.ALL_COMPLETED)

    return jsonify(len(allMessages))
