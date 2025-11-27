from django.contrib import admin
from .models import Attribute, AttributeValue, Rule, Applicant


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ("id", "nomi")


@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    list_display = ("id", "attribute", "qiymat")


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ("id", "shartlar", "natija")
    search_fields = ("shartlar",)


@admin.register(Applicant)
class ApplicantAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "daromad",
        "yosh",
        "kredit_tarixchasi",
        "qarzlar",
        "kredit_miqdori",
        "garov",
        "ish_staji",
        "natija",
    )
    search_fields = ("natija", "kredit_tarixchasi")
