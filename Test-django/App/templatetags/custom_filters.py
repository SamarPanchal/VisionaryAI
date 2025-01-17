from django import template

register = template.Library()

# Custom filter to create a range of numbers up to the given value
@register.filter
def to(value):
    return range(1, value + 1)

# Custom filter to add two numbers
@register.filter
def add(value, arg):
    return value + arg
