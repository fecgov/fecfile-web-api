FROM python:3.13
ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN mkdir /opt/nxg_fec
WORKDIR /opt/nxg_fec

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

RUN mv /etc/localtime /etc/localtime.backup && ln -s /usr/share/zoneinfo/EST5EDT /etc/localtime

COPY bin/entrypoint.sh /opt/
RUN chmod +x /opt/entrypoint.sh

RUN useradd nxgu --no-create-home --home /opt/nxg_fec \
    && chown -R nxgu:nxgu /opt/nxg_fec /opt/venv
USER nxgu

EXPOSE 8080
ENTRYPOINT ["/opt/entrypoint.sh"]
