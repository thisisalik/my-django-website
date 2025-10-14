from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import Letter, LetterImage, Profile, LetterLike, Match, Message
from django.db.models import Q
from django.views.decorators.http import require_POST
import os
import time  
from django.conf import settings
from django.core.files import File
import mimetypes
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib import messages as dj_messages
import requests
from django.http import StreamingHttpResponse, HttpResponseNotFound, HttpResponseForbidden
from django.views.decorators.http import require_GET
import uuid  
from urllib.parse import urlparse
from cloudinary.utils import cloudinary_url

from .forms import (
    LetterForm,
    MessageForm,
    ProfileForm,
    LetterFilterForm,
    FullRegisterForm
)
from .models import Notification
from django.http import JsonResponse
from django.shortcuts import redirect

LETTER_MIN_CHARS = 200
LETTER_MAX_CHARS = 2000


@login_required
@require_GET
def letter_pdf_proxy(request, letter_id):
    """
    Stream a Cloudinary raw PDF through our domain using a short-lived **signed** URL.
    Order: signed 'upload' -> 'authenticated' -> 'private'.
    """
    letter = get_object_or_404(Letter, id=letter_id)
    if letter.letter_type != 'pdf' or not letter.pdf:
        return HttpResponseNotFound("Not a PDF")

    # authorize: owner or active match
    me = request.user.profile
    owner = letter.profile
    if not (me.id == owner.id or Match.objects.filter(active=True)
            .filter(Q(user1__in=[me, owner], user2__in=[me, owner])).exists()):
        return HttpResponseForbidden("Not allowed")

    # --- derive public_id, extension, and (optional) version from the stored URL ---
    path = urlparse(letter.pdf.url).path  # '/<cloud>/raw/upload/v1/media/letters/pdf/foo.pdf'
    version = None
    try:
        after_upload = path.split('/upload/')[1]   # 'v1/media/letters/pdf/foo.pdf' OR 'media/...'
        parts = after_upload.split('/')
        if parts and parts[0].startswith('v') and parts[0][1:].isdigit():
            version = parts[0][1:]                 # '1'
            parts = parts[1:]                      # drop version segment
        public_id_with_ext = '/'.join(parts)       # 'media/letters/pdf/foo.pdf'
    except Exception:
        public_id_with_ext = letter.pdf.name       # storage fallback

    public_id_no_ext, ext_dot = os.path.splitext(public_id_with_ext)
    ext = (ext_dot.lstrip('.') or 'pdf').lower()

    def build_signed_url(delivery_type: str) -> str:
        # For type='upload' you can sign the URL (required when "Require signed delivery" is on).
        # Note: 'expires_at' is supported for 'authenticated'/'private' but ignored for 'upload'.
        params = dict(
            resource_type="raw",
            type=delivery_type,
            format=ext,
            sign_url=True,
            secure=True,
        )
        if version:
            params["version"] = version
        if delivery_type in ("authenticated", "private"):
            params["expires_at"] = int(time.time()) + 300  # 5 minutes
        url, _ = cloudinary_url(public_id_no_ext, **params)
        return url

    # Try signed 'upload' first (matches how the asset was stored).
    for delivery_type in ("upload", "authenticated", "private"):
        signed = build_signed_url(delivery_type)
        r = requests.get(signed, stream=True, timeout=15)
        if r.status_code == 200:
            resp = StreamingHttpResponse(
                r.iter_content(8192),
                content_type=r.headers.get('Content-Type', 'application/pdf'),
            )
            filename = os.path.basename(public_id_no_ext) + '.' + ext
            resp['Content-Disposition'] = r.headers.get('Content-Disposition',
                                                        f'inline; filename="{filename}"')
            if 'Content-Length' in r.headers:
                resp['Content-Length'] = r.headers['Content-Length']
            resp['Cache-Control'] = 'private, max-age=3600'
            return resp

        # If unauthorized/not found, try next type; surface other errors immediately.
        if r.status_code not in (401, 403, 404):
            r.raise_for_status()

    # If all attempts failed, raise the last one
    r.raise_for_status()

@login_required
def home_redirect(request):
    return redirect('browse_letter') 
