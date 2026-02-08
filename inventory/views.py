"""Views for inventory management."""

from uuid import UUID

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import InventoryItemForm, StockAdjustmentForm
from .models import SUBCATEGORY_MAP, InventoryItem

SORTABLE_COLUMNS = [
    ("name", "Name"),
    ("category", "Category"),
    ("subcategory", "Subcategory"),
    ("quantity_on_hand", "Qty"),
]


def _build_sort_url(category: str, field: str, direction: str) -> str:
    """Build a query string for sorting, preserving the category filter."""
    params = f"sort={field}&dir={direction}"
    if category:
        return f"/?category={category}&{params}"
    return f"/?{params}"


def item_list(request: HttpRequest) -> HttpResponse:
    """List all inventory items with optional filtering, search, and sorting."""
    items = InventoryItem.objects.all()

    category = request.GET.get("category", "")
    search = request.GET.get("search", "")
    sort = request.GET.get("sort", "name")
    direction = request.GET.get("dir", "asc")

    if category:
        items = items.filter(category=category)
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
                    "url": _build_sort_url(category, field, next_dir),
                    "active": True,
                }
            )
        else:
            columns.append(
                {
                    "field": field,
                    "label": label,
                    "url": _build_sort_url(category, field, "asc"),
                    "active": False,
                }
            )

    context = {
        "items": items,
        "current_category": category,
        "search_query": search,
        "current_sort": sort,
        "current_dir": direction,
        "columns": columns,
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

    return render(request, "inventory/item_form.html", {"form": form})


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

    return render(request, "inventory/item_form.html", {"form": form, "item": item})


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

    if request.method == "POST":
        form = StockAdjustmentForm(request.POST)
        if form.is_valid():
            form.apply_to(item)
            return render(request, "inventory/partials/item_row.html", {"item": item})
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
    return render(
        request,
        "inventory/partials/subcategory_select.html",
        {"choices": choices},
    )
