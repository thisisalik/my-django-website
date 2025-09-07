from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import Letter, LetterImage, Profile, LetterLike, Match, Message
from django.db.models import Q
from django.views.decorators.http import require_POST

import uuid  
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

@login_required
def home_redirect(request):
    return redirect('browse_letter') 
@login_required
def live_notifications(request):
    profile = request.user.profile
    active_chat_id = request.GET.get("active_chat_id")

    unread_messages_qs = Message.objects.filter(receiver=profile, is_read=False)

    # ✅ Exclude messages from currently active chat
    if active_chat_id:
        unread_messages_qs = unread_messages_qs.exclude(sender__id=active_chat_id)

    unread_messages_count = unread_messages_qs.count()

    # Exclude matched users from like count
    matched_profiles = Match.objects.filter(
        Q(user1=profile) | Q(user2=profile)
    ).values_list('user1', 'user2')

    matched_ids = set()
    for u1, u2 in matched_profiles:
        matched_ids.add(u1)
        matched_ids.add(u2)
    matched_ids.discard(profile.id)

    new_likes_count = LetterLike.objects.filter(
    to_letter__profile=profile,
    liked=True
    ).exclude(
    from_profile__in=LetterLike.objects.filter(from_profile=profile).values_list('to_letter__profile', flat=True)
    ).exclude(
        from_profile__id__in=matched_ids
    ).count()


    unseen_matches_count = Match.objects.filter(
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

    existing_letter = Letter.objects.filter(profile=profile).first()

    # ✅ Redirect only if a usable letter exists
    if existing_letter:
        if existing_letter.letter_type == 'text' and existing_letter.text_content:
            return redirect('view_profile')
        if existing_letter.letter_type == 'pdf' and existing_letter.pdf:
            return redirect('view_profile')
        if existing_letter.letter_type == 'image':
            # Only block if the letter *still has* images
            if LetterImage.objects.filter(letter=existing_letter).exists():
                return redirect('view_profile')
            else:
                existing_letter.delete()
                messages.info(request, "Previous empty letter cleared. You can upload a new one.")

    # ✅ Handle letter creation
    if request.method == 'POST':
        form = LetterForm(request.POST, request.FILES)

        # ---- strict validation per selected type ----
        lt = request.POST.get('letter_type')
        text_content = (request.POST.get('text_content') or '').strip()
        pdf = request.FILES.get('pdf')
        images = request.FILES.getlist('images')

        if lt == 'text':
            if not text_content:
                messages.error(request, "❌ Text letter cannot be empty.")
                return render(request, 'upload_letter.html', {'form': form})

        elif lt == 'pdf':
            if not pdf:
                messages.error(request, "❌ Please choose a PDF file.")
                return render(request, 'upload_letter.html', {'form': form})
            ct = (pdf.content_type or '').lower()
            if not (ct == 'application/pdf' or pdf.name.lower().endswith('.pdf')):
                messages.error(request, "❌ Selected file is not a PDF. Please choose a .pdf file.")
                return render(request, 'upload_letter.html', {'form': form})

        elif lt == 'image':
            if not images:
                messages.error(request, "❌ Please upload at least one image for an image letter.")
                return render(request, 'upload_letter.html', {'form': form})
            for f in images:
                ct = (f.content_type or '').lower()
                if not (ct.startswith('image/') or f.name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif'))):
                    messages.error(request, "❌ Only image files are allowed for an Image letter.")
                    return render(request, 'upload_letter.html', {'form': form})
        else:
            messages.error(request, "❌ Please pick a letter type.")
            return render(request, 'upload_letter.html', {'form': form})

        # ---- save like before ----
        if form.is_valid():
            if lt == 'text':
                Letter.objects.create(profile=profile, letter_type='text', text_content=text_content)

            elif lt == 'pdf':
                Letter.objects.create(profile=profile, letter_type='pdf', pdf=pdf)

            elif lt == 'image':
                letter = Letter.objects.create(profile=profile, letter_type='image')
                for img in images:
                    # double-guard (skip non-images silently)
                    ct = (img.content_type or '').lower()
                    if ct.startswith('image/') or img.name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif')):
                        LetterImage.objects.create(letter=letter, image=img)

            messages.success(request, "✅ Letter uploaded successfully!")
            return redirect('view_profile')
        else:
            messages.error(request, "❌ Please correct the errors below.")
    else:
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

        if form.is_valid():
            profile = form.save(commit=False)

            # ✅ Fix: preserve selected connection types
            profile.connection_types = request.POST.getlist('connection_types')
            profile.save()

            for letter in letters.filter(letter_type='text'):
                text_key = f'text_content_{letter.id}'
                new_text = request.POST.get(text_key, '').strip()
                if new_text:
                    letter.text_content = new_text
                    letter.save()

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

            if letter_form.is_valid():
                letter_type = letter_form.cleaned_data.get('letter_type')
                text_content = letter_form.cleaned_data.get('text_content', '').strip()
                pdf = letter_form.cleaned_data.get('pdf')
                images = request.FILES.getlist('images')

                if letter_type and (text_content or pdf or images):
                    letter = Letter.objects.create(
                        profile=profile,
                        letter_type=letter_type,
                        text_content=text_content,
                        pdf=pdf
                    )

                    if letter_type == 'image':
                        for img in images:
                            LetterImage.objects.create(letter=letter, image=img)

            messages.success(request, "✅ Profile updated successfully!")
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
        'letter_form': letter_form,
        'letters': letters,
        'unread_messages_count': unread_messages_count,
        'unseen_matches_count': unseen_matches_count,
        'upload_slots': range(5),
        'ages': ages,
        'only_image_letter': only_image_letter,
    })


