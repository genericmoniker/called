"""Gunicorn configuration file."""  # noqa: INP001

# Useful tutorial (the gunicorn docs themselves seem dated):
# https://betterstack.com/community/guides/scaling-python/gunicorn-explained/

bind = "127.0.0.1:8000"
workers = 4
worker_class = "gthread"
threads = 2
timeout = 60
