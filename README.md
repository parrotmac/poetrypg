# poetrypg

Prebuilt Poetry images that aspire to have the prerequisites available for a Python-based PostgreSQL app.

The main target for this container is to be used as a basis for things like Django or SQLAlchemy that connect to a PostgreSQL DB and are using Poetry.

### Goals
- [x] Auto-update from Poetry versions
- [ ] Auto-update from Python versions
- [ ] Auto-update from Debian & Alpine versions

Since these containers are, in turn, based on other containers, we'll probably need a way to query the DockerHub API for avaialble versions.

### Example Usage

```dockerfile
FROM isaacp/poetrypg:1.1.13-py3.9.12-alpine # Or, ya know, whatever version

# This will be our example app's home
WORKDIR /app

COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-ansi --no-dev

# Copy all your project files
# While this can be done earlier, it can be convienient to cache the above steps since they may take longer to complete.
COPY . ./
```