@login_required
def live_notifications(request):
    profile = request.user.profile
    active_chat_id = request.GET.get("active_chat_id")

    # ✅ active partners only
    active_pairs = Match.objects.filter(active=True).filter(
        Q(user1=profile) | Q(user2=profile)
    ).values_list('user1', 'user2')

    active_partner_ids = set()
    for u1, u2 in active_pairs:
        active_partner_ids.update([u1, u2])
    active_partner_ids.discard(profile.id)

    # ✅ only count unread from active partners
    unread_messages_qs = Message.objects.filter(
        receiver=profile,
        is_read=False,
        sender__id__in=active_partner_ids
    )

    # ✅ exclude currently open chat (unchanged)
    if active_chat_id:
        unread_messages_qs = unread_messages_qs.exclude(sender__id=active_chat_id)

    unread_messages_count = unread_messages_qs.count()

    # ✅ likes: keep your existing logic (unchanged)
    matched_profiles = Match.objects.filter(
        Q(user1=profile) | Q(user2=profile)
    ).values_list('user1', 'user2')

    matched_ids = set()
    for u1, u2 in matched_profiles:
        matched_ids.add(u1); matched_ids.add(u2)
    matched_ids.discard(profile.id)

    new_likes_count = LetterLike.objects.filter(
        to_letter__profile=profile,
        liked=True
    ).exclude(
        from_profile__in=LetterLike.objects.filter(from_profile=profile).values_list('to_letter__profile', flat=True)
    ).exclude(
        from_profile__id__in=matched_ids
    ).count()

    # ✅ unseen matches badge should also ignore inactive matches
    unseen_matches_count = Match.objects.filter(active=True).filter(
        Q(user1=profile, is_seen_by_user1=False) |
        Q(user2=profile, is_seen_by_user2=False)
    ).count()

    return JsonResponse({
        'new_likes_count': new_likes_count,
        'unread_messages_count': unread_messages_count,
        'unseen_matches_count': unseen_matches_count,
    })


@login_required
def browse_letter(request):
    profile = request.user.profile

    if not profile.letter_set.exists():
        return render(request, 'no_letter_uploaded.html')

    form = LetterFilterForm(request.GET or None)
    # Exclude own letters and letters from matched users
    matched_profiles = Match.objects.filter(
    Q(user1=profile) | Q(user2=profile)
    ).values_list('user1', 'user2')

    # Flatten and remove self
    matched_ids = set()
    for u1, u2 in matched_profiles:
        matched_ids.add(u1)
        matched_ids.add(u2)
    matched_ids.discard(profile.id)

    letters = Letter.objects.exclude(profile=profile).exclude(profile__id__in=matched_ids)

    if form.is_valid() and form.has_changed():
        gender = form.cleaned_data.get('gender')
        min_age = form.cleaned_data.get('min_age')
        max_age = form.cleaned_data.get('max_age')

        if gender:
            letters = letters.filter(profile__gender=gender)
        if min_age is not None:
            letters = letters.filter(profile__age__gte=min_age)
        if max_age is not None:
            letters = letters.filter(profile__age__lte=max_age)
    else:
        if profile.preferred_gender and profile.preferred_gender != "Any":
            letters = letters.filter(profile__gender=profile.preferred_gender)
        if profile.preferred_age_min:
            letters = letters.filter(profile__age__gte=profile.preferred_age_min)
        if profile.preferred_age_max:
            letters = letters.filter(profile__age__lte=profile.preferred_age_max)

    # ✅ Mutual same-city logic
        if profile.location:
            letters = letters.filter(
         Q(profile__only_same_city=False) | Q(profile__location__iexact=profile.location)
            )
            if profile.only_same_city:
                letters = letters.filter(profile__location__iexact=profile.location)
    # ✅ Exclude already liked/skipped
    seen_ids = LetterLike.objects.filter(from_profile=profile).values_list('to_letter_id', flat=True)
    letters = letters.exclude(id__in=seen_ids)

    # ✅ Match their preferences
    letters = letters.filter(
        profile__preferred_gender__in=["Any", profile.gender, None]
    ).filter(
        profile__preferred_age_min__lte=profile.age if profile.age else 200,
        profile__preferred_age_max__gte=profile.age if profile.age else 0
    )

    # ✅ Filter by connection type (Python-side, safe on all DBs)
    if profile.connection_types:
        letters = [l for l in letters if set(l.profile.connection_types or []) & set(profile.connection_types or [])]

        # ✅ Order letters: same city first, then others (if user allows it)
    if isinstance(letters, list):
        # Already a Python list (after connection type filter)
        same_city_letters = [l for l in letters if l.profile.location and l.profile.location.lower() == (profile.location or "").lower()]
        other_city_letters = [l for l in letters if l not in same_city_letters]
    else:
        same_city_letters = letters.filter(profile__location__iexact=profile.location)
        other_city_letters = letters.exclude(profile__location__iexact=profile.location)

    same_city_letters = sorted(same_city_letters, key=lambda l: l.created_at or l.id, reverse=True)
    other_city_letters = sorted(other_city_letters, key=lambda l: l.created_at or l.id, reverse=True)

    # ✅ Combine
    ordered_letters = list(same_city_letters) + list(other_city_letters)

    # ✅ Pick the first
    letter = ordered_letters[0] if ordered_letters else None

    # Counts
    unread_messages_count = Message.objects.filter(receiver=profile, is_read=False).count()
    unseen_matches_count = Match.objects.filter(
        Q(user1=profile, is_seen_by_user1=False) |
        Q(user2=profile, is_seen_by_user2=False)
    ).count()

    return render(request, 'browse_letter.html', {
        'letter': letter,
        'form': form,
        'unread_messages_count': unread_messages_count,
        'unseen_matches_count': unseen_matches_count,
    })



