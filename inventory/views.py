"""Views for inventory management."""

from uuid import UUID

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    InventoryItemForm,
    QuickRecipeForm,
    RecipeForm,
    RecipeIngredientFormSet,
    StockAdjustmentForm,
)
from .models import SUBCATEGORY_MAP, Category, InventoryItem, Recipe

SORTABLE_COLUMNS = [
    ("name", "Name"),
    ("category", "Category"),
    ("subcategory", "Subcategory"),
    ("quantity_on_hand", "Qty"),
]


def _build_sort_url(
    category: str, field: str, direction: str, subcategory: str = ""
) -> str:
    """Build a query string for sorting, preserving category and subcategory filters."""
    params = f"sort={field}&dir={direction}"
    if category:
        params = f"category={category}&{params}"
    if subcategory:
        params = f"{params}&subcategory={subcategory}"
    return f"/?{params}"


def item_list(request: HttpRequest) -> HttpResponse:
    """List all inventory items with optional filtering, search, and sorting."""
    items = InventoryItem.objects.prefetch_related(
        "earmarked_for",
        "earmarked_for__ingredients",
        "earmarked_for__ingredients__ingredient",
    ).all()

    category = request.GET.get("category", "")
    subcategory = request.GET.get("subcategory", "")
    search = request.GET.get("search", "")
    sort = request.GET.get("sort", "name")
    direction = request.GET.get("dir", "asc")

    if category:
        items = items.filter(category=category)
    if subcategory:
        items = items.filter(subcategory=subcategory)
    if search:
        items = items.filter(name__icontains=search)

    # Validate and apply sorting
    sortable_field_names = {f for f, _ in SORTABLE_COLUMNS}
    if sort not in sortable_field_names:
        sort = "name"
    order_prefix = "-" if direction == "desc" else ""
    items = items.order_by(f"{order_prefix}{sort}")

    # Build column headers with sort URLs
    columns = []
    for field, label in SORTABLE_COLUMNS:
        if field == sort:
            next_dir = "desc" if direction == "asc" else "asc"
            arrow = "\u25b2" if direction == "asc" else "\u25bc"
            columns.append(
                {
                    "field": field,
                    "label": f"{label} {arrow}",
                    "url": _build_sort_url(category, field, next_dir, subcategory),
                    "active": True,
                }
            )
        else:
            columns.append(
                {
                    "field": field,
                    "label": label,
                    "url": _build_sort_url(category, field, "asc", subcategory),
                    "active": False,
                }
            )

    # Build sub-tabs for ingredient subcategories
    sub_tabs: list[dict[str, str | bool]] = []
    if category == Category.INGREDIENT:
        sub_tabs.append(
            {
                "label": "All",
                "url": f"/?category={category}",
                "active": not subcategory,
            }
        )
        for value, label in SUBCATEGORY_MAP[Category.INGREDIENT]:
            sub_tabs.append(
                {
                    "label": label,
                    "url": f"/?category={category}&subcategory={value}",
                    "active": subcategory == value,
                }
            )

    context = {
        "items": items,
        "current_category": category,
        "current_subcategory": subcategory,
        "search_query": search,
        "current_sort": sort,
        "current_dir": direction,
        "columns": columns,
        "sub_tabs": sub_tabs,
        "show_earmarked_column": category in ("", Category.INGREDIENT),
    }

    if request.headers.get("HX-Request"):
        return render(request, "inventory/partials/item_table.html", context)

    return render(request, "inventory/item_list.html", context)


def item_create(request: HttpRequest) -> HttpResponse:
    """Create a new inventory item."""
    if request.method == "POST":
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("inventory:item_list")
    else:
        form = InventoryItemForm()

    return render(
        request,
        "inventory/item_form.html",
        {"form": form, "recipes": Recipe.objects.all()},
    )


def item_detail(request: HttpRequest, pk: UUID) -> HttpResponse:
    """Display details for a single inventory item."""
    item = get_object_or_404(InventoryItem, pk=pk)
    return render(request, "inventory/item_detail.html", {"item": item})


def item_update(request: HttpRequest, pk: UUID) -> HttpResponse:
    """Update an existing inventory item."""
    item = get_object_or_404(InventoryItem, pk=pk)

    if request.method == "POST":
        form = InventoryItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect("inventory:item_detail", pk=item.pk)
    else:
        form = InventoryItemForm(instance=item)

    return render(
        request,
        "inventory/item_form.html",
        {"form": form, "item": item, "recipes": Recipe.objects.all()},
    )


