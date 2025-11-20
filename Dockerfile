FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /smartsocialmonitor

RUN addgroup --system ssmgroup && adduser --system --ingroup ssmgroup ssmuser

COPY requirements.txt .

RUN  pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R ssmuser:ssmgroup /smartsocialmonitor

USER ssmuser

EXPOSE 8000

CMD ["/bin/sh", "-c", "gunicorn -w 2 -b 0.0.0.0:${PORT:-8000} dashboard:server"]