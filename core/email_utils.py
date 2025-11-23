# core/email_utils.py
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import Message


def _safe_send(to_email: str, subject: str, body: str):
    """Send a plain-text email, but never break the app if it fails."""
    if not to_email:
        return
    try:
        send_mail(
            subject.strip(),
            body,
            settings.DEFAULT_FROM_EMAIL,
            [to_email],
            fail_silently=True,  # important: do not crash views
        )
    except Exception:
        # you can log here later if you want
        pass


def send_welcome_email(user, profile):
    name = profile.name or user.first_name or "there"
    subject = "Welcome to Turtle 🐢 — Your story starts with a letter"
    body = (
        f"Hi {name},\n\n"
        "Welcome to Turtle — a slower, more meaningful way to connect.\n\n"
    "On Turtle, everything starts with one letter.\n"
    "You can:\n\n"
    "✍️ Write a text letter directly on the site\n\n"
    "📷 Upload a photo of a handwritten letter\n\n"
    "📄 Upload a PDF you’ve already written\n\n"
    "Once your letter is live, you’ll start seeing other people’s letters based on your preferences (age, city, connection type, etc.).\n\n"
    "You only match when both people like each other’s letters.\n"
    "That means every match comes from words, personality, and intention — not photos.\n\n"
    "And once you match, you’ll unlock each other’s profile details:\n"
    "profile picture, age, city, and more — plus the ability to chat.\n\n"
    "Turtle is designed for people who want something real.\n"
    "Take your time. Share your story. See who it resonates with.\n\n"
    "We’re happy you’re here.\n"
    "Log in here:\n"
    "https://turtleapp.co/accounts/login/\n\n"
    "Slowly,\n"
    "Turtle 🐢\n"
    )
    _safe_send(user.email, subject, body)


def send_like_email(to_profile, from_profile):
    """Used for the *first* like, before there is a match."""
    user = to_profile.user
    if not user.email:
        return

    liker_name = from_profile.name or "Someone"
    name = to_profile.name or user.first_name or "there"

    subject = "Someone liked your letter on Turtle 🐢"
    body = (
        f"Hi {name},\n\n"
        "Someone just liked your letter on Turtle.\n\n"
        "Go read their letter and see if you vibe — "
        "you might discover something meaningful.\n\n"
        "Log in here:\n"
        "https://turtleapp.co/accounts/login/\n\n"
        "Slowly,\n"
        "Turtle 🐢\n"
    )
    _safe_send(user.email, subject, body)


def send_match_email(profile_a, profile_b):
    """
    Called when a *new* Match is created.
    Sends one email to each side, naming the other.
    """
    for me, other in ((profile_a, profile_b), (profile_b, profile_a)):
        user = me.user
        if not user.email:
            continue

        my_name = me.name or user.first_name or "there"
        other_name = other.name or "someone"

        subject = "You have a new match on Turtle 🐢💌"
        body = (
            f"Hi {my_name},\n\n"
            f"You and {other_name} liked each other’s letters.\n"
            "You can now see each other’s profiles and start chatting inside Turtle.\n\n"
            "Log in here:\n"
            "https://turtleapp.co/accounts/login/\n\n"
            "Slowly,\n"
            "Turtle 🐢\n"
        )
        _safe_send(user.email, subject, body)


def send_new_message_email_if_unread_streak(sender_profile, receiver_profile):
    """
    Send a message email only when this is the *first* unread message
    in a streak from this sender to this receiver.

    Logic:
      - If receiver has >1 unread messages from `sender_profile`, we skip.
      - When they open the chat, your view already marks them all as read,
        so the next time they go away and get a new message, they’ll get
        one new email again.
    """
    user = receiver_profile.user
    if not user.email:
        return

    # Count unread messages from this sender to this receiver
    unread_from_sender = Message.objects.filter(
        sender=sender_profile,
        receiver=receiver_profile,
        is_read=False,
    ).count()

    if unread_from_sender != 1:
        # Either 0 (no need) or >1 (we already emailed once this streak)
        return

    receiver_name = receiver_profile.name or user.first_name or "there"
    sender_name = sender_profile.name or "Someone"

    subject = "You have a new message on Turtle 🐢💬"
    body = (
        f"Hi {receiver_name},\n\n"
        f"{sender_name} just sent you a message on Turtle.\n"
        "Open Turtle to read it and reply.\n\n"
        "Log in here:\n"
        "https://turtleapp.co/accounts/login/\n\n"
        "Slowly,\n"
        "Turtle 🐢\n"
    )
    _safe_send(user.email, subject, body)
