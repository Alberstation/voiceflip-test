# Contributing

## Code Style

- **Comments**: English only.
- **Docstrings**: English; prefer concise one-liners unless a longer description is needed.
- **Modularity**: Keep modules focused; extract helpers into separate files when functions exceed ~50 lines.
- **Constants**: Use `app/constants.py` for magic strings; avoid literals in business logic.

## Commit Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation
- `chore:` maintenance (deps, config)
- `refactor:` code change without behavior change
- `test:` add or update tests

Example: `feat: add MMR retrieval technique`

## Running Tests

All tests run inside Docker:

```bash
docker compose run --rm app pytest tests/ -v
```

## Environment

- Do not install Python packages on the host; all dependencies are in the container.
- Copy `.env.example` to `.env` and set `HUGGINGFACEHUB_API_TOKEN` for RAG features.
