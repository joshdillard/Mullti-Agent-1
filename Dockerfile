FROM python:3.12-slim

# Optional live integrations (Stripe, Google). Build with
#   docker build --build-arg INSTALL_EXTRAS=1 .
# to bake them in; otherwise they stay in demo mode until installed.
ARG INSTALL_EXTRAS=0

WORKDIR /app

COPY requirements.txt requirements-full.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && if [ "$INSTALL_EXTRAS" = "1" ]; then \
         pip install --no-cache-dir -r requirements-full.txt; \
       fi

COPY . .

ENV PYTHONUNBUFFERED=1
EXPOSE 8765

# Default to the dashboard; compose overrides this for the scheduler service.
CMD ["python", "run.py", "dashboard", "--host", "0.0.0.0", "--port", "8765"]
