# CLAUDE.md — mvph_inventory

## Project Overview

Brewery inventory management application. Tracks ingredients (malt, hops, yeast, adjuncts), chemicals (cleaning agents, sanitizers, water treatment), and finished goods (kegs, cans, bottles) for a small brewing operation.

Built with Django, PostgreSQL, and HTMX. Server-rendered UI using Django templates with HTMX for dynamic interactivity.

## Tech Stack

- **Backend:** Python 3.14+ / Django 6.x
- **Database:** PostgreSQL
- **Frontend:** Django templates + HTMX
- **Testing:** pytest with simple fixtures

## Project Structure

```
mvph_inventory/
├── manage.py
├── config/              # Django project settings
│   ├── settings/
│   │   ├── base.py
│   │   ├── local.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
├── inventory/           # Main inventory app
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   └── templates/
├── templates/           # Shared/base templates
├── static/              # Static assets
├── tests/               # Test directory (pytest)
├── requirements/
│   ├── base.txt
│   ├── local.txt
│   └── production.txt
└── pyproject.toml
```

## Coding Standards

- **Type hints required** on all function signatures and return types
- **Ruff** for linting and formatting (line length: 88)
- **mypy** for static type checking (strict mode)
- Follow Django conventions: fat models, thin views
- Use `django-stubs` for Django type support
- All imports sorted with `isort` (via Ruff)

## Commands

```bash
# Run dev server
python manage.py runserver

# Run tests
pytest

# Run tests with coverage
pytest --cov

# Lint and format
ruff check .
ruff format .

# Type check
mypy .

# Database migrations
python manage.py makemigrations
python manage.py migrate
```

## Rules

- **Always run tests before committing.** Do not commit if tests fail.
- **Keep PRs small and focused.** One concern per PR.
- **Document all API endpoints.** Every view that serves data must have a docstring describing its purpose, parameters, and response.
- Never commit secrets, `.env` files, or credentials.
- Prefer Django ORM over raw SQL unless there is a clear performance reason.
- Use Django's built-in auth system — do not roll custom authentication.
- Templates should use HTMX attributes for dynamic behavior rather than inline JavaScript.

## Database Conventions

- Model fields use `snake_case`
- All models include `created_at` and `updated_at` timestamp fields
- Use `django.db.models.UUIDField` for primary keys when appropriate
- Foreign keys use `related_name` explicitly

## Business Domain

### Item Categories
- **Ingredients** — brewing inputs: malt/grain, hops, yeast, adjuncts (fruit, spices, etc.)
- **Chemicals** — cleaning agents, sanitizers, water treatment chemicals
- **Finished Goods** — packaged beer: kegs, cans, bottles, cases

### MVP Scope
- CRUD operations for all inventory items
- Track stock quantities (simple quantity on hand)
- Categorize items by type (ingredient, chemical, finished good)
- Single-user / small business owner workflow
- No BOM, supplier tracking, or order management in MVP

### Future Considerations (post-MVP)
- Bill of Materials (recipes → ingredients)
- Supplier management and cost tracking
- Purchase orders and receiving
- Batch/lot tracking for ingredients
- Expiration date tracking for perishables
- Multi-location support (e.g., brewhouse vs. warehouse)

## Testing Conventions

- Tests live in the `tests/` directory at the project root
- Use `pytest` with simple fixtures (no factory_boy)
- Test files follow `test_<module>.py` naming
- Aim for coverage on all model methods and view logic
- Use `pytest-django` for Django integration