# 🧠 React to a Letter
@login_required
def react_to_letter(request, letter_id):
    profile = request.user.profile
    letter = get_object_or_404(Letter, id=letter_id)
    liked = request.POST.get('liked') == 'true'

    LetterLike.objects.create(from_profile=profile, to_letter=letter, liked=liked)

    if liked:
        reverse_like = LetterLike.objects.filter(
            from_profile=letter.profile,
            to_letter__profile=profile,
            liked=True
        ).exists()

        if reverse_like:
            if not Match.objects.filter(user1__in=[profile, letter.profile], user2__in=[profile, letter.profile]).exists():
                Match.objects.create(user1=profile, user2=letter.profile)

    return redirect('browse_letter')

@login_required
def upload_letter(request):
    profile = request.user.profile

    # If there is already a usable letter, send them to the profile
    existing = Letter.objects.filter(profile=profile).first()
    if existing:
        usable = (
            (existing.letter_type == 'text' and bool(existing.text_content)) or
            (existing.letter_type == 'pdf' and bool(existing.pdf)) or
            (existing.letter_type == 'image' and
             LetterImage.objects.filter(letter=existing).exists())
        )
        if usable:
            return redirect('view_profile')
        # empty image-letter -> delete silently, no flash
        if existing.letter_type == 'image':
            existing.delete()

    if request.method == 'POST':
        form = LetterForm(request.POST, request.FILES)

        # Require a letter type (your form sets required=False)
        lt = (request.POST.get('letter_type') or '').strip()
        if not lt:
            form.add_error('letter_type', "❌ Please pick a letter type.")
            return render(request, 'upload_letter.html', {'form': form})

        # Let the form enforce all other rules (200–2000, pdf, images, etc.)
        if not form.is_valid():
            return render(request, 'upload_letter.html', {'form': form})

        # Create the letter
        if lt == 'text':
            text = (form.cleaned_data.get('text_content') or '').strip()
            Letter.objects.create(profile=profile, letter_type='text', text_content=text)

        elif lt == 'pdf':
            pdf = form.cleaned_data.get('pdf')
            Letter.objects.create(profile=profile, letter_type='pdf', pdf=pdf)

        elif lt == 'image':
            letter = Letter.objects.create(profile=profile, letter_type='image')
            for img in request.FILES.getlist('images'):
                # form.clean already checked these are images
                LetterImage.objects.create(letter=letter, image=img)

        # No success flash; just go back
        return redirect('view_profile')

    # GET
    form = LetterForm()
    return render(request, 'upload_letter.html', {'form': form})

# 🧠 View Matches
@login_required
def view_matches(request):
    profile = request.user.profile
    matches = Match.objects.filter(user1=profile) | Match.objects.filter(user2=profile)

    matched_profiles = []
    for match in matches:
        matched_profiles.append(match.user2 if match.user1 == profile else match.user1)

    return render(request, 'matches.html', {'matches': matched_profiles})

from django.db.models import Q  # (you already have this import above)

