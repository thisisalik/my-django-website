from django import template

register = template.Library()

@register.filter
def get_item(queryset, index):
    try:
        return queryset[int(index)]
    except:
        return None
