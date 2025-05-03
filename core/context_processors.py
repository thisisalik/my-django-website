from .models import Match, Message, LetterLike

def global_notifications(request):
    if not request.user.is_authenticated:
        return {}

    profile = getattr(request.user, 'profile', None)
    if not profile:
        return {}

    # 📨 Unread messages
    unread_messages_count = Message.objects.filter(
        receiver=profile,
        is_read=False
    ).count()

    # 💘 Unseen matches
    unseen_matches_count = Match.objects.filter(
        user1=profile,
        is_seen_by_user1=False
    ).count() + Match.objects.filter(
        user2=profile,
        is_seen_by_user2=False
    ).count()

    # 🐢 Likes not yet answered
    liked_you_profiles = LetterLike.objects.filter(
        to_letter__profile=profile,
        liked=True
    ).exclude(
        from_profile__in=LetterLike.objects.filter(from_profile=profile)
            .values_list('to_letter__profile', flat=True)
    )

    new_likes_count = liked_you_profiles.count()

    return {
        'unread_messages_count': unread_messages_count,
        'unseen_matches_count': unseen_matches_count,
        'new_likes_count': new_likes_count,
    }