@login_required
def message_view(request, profile_id):
    sender = request.user.profile
    receiver = get_object_or_404(Profile, id=profile_id)

    # ✅ Only allow chatting if there's an ACTIVE match
    matched = Match.objects.filter(active=True).filter(
        Q(user1__in=[sender, receiver], user2__in=[sender, receiver])
    ).exists()

    if not matched:
        return HttpResponseForbidden("You can only message people you've matched with.")

    # ✅ Mark all messages received from this person as read
    Message.objects.filter(
        sender=receiver,
        receiver=sender,
        is_read=False
    ).update(is_read=True)

    messages_qs = Message.objects.filter(
        sender__in=[sender, receiver],
        receiver__in=[sender, receiver]
    ).order_by('timestamp')

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = sender
            message.receiver = receiver
            message.save()
            return redirect('message_view', profile_id=receiver.id)
    else:
        form = MessageForm()

    return render(request, 'messages.html', {'receiver': receiver, 'messages': messages_qs, 'form': form})

@login_required
def edit_profile(request):
    profile = request.user.profile
    letters = Letter.objects.filter(profile=profile)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        letter_form = LetterForm(request.POST, request.FILES)

        had_letter_error = False  # block redirect if any letter error

        # -- save profile (same as before) --
        if form.is_valid():
            p = form.save(commit=False)
            p.connection_types = request.POST.getlist('connection_types')
            p.save()
        # if profile form invalid, we'll re-render at bottom

        # -- edits to EXISTING text letters: require 200..2000 --
        for letter in letters.filter(letter_type='text'):
            key = f'text_content_{letter.id}'
            new_text = (request.POST.get(key) or '').strip()
            if new_text:
                if len(new_text) < LETTER_MIN_CHARS or len(new_text) > LETTER_MAX_CHARS:
                    had_letter_error = True
                    # put the error on the add-letter form as a non-field error so it shows under that section
                    letter_form.add_error(
                        None,
                        f"❌ Letter text must be between {LETTER_MIN_CHARS} and {LETTER_MAX_CHARS} characters."
                    )
                else:
                    letter.text_content = new_text
                    letter.save()

        # -- image deletes / adds (unchanged) --
        delete_ids_str = request.POST.get('delete_image_ids', '')
        if delete_ids_str:
            delete_ids = [int(i) for i in delete_ids_str.split(',') if i.isdigit()]
            LetterImage.objects.filter(id__in=delete_ids, letter__profile=profile).delete()

        for letter in letters.filter(letter_type='image'):
            if not letter.images.exists():
                letter.delete()

        for letter in letters.filter(letter_type='image'):
            for img in request.FILES.getlist('images'):
                LetterImage.objects.create(letter=letter, image=img)

        # -- NEW letter creation (uses LetterForm.clean to enforce 200..2000) --
        attempted = any([
            request.POST.get('letter_type'),
            (request.POST.get('text_content') or '').strip(),
            bool(request.FILES.get('pdf')),
            bool(request.FILES.getlist('images')),
        ])

        if attempted:
            if letter_form.is_valid():
                lt = letter_form.cleaned_data.get('letter_type')
                text_content = (letter_form.cleaned_data.get('text_content') or '').strip()
                pdf = letter_form.cleaned_data.get('pdf')
                images = request.FILES.getlist('images')

                if lt == 'text':
                    Letter.objects.create(profile=profile, letter_type='text', text_content=text_content)
                elif lt == 'pdf':
                    Letter.objects.create(profile=profile, letter_type='pdf', pdf=pdf)
                elif lt == 'image':
                    new_letter = Letter.objects.create(profile=profile, letter_type='image')
                    for img in images:
                        LetterImage.objects.create(letter=new_letter, image=img)
            else:
                had_letter_error = True
                # keep errors on the form; no flash messages

        # -- redirect only when everything is valid --
        if form.is_valid() and not had_letter_error:
            # no success flash here (you said you don't want green messages)
            return redirect('view_profile')

    else:
        form = ProfileForm(instance=profile)
        letter_form = LetterForm()

    ages = range(18, 101)
    only_image_letter = (
        letters.count() == 1 and
        letters.first().letter_type == 'image' and
        letters.first().images.exists()
    )

    unread_messages_count = Message.objects.filter(receiver=profile, is_read=False).count()
    unseen_matches_count = Match.objects.filter(
        Q(user1=profile, is_seen_by_user1=False) |
        Q(user2=profile, is_seen_by_user2=False)
    ).count()

    return render(request, 'edit_profile.html', {
        'form': form,
        'letter_form': letter_form,  # make sure template can show its errors
        'letters': letters,
        'unread_messages_count': unread_messages_count,
        'unseen_matches_count': unseen_matches_count,
        'upload_slots': range(5),
        'ages': ages,
        'only_image_letter': only_image_letter,
    })


