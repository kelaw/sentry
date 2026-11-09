"""
Sentry demo app: a tiny Flask "order service" instrumented with the Sentry Python SDK.

Routes:
  /            index with links to everything below
  /error       unhandled exception (ZeroDivisionError) -> Sentry issue
  /handled     caught exception sent manually with extra context
  /message     plain message event (no exception)
  /checkout    slow-ish request with custom spans -> shows up in Performance/Traces
"""

import os
import random
import time

import sentry_sdk
from flask import Flask, jsonify

# 1. Initialise the SDK once, before the app starts handling requests.
#    The DSN comes from the environment so it never gets committed to git.
sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN"),
    environment=os.environ.get("SENTRY_ENVIRONMENT", "development"),
    release=os.environ.get("SENTRY_RELEASE", "sentry-demo@1.0.0"),
    traces_sample_rate=1.0,   # capture 100% of transactions (fine for a demo, too high for prod)
    send_default_pii=False,   # don't send IPs/headers/cookies by default
    debug=os.environ.get("SENTRY_DEBUG") == "1",  # print SDK activity to the console
)

app = Flask(__name__)


@app.before_request
def tag_request():
    # Tags are indexed and searchable in Sentry; user context shows who was affected.
    sentry_sdk.set_tag("service", "order-service")
    sentry_sdk.set_user({"id": "demo-user-42"})


@app.route("/")
def index():
    return (
        "<h1>Sentry demo</h1><ul>"
        '<li><a href="/error">/error</a> unhandled exception</li>'
        '<li><a href="/handled">/handled</a> caught exception with context</li>'
        '<li><a href="/message">/message</a> message event</li>'
        '<li><a href="/checkout">/checkout</a> traced request with spans</li>'
        "</ul>"
    )


@app.route("/error")
def unhandled_error():
    # The Flask integration catches this automatically and reports it.
    order_total = 100
    items = 0
    if items <= 0:
        # An empty order has no average price; reject it instead of dividing by zero.
        return (
            jsonify(
                error="empty_order",
                message=(
                    "Cannot calculate the average item price: the order contains "
                    f"{items} items (order total: {order_total}). "
                    "Add at least one item to the order and try again."
                ),
                order_total=order_total,
                items=items,
            ),
            400,
        )
    return jsonify(avg_price=order_total / items)


@app.route("/handled")
def handled_error():
    try:
        inventory = {"sku-1": 3}
        inventory["sku-999"]  # KeyError
    except KeyError as exc:
        # Breadcrumbs and context make the issue page far more useful when debugging.
        sentry_sdk.add_breadcrumb(category="inventory", message="Looked up sku-999", level="info")
        sentry_sdk.set_context("order", {"order_id": "A-1001", "sku": "sku-999"})
        event_id = sentry_sdk.capture_exception(exc)
        return jsonify(status="recovered", sentry_event_id=event_id), 200


@app.route("/message")
def message():
    event_id = sentry_sdk.capture_message("Payment provider responded slowly", level="warning")
    return jsonify(sentry_event_id=event_id)


@app.route("/checkout")
def checkout():
    # Custom spans break the request into steps you can see in the trace waterfall.
    with sentry_sdk.start_span(op="db.query", name="load cart"):
        time.sleep(random.uniform(0.05, 0.15))
    with sentry_sdk.start_span(op="http.client", name="charge card (fake payment API)"):
        time.sleep(random.uniform(0.2, 0.4))
    with sentry_sdk.start_span(op="task", name="send confirmation email"):
        time.sleep(0.05)
    return jsonify(status="ok", order_id="A-1001")


if __name__ == "__main__":
    if not os.environ.get("SENTRY_DSN"):
        print("WARNING: SENTRY_DSN is not set, so nothing will be sent to Sentry.")
    app.run(port=5000, debug=False)
