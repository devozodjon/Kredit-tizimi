from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Applicant, AttributeValue, Rule, Attribute
import json


# -------------------------
#  Yordamchi funksiya
# -------------------------
def qiymat_mos(kiritilgan, shart):
    try:
        kiritilgan_int = int(kiritilgan)
        if shart.startswith(">="):
            return kiritilgan_int >= int(shart[2:])
        elif shart.startswith("<="):
            return kiritilgan_int <= int(shart[2:])
        elif shart.startswith(">"):
            return kiritilgan_int > int(shart[1:])
        elif shart.startswith("<"):
            return kiritilgan_int < int(shart[1:])
        elif shart.startswith("!="):
            return str(kiritilgan) != shart[2:]
        else:
            return str(kiritilgan) == shart
    except ValueError:
        return str(kiritilgan) == shart


# -------------------------
#  Asosiy index (bitta HTML fayl)
# -------------------------
def index(request):
    natija = None

    if request.method == "POST" and 'daromad' in request.POST:
        foydalanuvchi_qiymatlari = {
            "Daromad": request.POST.get("daromad"),
            "Yosh": request.POST.get("yosh"),
            "Kredit tarixchasi": request.POST.get("kredit_tarixchasi"),
            "Qarzlar": request.POST.get("qarzlar"),
            "Kredit miqdori": request.POST.get("kredit_miqdori"),
            "Garov": request.POST.get("garov"),
            "Ish staji": request.POST.get("ish_staji")
        }

        rules = Rule.objects.all()
        for rule in rules:
            mos = True
            for atribut_index, qiymat_key in rule.shartlar:
                atribut_value = AttributeValue.objects.get(key=qiymat_key)
                atribut_nomi = atribut_value.attribute.nomi

                if atribut_nomi not in foydalanuvchi_qiymatlari:
                    mos = False
                    break

                kiritilgan = foydalanuvchi_qiymatlari[atribut_nomi]
                if not qiymat_mos(kiritilgan, atribut_value.qiymat):
                    mos = False
                    break

            if mos:
                natija = AttributeValue.objects.get(key=rule.natija).qiymat
                break

        if not natija:
            natija = "Mos qoida topilmadi"

        Applicant.objects.create(
            daromad=foydalanuvchi_qiymatlari["Daromad"],
            yosh=foydalanuvchi_qiymatlari["Yosh"],
            kredit_tarixchasi=foydalanuvchi_qiymatlari["Kredit tarixchasi"],
            qarzlar=foydalanuvchi_qiymatlari["Qarzlar"],
            kredit_miqdori=foydalanuvchi_qiymatlari["Kredit miqdori"],
            garov=foydalanuvchi_qiymatlari["Garov"],
            ish_staji=foydalanuvchi_qiymatlari["Ish staji"],
            natija=natija
        )

    return render(request, "index.html", {"natija": natija})


# -------------------------
#  Login/Logout
# -------------------------
def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_superuser:
            login(request, user)
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False}, status=401)

    return JsonResponse({"error": "Invalid request"}, status=400)


def user_logout(request):
    logout(request)
    return redirect('/')


# -------------------------
#  API endpoints (faqat superuser uchun)
# -------------------------
@login_required
def api_stats(request):
    if not request.user.is_superuser:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    return JsonResponse({
        "applicants": Applicant.objects.count(),
        "rules": Rule.objects.count(),
        "attributes": Attribute.objects.count(),
        "values": AttributeValue.objects.count(),
    })


@login_required
def api_attributes(request):
    if not request.user.is_superuser:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    attributes = list(Attribute.objects.values('id', 'nomi'))
    return JsonResponse(attributes, safe=False)


@login_required
def api_attribute_values(request):
    if not request.user.is_superuser:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    values = AttributeValue.objects.select_related('attribute').all()
    data = [{
        'id': v.id,
        'attribute_name': v.attribute.nomi,
        'qiymat': v.qiymat,
        'key': v.key
    } for v in values]
    return JsonResponse(data, safe=False)


@login_required
def api_rules(request):
    if not request.user.is_superuser:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    rules = list(Rule.objects.values('id', 'shartlar', 'natija'))
    return JsonResponse(rules, safe=False)


@login_required
def api_applicants(request):
    if not request.user.is_superuser:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    applicants = list(Applicant.objects.values(
        'id', 'daromad', 'yosh', 'kredit_tarixchasi', 'qarzlar',
        'kredit_miqdori', 'garov', 'ish_staji', 'natija'
    ).order_by('-id'))
    return JsonResponse(applicants, safe=False)


# -------------------------
#  Delete endpoints
# -------------------------
@login_required
@csrf_exempt
def api_attribute_delete(request, pk):
    if not request.user.is_superuser:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    if request.method == "POST":
        attribute = get_object_or_404(Attribute, pk=pk)
        attribute.delete()
        return JsonResponse({"success": True})

    return JsonResponse({"error": "Invalid method"}, status=400)


@login_required
@csrf_exempt
def api_attribute_value_delete(request, pk):
    if not request.user.is_superuser:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    if request.method == "POST":
        value = get_object_or_404(AttributeValue, pk=pk)
        value.delete()
        return JsonResponse({"success": True})

    return JsonResponse({"error": "Invalid method"}, status=400)


@login_required
@csrf_exempt
def api_rule_delete(request, pk):
    if not request.user.is_superuser:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    if request.method == "POST":
        rule = get_object_or_404(Rule, pk=pk)
        rule.delete()
        return JsonResponse({"success": True})

    return JsonResponse({"error": "Invalid method"}, status=400)


@login_required
@csrf_exempt
def api_applicant_delete(request, pk):
    if not request.user.is_superuser:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    if request.method == "POST":
        applicant = get_object_or_404(Applicant, pk=pk)
        applicant.delete()
        return JsonResponse({"success": True})

    return JsonResponse({"error": "Invalid method"}, status=400)