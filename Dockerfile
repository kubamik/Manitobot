FROM python:3.13-slim
RUN pip install poetry~=1.8.0
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry install
# Copy in everything else:
COPY . .
# Install project package:
RUN poetry install

CMD poetry run python main.py