def _save_temp_profile_picture(uploaded_file):
    """Save uploaded image to MEDIA_ROOT/tmp_reg and return relative path 'tmp_reg/<filename>'."""
    temp_dir = os.path.join(settings.MEDIA_ROOT, 'tmp_reg')
    os.makedirs(temp_dir, exist_ok=True)

    _, ext = os.path.splitext(uploaded_file.name)
    fname = f"{uuid.uuid4().hex}{ext.lower()}"
    rel_path = os.path.join('tmp_reg', fname)
    abs_path = os.path.join(settings.MEDIA_ROOT, rel_path)

    with open(abs_path, 'wb+') as dst:
        for chunk in uploaded_file.chunks():
            dst.write(chunk)
    return rel_path  # e.g. 'tmp_reg/abc123.jpg'

from django.contrib.auth import login
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files import File
import mimetypes, os
# keep your existing imports (uuid, settings, etc.)

LETTER_MIN_CHARS = 200
LETTER_MAX_CHARS = 2000

def register(request):
    ages = range(18, 101)

    if request.method == 'POST':
        temp_profile_picture = (request.POST.get('temp_profile_picture') or '').strip() or None

        if temp_profile_picture and 'profile_picture' not in request.FILES:
            abs_temp = os.path.join(settings.MEDIA_ROOT, temp_profile_picture)
            if os.path.exists(abs_temp):
                ctype, _ = mimetypes.guess_type(abs_temp)
                if not ctype:
                    ctype = 'application/octet-stream'
                with open(abs_temp, 'rb') as f:
                    data = f.read()
                request.FILES['profile_picture'] = SimpleUploadedFile(
                    name=os.path.basename(abs_temp),
                    content=data,
                    content_type=ctype
                )

        form = FullRegisterForm(request.POST, request.FILES)

        if not form.is_valid():
            uploaded = request.FILES.get('profile_picture')
            if uploaded:
                try:
                    temp_profile_picture = _save_temp_profile_picture(uploaded)
                except Exception:
                    temp_profile_picture = None
            if temp_profile_picture:
                form.fields['profile_picture'].required = False
                form.fields['profile_picture'].widget.attrs.pop('required', None)
            messages.error(request, form.errors)
            return render(request, 'register.html',
                          {'form': form, 'ages': ages, 'temp_profile_picture': temp_profile_picture})

        # --- letter validation BEFORE saving user ---
        skip_letter = request.POST.get('skip_letter') in ('1', 'on', 'true', 'True')
        letter_type = form.cleaned_data.get('letter_type')
        text_content = (form.cleaned_data.get('text_content') or '').strip()
        pdf = request.FILES.get('pdf')
        images = request.FILES.getlist('images')

        if not skip_letter and letter_type:
            if letter_type == 'text':
                if not text_content:
                    messages.error(request, "❌ Please write your letter text.")
                    return render(request, 'register.html', {'form': form, 'ages': ages, 'temp_profile_picture': temp_profile_picture})
                if len(text_content) < LETTER_MIN_CHARS:
                    messages.error(request, f"❌ Letter text must be at least {LETTER_MIN_CHARS} characters.")
                    return render(request, 'register.html', {'form': form, 'ages': ages, 'temp_profile_picture': temp_profile_picture})
                if len(text_content) > LETTER_MAX_CHARS:
                    messages.error(request, f"❌ Letter text must be {LETTER_MAX_CHARS} characters or fewer.")
                    return render(request, 'register.html', {'form': form, 'ages': ages, 'temp_profile_picture': temp_profile_picture})

            elif letter_type == 'pdf':
                if not pdf:
                    messages.error(request, "❌ Please choose a PDF file.")
                    return render(request, 'register.html', {'form': form, 'ages': ages, 'temp_profile_picture': temp_profile_picture})
                ct = (pdf.content_type or '').lower()
                if not (ct == 'application/pdf' or pdf.name.lower().endswith('.pdf')):
                    messages.error(request, "❌ Selected file is not a PDF. Please choose a .pdf file.")
                    return render(request, 'register.html', {'form': form, 'ages': ages, 'temp_profile_picture': temp_profile_picture})

            elif letter_type == 'image':
                if not images:
                    messages.error(request, "❌ Please choose at least one image.")
                    return render(request, 'register.html', {'form': form, 'ages': ages, 'temp_profile_picture': temp_profile_picture})
                for f in images:
                    ct = (f.content_type or '').lower()
                    if not (ct.startswith('image/') or f.name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif'))):
                        messages.error(request, "❌ Only image files are allowed for an Image letter.")
                        return render(request, 'register.html', {'form': form, 'ages': ages, 'temp_profile_picture': temp_profile_picture})

        # --- now safe to create user ---
        user = form.save(commit=False)
        user.username = form.cleaned_data['email']
        user.email = form.cleaned_data['email']
        user.save()

        profile = user.profile
        profile.name = form.cleaned_data['name']
        profile.age = form.cleaned_data['age']
        profile.gender = form.cleaned_data['gender']

        profile_picture = form.cleaned_data.get('profile_picture')
        if profile_picture:
            profile.profile_picture = profile_picture
        elif temp_profile_picture:
            abs_temp = os.path.join(settings.MEDIA_ROOT, temp_profile_picture)
            if os.path.exists(abs_temp):
                with open(abs_temp, 'rb') as f:
                    profile.profile_picture.save(os.path.basename(abs_temp), File(f), save=False)
                try:
                    os.remove(abs_temp)
                except Exception:
                    pass

        profile.preferred_gender = form.cleaned_data.get('preferred_gender')
        profile.preferred_age_min = form.cleaned_data.get('preferred_age_min')
        profile.preferred_age_max = form.cleaned_data.get('preferred_age_max')
        profile.location = form.cleaned_data.get('location')
        profile.only_same_city = bool(form.cleaned_data.get('only_same_city'))
        profile.connection_types = request.POST.getlist('connection_types')
        profile.save()

        # --- save letter now ---
        if not skip_letter and letter_type:
            if letter_type == 'text':
                Letter.objects.create(profile=profile, letter_type='text', text_content=text_content)
            elif letter_type == 'pdf':
                Letter.objects.create(profile=profile, letter_type='pdf', pdf=pdf)
            elif letter_type == 'image':
                letter = Letter.objects.create(profile=profile, letter_type='image')
                for img in images:
                    ct = (img.content_type or '').lower()
                    if ct.startswith('image/') or img.name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif')):
                        LetterImage.objects.create(letter=letter, image=img)

        login(request, user)
        return redirect('browse_letter')

    else:
        form = FullRegisterForm()
        return render(request, 'register.html', {'form': form, 'ages': ages})

@login_required
def view_profile(request):
    profile = request.user.profile

    # ✅ Exclude image letters that have no images
    all_letters = Letter.objects.filter(profile=profile)
    letters = [l for l in all_letters if not (l.letter_type == 'image' and not l.images.exists())]
    has_letter = bool(letters)

    unread_messages_count = Message.objects.filter(receiver=profile, is_read=False).count()
    unseen_matches_count = Match.objects.filter(
        Q(user1=profile, is_seen_by_user1=False) |
        Q(user2=profile, is_seen_by_user2=False)
    ).count()

    return render(request, 'view_profile.html', {
        'profile': profile,
        'letters': letters,
        'has_letter': has_letter,
        'unread_messages_count': unread_messages_count,
        'unseen_matches_count': unseen_matches_count,
    })

@login_required
def edit_letter(request, letter_id):
    profile = request.user.profile
    letter = get_object_or_404(Letter, id=letter_id, profile=profile)

    if request.method == 'POST':
        if letter.letter_type == 'text':
            text = request.POST.get('text_content', '').strip()
            print(">>> SUBMITTED:", text)
            if not text:
                messages.error(request, "❌ Text cannot be empty.")
                return redirect('edit_letter', letter_id=letter.id)
            letter.text_content = text

        elif letter.letter_type == 'pdf':
            if 'pdf' in request.FILES:
                letter.pdf = request.FILES['pdf']

        # Save and confirm
        letter.save()
        messages.success(request, "✅ Letter updated successfully!")
        return redirect('view_profile')

    return render(request, 'edit_letter.html', {'letter': letter})

# 🧠 Delete Letter
@login_required
def delete_letter(request, letter_id):
    profile = request.user.profile
    letter = get_object_or_404(Letter, id=letter_id, profile=profile)
    if request.method == 'POST':
        letter.delete()
        messages.success(request, "✅ Letter deleted.")
        return redirect('view_profile')

    return render(request, 'confirm_delete_letter.html')

@login_required
def likes_received(request):
    profile = request.user.profile

    # Get matched profiles
    matched_profiles = Match.objects.filter(
    Q(user1=profile) | Q(user2=profile)
    ).values_list('user1', 'user2')

    matched_ids = set()
    for u1, u2 in matched_profiles:
        matched_ids.add(u1)
        matched_ids.add(u2)
    matched_ids.discard(profile.id)

    likes = LetterLike.objects.filter(
        to_letter__profile=profile,
        liked=True
    ).exclude(
        from_profile__in=LetterLike.objects.filter(from_profile=profile).values_list('to_letter__profile', flat=True)
    ).exclude(
        from_profile__id__in=matched_ids
    )


    # ✅ Count unread messages and unseen matches (for 💬 badge)
    unread_messages_count = Message.objects.filter(receiver=profile, is_read=False).count()
    unseen_matches_count = Match.objects.filter(
        Q(user1=profile, is_seen_by_user1=False) |
        Q(user2=profile, is_seen_by_user2=False)
    ).count()

    # ✅ Count new likes (for 🐢 badge)
    new_likes_count = likes.count()

    return render(request, 'likes_received.html', {
        'likes': likes,
        'unread_messages_count': unread_messages_count,
        'unseen_matches_count': unseen_matches_count,
        'new_likes_count': new_likes_count,
    })

@login_required
def like_back(request, profile_id):
    my_profile = request.user.profile
    other_profile = get_object_or_404(Profile, id=profile_id)

    their_letter = other_profile.letter_set.order_by('-created_at').first()
    if their_letter:
        # ✅ Create the like
        LetterLike.objects.create(from_profile=my_profile, to_letter=their_letter, liked=True)

        # ✅ Check for reverse like to form a match
        reverse_like_exists = LetterLike.objects.filter(
            from_profile=other_profile,
            to_letter__profile=my_profile,
            liked=True
        ).exists()

        if reverse_like_exists:
            if not Match.objects.filter(user1__in=[my_profile, other_profile], user2__in=[my_profile, other_profile]).exists():
                Match.objects.create(user1=my_profile, user2=other_profile)

    return redirect('likes_received')

@login_required
def reject_like(request, profile_id):
    my_profile = request.user.profile
    other_profile = get_object_or_404(Profile, id=profile_id)

    their_letter = other_profile.letter_set.order_by('-created_at').first()
    if their_letter:
        LetterLike.objects.create(from_profile=my_profile, to_letter=their_letter, liked=False)

    return redirect('likes_received')

# 🧠 Unmatch View
@login_required
def unmatch(request, profile_id):
    my_profile = request.user.profile
    other_profile = get_object_or_404(Profile, id=profile_id)

    Match.objects.filter(user1__in=[my_profile, other_profile], user2__in=[my_profile, other_profile]).delete()
    Message.objects.filter(sender__in=[my_profile, other_profile], receiver__in=[my_profile, other_profile]).delete()

    return redirect('view_matches')

@login_required
def delete_letter_image(request, image_id):
    image = get_object_or_404(LetterImage, id=image_id, letter__profile=request.user.profile)
    letter = image.letter

    image.delete()

    if letter.letter_type == "image" and not letter.images.exists():
        letter.delete()

    # 🧠 Redirect back to Edit Profile page instead of View Profile
    return redirect('edit_profile')


# 🧠 Add More Images
@login_required
def add_letter_images(request, letter_id):
    profile = request.user.profile
    letter = get_object_or_404(Letter, id=letter_id, profile=profile)

    if letter.letter_type != 'image':
        messages.error(request, "❌ Only image letters can have additional images.")
        return redirect('edit_profile')

    if request.method == 'POST':
        for img in request.FILES.getlist('images'):
            LetterImage.objects.create(letter=letter, image=img)
        messages.success(request, "✅ Images added successfully!")
        return redirect('edit_profile')

    return render(request, 'add_images.html', {'letter': letter})

@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'notifications.html', {'notifications': notifications})

