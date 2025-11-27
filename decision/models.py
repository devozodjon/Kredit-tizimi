from django.db import models

class Applicant(models.Model):
    daromad = models.IntegerField()
    yosh = models.IntegerField()
    kredit_tarixchasi = models.CharField(max_length=20, choices=[
        ("Yaxshi", "Yaxshi"),
        ("O'rtacha", "O'rtacha"),
        ("Yomon", "Yomon"),
    ])
    qarzlar = models.IntegerField()
    kredit_miqdori = models.IntegerField()
    natija = models.CharField(max_length=50, blank=True, null=True)
    garov = models.CharField(max_length=100, blank=True, null=True)
    ish_staji = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.yosh} yosh - {self.natija or 'Aniqlanmagan'}"


class Attribute(models.Model):
    nomi = models.CharField(max_length=100)

    def __str__(self):
        return self.nomi


class AttributeValue(models.Model):
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name='qiymatlar')
    qiymat = models.CharField(max_length=100)
    key = models.IntegerField(unique=True)

    def __str__(self):
        return f"{self.attribute.nomi} = {self.qiymat}"


class Rule(models.Model):
    shartlar = models.JSONField()
    natija = models.IntegerField()

    def __str__(self):
        return f"{self.shartlar} => {self.natija}"
