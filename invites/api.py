from django.http import JsonResponse, HttpResponseNotAllowed

from authn.decorators.api import api
from club.exceptions import ApiAccessDenied
from common.api import API
from invites.models import Invite
from utils.strings import random_string


@api(require_auth=True)
def api_gift_invite_link(request):
    if request.method == "GET":
        user_invites = Invite.for_user(user=request.me)
        return JsonResponse({
            "invites": [invite.to_dict() for invite in user_invites],
            "can_create_invite": Invite.can_create_invite(request.me),
            "max_invites": Invite.MAX_INVITES_PER_USER,
        })

    if request.method == "POST":
        if not Invite.can_create_invite(request.me):
            raise ApiAccessDenied(message="У вас уже есть максимальное количество активных инвайтов")

        invite = Invite.objects.create(
            user=request.me,
        )

        return JsonResponse({
            "invite": invite.to_dict(),
        })

    return HttpResponseNotAllowed(permitted_methods=["GET", "POST"])