@login_required
def matched_profile_view(request, profile_id):
    matched_profile = get_object_or_404(Profile, id=profile_id)
    viewer_profile = request.user.profile

    # Find the match (same logic, unchanged)
    match = Match.objects.filter(
        user1__in=[viewer_profile, matched_profile],
        user2__in=[viewer_profile, matched_profile]
    ).first()

    # Mark seen (unchanged)
    if match:
        if match.user1 == viewer_profile and not match.is_seen_by_user1:
            match.is_seen_by_user1 = True
            match.save()
        elif match.user2 == viewer_profile and not match.is_seen_by_user2:
            match.is_seen_by_user2 = True
            match.save()

    letter = matched_profile.letter_set.order_by('-created_at').first()

    # ✅ Pass `match` to the template (the only addition)
    return render(
        request,
        'matched_profile.html',
        {'profile': matched_profile, 'letter': letter, 'match': match}
    )

from django.utils import timezone
from django.db.models import Q

@login_required
def chat_list_partial_view(request):
    return chat_list_view(request, partial=True)

@login_required
def chat_list_view(request, partial=False):
    profile = request.user.profile

    # ✅ Only active matches
    matches = Match.objects.filter(active=True).filter(
        Q(user1=profile) | Q(user2=profile)
    )

    matched_profiles = [m.user2 if m.user1 == profile else m.user1 for m in matches]

    unread_senders = set(
        Message.objects.filter(receiver=profile, is_read=False)
        .values_list('sender_id', flat=True)
    )

    profiles_with_data = []
    for m in matched_profiles:
        m.has_unread = m.id in unread_senders

        last_msg = Message.objects.filter(
            sender__in=[profile, m],
            receiver__in=[profile, m]
        ).order_by('-timestamp').first()

        m.last_message = last_msg.text if last_msg else ""
        m.last_message_time = last_msg.timestamp if last_msg else None
        m.is_new_match = last_msg is None

        profiles_with_data.append(m)

    from django.utils import timezone
    far_future = timezone.now() + timezone.timedelta(days=365 * 100)

    profiles_with_data.sort(
        key=lambda p: p.last_message_time if p.last_message_time is not None else far_future,
        reverse=True
    )

    context = {
        'matches': profiles_with_data,
        'unread_messages_count': len(unread_senders),
        # (Optional) also count only active unseen matches so badges ignore unmatched ones
        'unseen_matches_count': Match.objects.filter(
            active=True
        ).filter(
            Q(user1=profile, is_seen_by_user1=False) |
            Q(user2=profile, is_seen_by_user2=False)
        ).count()
    }

    if partial:
        return render(request, 'partial_chat_list.html', context)
    else:
        return render(request, 'chat_list.html', context)


