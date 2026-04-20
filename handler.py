from app import app

def handler(request, context=None):
    return app(request)