# core/tests/test_core.py
import pytest
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import Profile, Letter, LetterImage, Match, Message

# ---------- helpers ----------

def ensure_profile(user, **overrides):
    """Get or create Profile and fill minimal fields so filters don't choke."""
    try:
        p = user.profile
    except Profile.DoesNotExist:
        p = Profile.objects.create(user=user)
    # sensible defaults
    p.name = p.name or user.username
    p.age = overrides.get("age", 25)
    p.gender = overrides.get("gender", "Male")
    p.location = overrides.get("location", "Munich")
    p.connection_types = overrides.get("connection_types", ["dating"])
    p.preferred_gender = overrides.get("preferred_gender", "Any")
    p.preferred_age_min = overrides.get("preferred_age_min", 18)
    p.preferred_age_max = overrides.get("preferred_age_max", 99)
    p.save()
    return p

def login(client, user):
    client.post("/accounts/login/", data={"username": user.username, "password": "pw", "remember_me": 1})

def mk_user(django_user_model, email):
    u = django_user_model.objects.create_user(username=email, email=email, password="pw")
    ensure_profile(u)
    return u

def pdf_file(name="x.pdf"):
    return SimpleUploadedFile(name, b"%PDF-1.4\n%", content_type="application/pdf")

def img_file(name="x.png"):
    # minimal PNG header is enough for tests
    return SimpleUploadedFile(name, b"\x89PNG\r\n\x1a\n", content_type="image/png")

# ---------- tests ----------

@pytest.mark.django_db
def test_upload_pdf_requires_real_pdf(client, django_user_model):
    """Letter type=pdf must have a .pdf file; image file should be rejected."""
    u = mk_user(django_user_model, "u1@test.com")
    login(client, u)

    url = reverse("upload_letter")

    # wrong: no file
    r = client.post(url, data={"letter_type": "pdf"})
    assert r.status_code == 200
    assert not Letter.objects.filter(profile=u.profile).exists()

    # wrong: image instead of pdf (pass file object in data)
    r = client.post(url, data={"letter_type": "pdf", "pdf": img_file()})
    assert r.status_code == 200
    assert not Letter.objects.filter(profile=u.profile).exists()

    # ok: proper pdf
    r = client.post(url, data={"letter_type": "pdf", "pdf": pdf_file()})
    assert r.status_code in (302, 303)
    assert Letter.objects.filter(profile=u.profile, letter_type="pdf").count() == 1


@pytest.mark.django_db
def test_upload_image_requires_at_least_one_image(client, django_user_model):
    u = mk_user(django_user_model, "u2@test.com")
    login(client, u)
    url = reverse("upload_letter")

    # wrong: no images
    r = client.post(url, data={"letter_type": "image"})
    assert r.status_code == 200
    assert not Letter.objects.filter(profile=u.profile).exists()

    # ok: with one image (list of files in data)
    r = client.post(url, data={"letter_type": "image", "images": [img_file()]})
    assert r.status_code in (302, 303)
    L = Letter.objects.get(profile=u.profile, letter_type="image")
    assert L.images.count() == 1


@pytest.mark.django_db
def test_like_then_mutual_like_creates_single_match(client, django_user_model):
    """Mutual likes create exactly one match; no duplicates."""
    # A & B with text letters
    A = mk_user(django_user_model, "a@test.com")
    B = mk_user(django_user_model, "b@test.com")
    Letter.objects.create(profile=A.profile, letter_type="text", text_content="A's letter")
    LB = Letter.objects.create(profile=B.profile, letter_type="text", text_content="B's letter")

    # A likes B
    login(client, A)
    client.post(reverse("react_to_letter", args=[LB.id]), data={"liked": "true"})

    # B likes A (mutual)
    client.post("/accounts/logout/")
    login(client, B)
    LA = Letter.objects.get(profile=A.profile)
    client.post(reverse("react_to_letter", args=[LA.id]), data={"liked": "true"})

    assert Match.objects.count() == 1  # exactly one match


@pytest.mark.django_db
def test_cannot_message_without_match(client, django_user_model):
    A = mk_user(django_user_model, "c@test.com")
    B = mk_user(django_user_model, "d@test.com")

    login(client, A)
    r = client.get(reverse("message_view", args=[B.profile.id]))
    assert r.status_code == 403  # forbidden by the view unless matched


@pytest.mark.django_db
def test_can_message_after_match_and_marks_read(client, django_user_model):
    """After mutual like, messaging works and messages persist."""
    A = mk_user(django_user_model, "e@test.com")
    B = mk_user(django_user_model, "f@test.com")
    LA = Letter.objects.create(profile=A.profile, letter_type="text", text_content="A")
    LB = Letter.objects.create(profile=B.profile, letter_type="text", text_content="B")

    # mutual like to create Match
    login(client, A)
    client.post(reverse("react_to_letter", args=[LB.id]), data={"liked": "true"})
    client.post("/accounts/logout/")
    login(client, B)
    client.post(reverse("react_to_letter", args=[LA.id]), data={"liked": "true"})
    assert Match.objects.count() == 1

    # B sends a message to A
    r = client.post(reverse("message_view", args=[A.profile.id]), data={"text": "hi!"})
    assert r.status_code in (302, 303)
    assert Message.objects.filter(sender=B.profile, receiver=A.profile, text="hi!").exists()
