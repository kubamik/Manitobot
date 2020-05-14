FROM python:3.8-slim
RUN pip install poetry
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry install
# Copy in everything else:
COPY . .

CMD poetry run python main.py
