# app/utils/context_helpers.py
def inject_user_context(request, **kwargs):
    return {
        "request": request,
        "user": {
            "name": "Jeremy Bale",  # always needed
            "avatar_url": ""        # can be empty if no custom avatar yet
        },
        **kwargs
    }



