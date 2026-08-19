"""
EmailNotificationService — source file used to pose mocking-decision questions.

Has three kinds of dependency:
  - An HTTP client for fetching user preferences (query — return value matters)
  - An SMTP client for sending email (command — side effect, no useful return value)
  - A metrics recorder for tracking send counts (fire-and-forget side effect)
"""

import requests as http_lib


class EmailNotificationService:
    def __init__(self, http_client=None, smtp_client=None, metrics=None):
        self._http = http_client or http_lib
        self._smtp = smtp_client
        self._metrics = metrics

    def notify(self, user_id: str, message: str) -> bool:
        """Send a notification email to a user.

        Fetches the user's email address from the preferences API, sends
        the email via SMTP, and records a metric.

        Returns True if the email was sent successfully.
        """
        prefs = self._http.get(f"https://prefs.example.com/users/{user_id}")
        if prefs.status_code != 200:
            return False

        email = prefs.json()["email"]
        self._smtp.send(to=email, subject="Notification", body=message)
        self._metrics.increment("email.sent", tags={"user_id": user_id})
        return True