def item_delete(request: HttpRequest, pk: UUID) -> HttpResponse:
    """Delete an inventory item after confirmation."""
    item = get_object_or_404(InventoryItem, pk=pk)

    if request.method == "POST":
        item.delete()
        return redirect("inventory:item_list")

    return render(request, "inventory/item_confirm_delete.html", {"item": item})


def adjust_stock(request: HttpRequest, pk: UUID) -> HttpResponse:
    """HTMX endpoint: adjust stock quantity inline."""
    item = get_object_or_404(InventoryItem, pk=pk)

    # Determine if earmarked column is visible based on current page context
    current_url = request.headers.get("HX-Current-URL", "")
    show_earmarked = (
        "category=chemical" not in current_url
        and "category=finished_good" not in current_url
    )
    row_context = {"item": item, "show_earmarked_column": show_earmarked}

    if request.GET.get("cancel"):
        return render(request, "inventory/partials/item_row.html", row_context)

    if request.method == "POST":
        form = StockAdjustmentForm(request.POST)
        if form.is_valid():
            form.apply_to(item)
            return render(request, "inventory/partials/item_row.html", row_context)
    else:
        form = StockAdjustmentForm()

    return render(
        request,
        "inventory/partials/adjust_stock_form.html",
        {"item": item, "form": form},
    )


def subcategory_options(request: HttpRequest) -> HttpResponse:
    """HTMX endpoint: return subcategory <option> elements for a given category."""
    category = request.GET.get("category", "")
    choices = SUBCATEGORY_MAP.get(category, [])
    show_earmarked = category == Category.INGREDIENT
    recipes = Recipe.objects.all() if show_earmarked else Recipe.objects.none()
    return render(
        request,
        "inventory/partials/subcategory_select.html",
        {
            "choices": choices,
            "show_earmarked": show_earmarked,
            "recipes": recipes,
        },
    )


def recipe_list(request: HttpRequest) -> HttpResponse:
    """List all recipes."""
    recipes = Recipe.objects.all()
    return render(request, "inventory/recipe_list.html", {"recipes": recipes})


def recipe_create(request: HttpRequest) -> HttpResponse:
    """Create a new recipe."""
    if request.method == "POST":
        form = RecipeForm(request.POST)
        formset = RecipeIngredientFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            recipe = form.save()
            formset.instance = recipe
            formset.save()
            return redirect("inventory:recipe_list")
    else:
        form = RecipeForm()
        formset = RecipeIngredientFormSet()
    return render(
        request,
        "inventory/recipe_form.html",
        {"form": form, "ingredient_formset": formset},
    )


def recipe_update(request: HttpRequest, pk: UUID) -> HttpResponse:
    """Update an existing recipe."""
    recipe = get_object_or_404(Recipe, pk=pk)
    if request.method == "POST":
        form = RecipeForm(request.POST, instance=recipe)
        formset = RecipeIngredientFormSet(request.POST, instance=recipe)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect("inventory:recipe_list")
    else:
        form = RecipeForm(instance=recipe)
        formset = RecipeIngredientFormSet(instance=recipe)
    return render(
        request,
        "inventory/recipe_form.html",
        {"form": form, "ingredient_formset": formset, "recipe": recipe},
    )


def recipe_delete(request: HttpRequest, pk: UUID) -> HttpResponse:
    """Delete a recipe after confirmation."""
    recipe = get_object_or_404(Recipe, pk=pk)
    if request.method == "POST":
        recipe.delete()
        return redirect("inventory:recipe_list")
    return render(request, "inventory/recipe_confirm_delete.html", {"recipe": recipe})


def recipe_quick_add(request: HttpRequest) -> HttpResponse:
    """HTMX endpoint: quick-add a recipe and return updated earmarked_for select."""
    if request.method == "POST":
        # Map recipe_name to name for the form
        data = {"name": request.POST.get("recipe_name", "")}
        form = QuickRecipeForm(data)
        if form.is_valid():
            new_recipe = form.save()
            recipes = Recipe.objects.all()
            # Return OOB swap for checkbox list + empty slot content
            return render(
                request,
                "inventory/partials/quick_recipe_success.html",
                {"recipes": recipes, "selected": [new_recipe.pk]},
            )
        # If invalid, re-show the form with errors
        return render(
            request,
            "inventory/partials/quick_recipe_form.html",
            {"form": form},
        )
    form = QuickRecipeForm()
    return render(
        request,
        "inventory/partials/quick_recipe_form.html",
        {"form": form},
    )
