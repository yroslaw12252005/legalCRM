from django import template

register = template.Library()

@register.filter
def get_range(start, end):
    return range(start, end + 1)

@register.filter
def multiply(value, arg):
    t = str(value.time())
    return (int(t[0:2])-9) * arg

@register.filter
def math(value, arg):
    print()
    return ((int(value[0:2])-9) * arg)+(int(value[-2:])*6)+30