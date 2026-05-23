FROM python:3.11-slim

WORKDIR /app

COPY hf-space/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

ENV HOST=0.0.0.0 PORT=7860
EXPOSE 7860

CMD ["python", "hf-space/app.py"]
