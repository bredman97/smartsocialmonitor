FROM python:3.13-slim

WORKDIR /smartsocialmonitor

RUN addgroup --system ssmgroup && adduser --system --ingroup ssmgroup ssmuser

COPY requirements.txt .

RUN  pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R ssmuser:ssmgroup /smartsocialmonitor

USER ssmuser

EXPOSE 8050

CMD [ "gunicorn", "-w", "2", "-b", "0.0.0.0:8050", "dashboard:server"]