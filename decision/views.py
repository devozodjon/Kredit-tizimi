from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Attribute, AttributeValue, Rule
import json


def qiymat_mos(user_value, db_value):
    """Foydalanuvchi qiymatini shart bilan solishtiradi"""
    try:
        user_val = int(user_value)
        if db_value.startswith(">="):
            return user_val >= int(db_value[2:])
        if db_value.startswith("<="):
            return user_val <= int(db_value[2:])
        if db_value.startswith(">"):
            return user_val > int(db_value[1:])
        if db_value.startswith("<"):
            return user_val < int(db_value[1:])
        if db_value.startswith("!="):
            return str(user_value) != db_value[2:]
    except (ValueError, TypeError):
        pass
    return str(user_value).strip() == str(db_value).strip()


@csrf_exempt
def find_matching_rule(request):
    """
    Frontend'dan barcha ma'lumotlarni olib,
    eng mos qoidani topadi va natija beradi
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_answers = data.get('answers', {})

            if not user_answers:
                return JsonResponse({
                    'found': False,
                    'result': 'Ma\'lumot kiritilmagan'
                })

            # Frontend ID -> DB format mapping
            db_answers = {}
            for frontend_id, value in user_answers.items():
                db_atribut_index = int(frontend_id) - 1
                db_answers[str(db_atribut_index)] = value

            print(f"Frontend answers: {user_answers}")
            print(f"DB format answers: {db_answers}")

            # Barcha qoidalarni ID bilan sortirlash
            rules = Rule.objects.all().order_by('id')

            for rule in rules:
                rule_matches = True
                print(f"\n=== Qoida #{rule.id} tekshirilmoqda ===")

                # Bu qoidaning BARCHA shartlarini tekshir
                for condition in rule.shartlar:
                    attr_index = condition['atribut']
                    val_key = condition['qiymat']

                    # Agar atribut kiritilmagan bo'lsa
                    if str(attr_index) not in db_answers:
                        rule_matches = False
                        print(f"❌ Atribut {attr_index} kiritilmagan")
                        break

                    user_val = db_answers[str(attr_index)]
                    try:
                        attr_val = AttributeValue.objects.get(key=val_key)
                    except AttributeValue.DoesNotExist:
                        rule_matches = False
                        print(f"❌ Key {val_key} topilmadi")
                        break

                    if not qiymat_mos(user_val, attr_val.qiymat):
                        rule_matches = False
                        print(f"❌ Qiymat mos kelmadi")
                        break

                # Agar qoida mos kelsa
                if rule_matches:
                    print(f"✅ Qoida #{rule.id} MOS KELDI!")
                    result_key = rule.natija

                    try:
                        result_value = AttributeValue.objects.get(key=result_key)
                    except AttributeValue.DoesNotExist:
                        continue

                    # CHAIN LOGIC: Agar natija "Qo'shimcha tekshiruv kerak" (26)
                    if result_key == 26:
                        print(f"🔗 Chain natija: Qo'shimcha tekshiruv kerak")

                        return JsonResponse({
                            'found': True,
                            'chain_required': True,
                            'result': result_value.qiymat,
                            'rule_id': rule.id,
                            'message': 'Qo\'shimcha ma\'lumot kiritish kerak'
                        })

                    # Oddiy natija
                    return JsonResponse({
                        'found': True,
                        'result': result_value.qiymat,
                        'rule_id': rule.id
                    })

            # Mos qoida topilmadi
            return JsonResponse({
                'found': False,
                'result': 'Mos qoida topilmadi. Iltimos, ma\'lumotlarni qayta tekshiring.'
            })

        except Exception as e:
            print(f"Xatolik: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'found': False,
                'result': f'Server xatosi: {str(e)}'
            }, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def check_chain_rule(request):
    """
    Chain qoidalarini tekshirish - Qo'shimcha ma'lumotlar bilan
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_answers = data.get('answers', {})

            if not user_answers:
                return JsonResponse({
                    'found': False,
                    'result': 'Ma\'lumot kiritilmagan'
                })

            # Frontend ID -> DB format + Qo'yilgan talab qo'shish
            db_answers = {}
            for frontend_id, value in user_answers.items():
                db_atribut_index = int(frontend_id) - 1
                db_answers[str(db_atribut_index)] = value

            # Qo'yilgan talab (atribut 7, key 26) qo'shish
            db_answers['7'] = 'Qo\'shimcha tekshiruv kerak'

            print(f"Chain answers: {db_answers}")

            # Barcha qoidalarni qayta tekshirish
            rules = Rule.objects.all().order_by('id')

            for rule in rules:
                rule_matches = True
                print(f"\n=== Chain Qoida #{rule.id} tekshirilmoqda ===")

                for condition in rule.shartlar:
                    attr_index = condition['atribut']
                    val_key = condition['qiymat']

                    if str(attr_index) not in db_answers:
                        rule_matches = False
                        break

                    user_val = db_answers[str(attr_index)]
                    try:
                        attr_val = AttributeValue.objects.get(key=val_key)
                    except AttributeValue.DoesNotExist:
                        rule_matches = False
                        break

                    if not qiymat_mos(user_val, attr_val.qiymat):
                        rule_matches = False
                        break

                if rule_matches:
                    print(f"✅ Chain Qoida #{rule.id} MOS KELDI!")
                    result_key = rule.natija

                    try:
                        result_value = AttributeValue.objects.get(key=result_key)
                        return JsonResponse({
                            'found': True,
                            'result': result_value.qiymat,
                            'rule_id': rule.id
                        })
                    except AttributeValue.DoesNotExist:
                        continue

            # Mos chain qoida topilmadi
            return JsonResponse({
                'found': False,
                'result': 'Qo\'shimcha ma\'lumotlar bilan ham mos qoida topilmadi'
            })

        except Exception as e:
            print(f"Chain xatolik: {str(e)}")
            return JsonResponse({
                'found': False,
                'result': f'Server xatosi: {str(e)}'
            }, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def user_form(request):
    return render(request, 'index.html', {'page': 'user'})


@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('decision:admin_panel')
        else:
            return render(request, 'index.html', {
                'page': 'login',
                'error': 'Login yoki parol noto\'g\'ri!'
            })

    return render(request, 'index.html', {'page': 'login'})


def logout_view(request):
    logout(request)
    return redirect('decision:user_form')


@login_required(login_url='decision:login')
def admin_panel(request):
    return redirect('/admin/')


def reset_form(request):
    return redirect('decision:user_form')