from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import Letter, LetterImage, Profile, LetterLike, Match, Message
from .forms import (
    LetterForm,
    MessageForm,
    ProfileForm,
    LetterFilterForm,
    FullRegisterForm
)

# 🧠 Browse Letters
@login_required
def browse_letter(request):
    profile = request.user.profile

    if not profile.letter_set.exists():
        return render(request, 'no_letter_uploaded.html')

    form = LetterFilterForm(request.GET or None)
    letters = Letter.objects.exclude(profile=profile)

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

    seen_ids = LetterLike.objects.filter(from_profile=profile).values_list('to_letter_id', flat=True)
    letters = letters.exclude(id__in=seen_ids)

    letter = letters.first()

    if not letter:
        return render(request, 'no_more_letters.html', {'form': form})

    return render(request, 'browse_letter.html', {'letter': letter, 'form': form})

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

    if Letter.objects.filter(profile=profile).exists():
        return redirect('view_profile')

    if request.method == 'POST':
        form = LetterForm(request.POST, request.FILES)
        if form.is_valid():
            letter = form.save(commit=False)
            letter.profile = profile
            letter.save()

            # Save uploaded images separately
            if letter.letter_type == 'image':
                for img in request.FILES.getlist('images'):
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

# 🧠 Message View
@login_required
def message_view(request, profile_id):
    sender = request.user.profile
    receiver = get_object_or_404(Profile, id=profile_id)

    matched = Match.objects.filter(
        user1__in=[sender, receiver],
        user2__in=[sender, receiver]
    ).exists()

    if not matched:
        return HttpResponseForbidden("You can only message people you've matched with.")

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

# 🧠 Edit Profile
@login_required
def edit_profile(request):
    profile = request.user.profile
    letters = Letter.objects.filter(profile=profile)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('view_profile')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'edit_profile.html', {'form': form, 'letters': letters})

# 🧠 Register View
def register(request):
    if request.method == 'POST':
        form = FullRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            user.username = form.cleaned_data['name']
            user.email = form.cleaned_data['email']
            user.save()

            profile = user.profile
            profile.age = form.cleaned_data['age']
            profile.gender = form.cleaned_data['gender']
            profile.profile_picture = form.cleaned_data.get('profile_picture')
            profile.preferred_gender = form.cleaned_data.get('preferred_gender')
            profile.preferred_age_min = form.cleaned_data.get('preferred_age_min')
            profile.preferred_age_max = form.cleaned_data.get('preferred_age_max')
            profile.save()

            letter_type = form.cleaned_data.get('letter_type')
            if letter_type:
                Letter.objects.create(
                    profile=profile,
                    letter_type=letter_type,
                    text_content=form.cleaned_data.get('text_content', ''),
                    pdf=form.cleaned_data.get('pdf')
                )

            login(request, user)
            return redirect('browse_letter')
    else:
        form = FullRegisterForm()

    return render(request, 'register.html', {'form': form})

# 🧠 View Profile
@login_required
def view_profile(request):
    profile = request.user.profile
    letters = Letter.objects.filter(profile=profile)
    has_letter = letters.exists()

    return render(request, 'view_profile.html', {
        'profile': profile,
        'letters': letters,
        'has_letter': has_letter,
    })

@login_required
def edit_letter(request, letter_id):
    profile = request.user.profile
    letter = get_object_or_404(Letter, id=letter_id, profile=profile)

    if request.method == 'POST':
        form = LetterForm(request.POST, request.FILES, instance=letter)

        if form.is_valid():
            edited_letter = form.save(commit=False)

            # ✅ VERY IMPORTANT: Set the letter_type if it’s missing!
            if not edited_letter.letter_type:
                edited_letter.letter_type = 'text'

            if edited_letter.letter_type == 'text':
                new_text = form.cleaned_data.get('text_content')
                if new_text:
                    edited_letter.text_content = new_text
                else:
                    messages.error(request, "❌ Text cannot be empty.")
                    return redirect('edit_letter', letter_id=letter.id)

            elif edited_letter.letter_type == 'pdf':
                new_pdf = form.cleaned_data.get('pdf')
                if new_pdf:
                    edited_letter.pdf = new_pdf

            edited_letter.save()

            messages.success(request, "✅ Letter updated successfully!")
            return redirect('view_profile')
        else:
            messages.error(request, "❌ Please correct the errors.")
    else:
        form = LetterForm(instance=letter)

    return render(request, 'edit_letter.html', {'form': form, 'letter': letter})

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

# 🧠 Likes System
@login_required
def likes_received(request):
    profile = request.user.profile

    likes = LetterLike.objects.filter(
        to_letter__profile=profile,
        liked=True
    ).exclude(
        from_profile__in=LetterLike.objects.filter(from_profile=profile).values_list('to_letter__profile', flat=True)
    )

    return render(request, 'likes_received.html', {'likes': likes})

@login_required
def like_back(request, profile_id):
    my_profile = request.user.profile
    other_profile = get_object_or_404(Profile, id=profile_id)

    their_letter = other_profile.letter_set.order_by('-created_at').first()
    if their_letter:
        LetterLike.objects.create(from_profile=my_profile, to_letter=their_letter, liked=True)

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
