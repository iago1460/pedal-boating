from django import template

register = template.Library()


@register.filter
def get_index(array, item):
    return array.index(item)

@register.filter
def lookup(d, key):
    return d[key]
