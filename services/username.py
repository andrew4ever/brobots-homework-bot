def username(user):
    return user.first_name + (user.last_name if user.last_name else '')
