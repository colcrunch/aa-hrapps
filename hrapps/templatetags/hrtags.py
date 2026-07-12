from django.template.defaulttags import register

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def filter_by_question_id(qs, question_id):
    return qs.filter(
        question_id=question_id
    )