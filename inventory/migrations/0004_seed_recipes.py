"""Seed initial recipes."""

from django.db import migrations


def seed_recipes(apps, schema_editor):
    Recipe = apps.get_model("inventory", "Recipe")
    for name in ["Pale Ale", "Double IPA", "Stout"]:
        Recipe.objects.get_or_create(name=name)


def remove_recipes(apps, schema_editor):
    Recipe = apps.get_model("inventory", "Recipe")
    Recipe.objects.filter(name__in=["Pale Ale", "Double IPA", "Stout"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0003_recipe_inventoryitem_earmarked_for"),
    ]

    operations = [
        migrations.RunPython(seed_recipes, remove_recipes),
    ]
