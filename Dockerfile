ARG PYTHON_VERSION=3.12-slim-trixie

FROM python:${PYTHON_VERSION}

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


RUN apt-get update \
    && apt-get install -y sqlite3 curl ffmpeg\
    && rm -rf /var/lib/apt/lists/*


# Supercronic ---
# Latest releases available at https://github.com/aptible/supercronic/releases
ARG TARGETARCH
ENV SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/v0.2.32/supercronic-linux-${TARGETARCH} \
    SUPERCRONIC=supercronic-linux-${TARGETARCH}

RUN case "$TARGETARCH" in \
      amd64) SUPERCRONIC_SHA1SUM=7da26ce6ab48d75e97f7204554afe7c80779d4e0 ;; \
      arm64) SUPERCRONIC_SHA1SUM=7f89438e7810669d3e0ea488a202aaf422cc2fdf ;; \
    esac \
 && curl -fsSLO "$SUPERCRONIC_URL" \
 && echo "${SUPERCRONIC_SHA1SUM}  ${SUPERCRONIC}" | sha1sum -c - \
 && chmod +x "$SUPERCRONIC" \
 && mv "$SUPERCRONIC" "/usr/local/bin/${SUPERCRONIC}" \
 && ln -s "/usr/local/bin/${SUPERCRONIC}" /usr/local/bin/supercronic


# App ---
RUN mkdir -p /code
WORKDIR /code
RUN pip install pipenv
COPY Pipfile Pipfile.lock /code/
RUN pipenv install --deploy --system
COPY . /code
RUN python manage.py collectstatic --noinput

EXPOSE 8000

RUN chmod +x ./scripts/startup.sh
ENTRYPOINT ["./scripts/startup.sh"]
