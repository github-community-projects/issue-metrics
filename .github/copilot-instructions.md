# Copilot Instructions

This is a GitHub Action that searches for issues/pull requests/discussions in a repository, measures several metrics, and generates a report in form of a GitHub issue. The issues/pull requests/discussions to search for can be filtered by using a search query.

## Code Standards

### Required Before Each Commit

- Run `make lint` before committing any changes to ensure proper code linting and formatting.

### Development Flow

- Lint: `make lint`
- Test: `make test`

## Repository Structure

- `Makefile`: Contains commands for linting, testing, and other tasks
- `pyproject.toml`: Python dependencies and project configuration
- `README.md`: Project documentation and setup instructions
- `test_*.py`: Python test files matching the naming convention for test discovery

## Key Guidelines

1. Follow Python best practices and idiomatic patterns
2. Maintain existing code structure and organization
3. Write unit tests for new functionality.
4. Document changes to environment variables in the `README.md` file.
