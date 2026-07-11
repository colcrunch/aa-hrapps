from django.conf import settings
from allianceauth.eveonline.models import EveCharacter
from allianceauth.services.hooks import get_extension_logger

from hrapps.models import FormResponse, ResponseComment

logger = get_extension_logger(__name__)


class Field:
    def __init__(self,
                 type,
                 question,
                 options=None,
                 required=False,
                 allowMultiple=None,
                 allowUpdates=None,
                 attachmentLimit=None
                 ):
        self.type = type
        self.question = question
        self.required = required
        self.allowMultiple = allowMultiple
        self.allowUpdates = allowUpdates
        self.attachmentLimit = attachmentLimit
        if options is not None:
            self.options = tuple(options)
        else:
            self.options = None

    def __dict__(self):
        return {
            "type": self.type,
            "question": self.question,
            "required": self.required,
            "options": self.options,
            "allowMultiple": self.allowMultiple,
            "allowUpdates": self.allowUpdates,
            "attachmentLimit": self.attachmentLimit,
        }

class ResponseItem:
    def __init__(self, question, answer):
        self.question = question
        self.answer = answer

    @property
    def answer_is_list(self):
        return isinstance(self.answer, list)


def get_corptools_chars(characters):
    if "corptools" in settings.INSTALLED_APPS:
        from corptools.models.audits import CharacterAudit

        char_audits = CharacterAudit.objects\
            .filter(character__in=characters)\
            .values_list("character__character_name", flat=True)
        return char_audits

    return None


def get_memberaudit_chars(characters):
    if "memberaudit" in settings.INSTALLED_APPS:
        from memberaudit.models.characters import Character

        char_audits = Character.objects\
            .filter(eve_character__in=characters)\
            .values_list("eve_character__character_name", "pk")

        char_audits = dict(char_audits)

        return char_audits

    return None


def process_comments(comments):
    root_comments = comments.filter(reply_to=None)
    replied_comments = comments.filter(reply_to__isnull=False).values_list("reply_to", flat=True)
    replies = dict()

    for id in replied_comments:
        replies[id] = comments.filter(reply_to=id)

    return root_comments, replies


def get_application_context(request, application_id, admin=False):
    try:
        application = FormResponse.objects.get(pk=application_id)
    except FormResponse.DoesNotExist as e:
        return None

    if admin == True or request.user.has_perm("hrapps.manage_hrapps"):
        app_comments = ResponseComment.objects.filter(response=application)
    else:
        # Only load non-private comments for applicants.
        app_comments = ResponseComment.objects.filter(response=application, private=False)
    root_comments, replies = process_comments(app_comments)
    characters = EveCharacter.objects \
        .filter(character_ownership__user=application.user) \
        .select_related() \
        .order_by('character_name')

    response_items = []
    for item in application.response["questions"]:
        response_items.append(ResponseItem(item["question"], item["answer"]))

    corptools = get_corptools_chars(characters) if "corptools" in settings.INSTALLED_APPS else None
    memberaudit = get_memberaudit_chars(characters) if "memberaudit" in settings.INSTALLED_APPS else None

    return {
      "application": application,
      "root_comments": root_comments,
      "replies": replies,
      "responses": response_items,
      "characters": characters,
      "corptools": corptools,
      "memberaudit": memberaudit,
      "admin": admin,
    }

def add_comment(request, response_id):
    user = request.user
    comment = request.POST.get("comment")
    private = request.POST.get("private")
    if private is None:
        private = False
    else:
        private = True

    try:
        comment = ResponseComment(
            user=user,
            content=comment,
            private=private,
            response_id=response_id
        )

        comment.save()
        return True
    except Exception as e:
        logger.error(e)
        return False


def add_reply(request, response_id, comment_id):
    user = request.user
    reply = request.POST.get("reply")
    private = ResponseComment.objects.get(pk=comment_id).private

    try:
        comment = ResponseComment(
            user=user,
            content=reply,
            private=private,
            response_id=response_id,
            reply_to_id=comment_id
        )

        comment.save()
        return True
    except Exception as e:
        logger.error(e)
        return False
