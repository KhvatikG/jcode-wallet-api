FROM python:3.13-alpine
LABEL authors="Игорь"

WORKDIR /app

RUN apk --no-cache add curl bash

RUN curl -sSL https://install.python-poetry.org | python3
ENV PATH="/root/.local/bin:$PATH"
RUN poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root

COPY . .

#CMD ["bash"]
RUN chmod +x ./entrypoint.sh
ENTRYPOINT ["bash", "./entrypoint.sh"]
#CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