from django.contrib.auth import login
import uuid  # already in your code

def register(request):
    ages = range(18, 101)

    if request.method == 'POST':
        form = FullRegisterForm(request.POST, request.FILES)
        if not form.is_valid():
            # 👇 keep your visibility helpers
            print("REGISTER FORM ERRORS:", form.errors.as_json())
            messages.error(request, form.errors)
            return render(request, 'register.html', {'form': form, 'ages': ages})

        if form.is_valid():
            user = form.save(commit=False)
            user.username = form.cleaned_data['email']
            user.email = form.cleaned_data['email']
            user.save()

            profile = user.profile
            profile.name = form.cleaned_data['name']
            profile.age = form.cleaned_data['age']
            profile.gender = form.cleaned_data['gender']
            profile.profile_picture = form.cleaned_data.get('profile_picture')
            profile.preferred_gender = form.cleaned_data.get('preferred_gender')
            profile.preferred_age_min = form.cleaned_data.get('preferred_age_min')
            profile.preferred_age_max = form.cleaned_data.get('preferred_age_max')
            profile.location = form.cleaned_data.get('location')
            profile.only_same_city = bool(form.cleaned_data.get('only_same_city'))
            profile.connection_types = request.POST.getlist('connection_types')
            profile.save()

            # ✅ NEW: respect "I'll upload later"
            skip_letter = request.POST.get('skip_letter') in ('1', 'on', 'true', 'True')

            # ---- strict validation for initial letter ----
            if not skip_letter:
                letter_type = form.cleaned_data.get('letter_type')
                text_content = (form.cleaned_data.get('text_content') or '').strip()
                pdf = request.FILES.get('pdf')
                images = request.FILES.getlist('images')

                if letter_type:
                    if letter_type == 'text':
                        if not text_content:
                            messages.error(request, "❌ Please write your letter text.")
                            return render(request, 'register.html', {'form': form, 'ages': ages})

                    elif letter_type == 'pdf':
                        if not pdf:
                            messages.error(request, "❌ Please choose a PDF file.")
                            return render(request, 'register.html', {'form': form, 'ages': ages})
                        ct = (pdf.content_type or '').lower()
                        if not (ct == 'application/pdf' or pdf.name.lower().endswith('.pdf')):
                            messages.error(request, "❌ Selected file is not a PDF. Please choose a .pdf file.")
                            return render(request, 'register.html', {'form': form, 'ages': ages})

                    elif letter_type == 'image':
                        if not images:
                            messages.error(request, "❌ Please choose at least one image.")
                            return render(request, 'register.html', {'form': form, 'ages': ages})
                        for f in images:
                            ct = (f.content_type or '').lower()
                            if not (ct.startswith('image/') or f.name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif'))):
                                messages.error(request, "❌ Only image files are allowed for an Image letter.")
                                return render(request, 'register.html', {'form': form, 'ages': ages})

                    # ---- create letter (same behavior as before) ----
                    if letter_type and (text_content or pdf or images):
                        letter = Letter.objects.create(
                            profile=profile,
                            letter_type=letter_type,
                            text_content=text_content if letter_type == 'text' else '',
                            pdf=pdf if letter_type == 'pdf' else None
                        )
                        if letter_type == 'image':
                            for img in images:
                                ct = (img.content_type or '').lower()
                                if ct.startswith('image/') or img.name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif')):
                                    LetterImage.objects.create(letter=letter, image=img)
            # if skipping: do nothing with letters

            login(request, user)
            return redirect('browse_letter')
        else:
            return render(request, 'register.html', {'form': form, 'ages': ages})
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
    