@login_required
@require_POST
def unmatch(request, match_id):
    viewer_profile = request.user.profile
    match = get_object_or_404(Match, id=match_id)

    if match.user1 != viewer_profile and match.user2 != viewer_profile:
        messages.error(request, "You’re not part of this match.")
        return redirect('chat_list')

    if match.active:
        match.active = False
        match.unmatched_at = timezone.now()
        match.unmatched_by = viewer_profile
        match.save()

        # ✅ Determine the other party
        other_profile = match.user2 if match.user1 == viewer_profile else match.user1

        # ✅ Important: mark any unread incoming msgs as read so badges clear
        Message.objects.filter(
            sender=other_profile,
            receiver=viewer_profile,
            is_read=False
        ).update(is_read=True)

        messages.success(request, "You’ve unmatched.")
    else:
        messages.info(request, "This match is already closed.")

    return redirect('chat_list')

@login_required
def fetch_messages(request, profile_id):
    sender = request.user.profile
    receiver = get_object_or_404(Profile, id=profile_id)

    matched = Match.objects.filter(
        user1__in=[sender, receiver],
        user2__in=[sender, receiver]
    ).exists()

    if not matched:
        return HttpResponseForbidden("Unauthorized")

    messages_qs = Message.objects.filter(
        sender__in=[sender, receiver],
        receiver__in=[sender, receiver]
    ).order_by('timestamp')

    return render(request, 'partial_messages.html', {'messages': messages_qs})

from django.contrib.auth.views import LoginView

class CustomLoginView(LoginView):
    def form_valid(self, form):
        remember_me = self.request.POST.get('remember_me')

        # ✅ Set session expiry BEFORE calling parent logic
        if not remember_me:
            self.request.session.set_expiry(0)  # expires on browser close
        else:
            self.request.session.set_expiry(60 * 60 * 24 * 14)  # 2 weeks

        # 🧠 Now let Django handle login and redirect
        return super().form_valid(form)
    
