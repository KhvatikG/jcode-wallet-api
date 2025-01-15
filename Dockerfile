FROM python:3.13-alpine
LABEL authors="Игорь"

WORKDIR /app

RUN apk --no-cache add curl bash gcc python3-dev musl-dev linux-headers

RUN curl -sSL https://install.python-poetry.org | python3
ENV PATH="/root/.local/bin:$PATH"
RUN poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root

COPY . .

RUN chmod +x ./entrypoint.sh
ENTRYPOINT ["bash", "./entrypoint.sh"]
