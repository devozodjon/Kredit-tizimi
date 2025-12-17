from django.shortcuts import render, redirect, get_object_or_404
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


# ==================== USER QISMI ====================

@csrf_exempt
def user_form(request):
    """Foydalanuvchi uchun kredit arizasi formasi"""
    return render(request, 'index.html')


@csrf_exempt
def find_matching_rule(request):
    """Frontend'dan barcha ma'lumotlarni olib, eng mos qoidani topadi"""
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

                for condition in rule.shartlar:
                    attr_index = condition['atribut']
                    val_key = condition['qiymat']

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

                if rule_matches:
                    print(f"✅ Qoida #{rule.id} MOS KELDI!")
                    result_key = rule.natija

                    try:
                        result_value = AttributeValue.objects.get(key=result_key)
                    except AttributeValue.DoesNotExist:
                        continue

                    # CHAIN LOGIC
                    if result_key == 26:
                        print(f"🔗 Chain natija: Qo'shimcha tekshiruv kerak")
                        return JsonResponse({
                            'found': True,
                            'chain_required': True,
                            'result': result_value.qiymat,
                            'rule_id': rule.id,
                            'message': 'Qo\'shimcha ma\'lumot kiritish kerak'
                        })

                    return JsonResponse({
                        'found': True,
                        'result': result_value.qiymat,
                        'rule_id': rule.id
                    })

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
    """Chain qoidalarini tekshirish"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_answers = data.get('answers', {})

            if not user_answers:
                return JsonResponse({
                    'found': False,
                    'result': 'Ma\'lumot kiritilmagan'
                })

            db_answers = {}
            for frontend_id, value in user_answers.items():
                db_atribut_index = int(frontend_id) - 1
                db_answers[str(db_atribut_index)] = value

            # Qo'yilgan talab qo'shish
            db_answers['7'] = 'Qo\'shimcha tekshiruv kerak'

            print(f"Chain answers: {db_answers}")

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


def reset_form(request):
    """Qayta boshlash"""
    return redirect('decision:user_form')


# ==================== ADMIN AUTHENTICATION ====================

@csrf_exempt
def admin_login_view(request):
    """Admin login sahifasi"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('decision:admin_panel')
        else:
            return render(request, 'index.html', {
                'page': 'admin_login',
                'error': 'Login yoki parol noto\'g\'ri!'
            })

    return render(request, 'index.html', {'page': 'admin_login'})


def logout_view(request):
    """Admin logout"""
    logout(request)
    return redirect('decision:user_form')


@login_required(login_url='decision:admin_login')
def admin_panel(request):
    """Admin panel asosiy sahifa"""
    return render(request, 'index.html', {'page': 'admin_panel'})


# ==================== ATTRIBUTE CRUD ====================

@login_required(login_url='decision:admin_login')
def get_attributes(request):
    """Barcha atributlarni olish"""
    attributes = Attribute.objects.all()
    data = [{
        'id': attr.id,
        'nomi': attr.nomi,
        'qiymatlar_soni': attr.qiymatlar.count()
    } for attr in attributes]
    return JsonResponse({'attributes': data})


@login_required(login_url='decision:admin_login')
@csrf_exempt
def create_attribute(request):
    """Yangi atribut yaratish"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nomi = data.get('nomi')

            if not nomi:
                return JsonResponse({'error': 'Nomi kiritilmagan'}, status=400)

            attribute = Attribute.objects.create(nomi=nomi)
            return JsonResponse({
                'success': True,
                'attribute': {
                    'id': attribute.id,
                    'nomi': attribute.nomi
                }
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=400)


@login_required(login_url='decision:admin_login')
@csrf_exempt
def update_attribute(request, attr_id):
    """Atributni yangilash"""
    if request.method == 'POST':
        try:
            attribute = get_object_or_404(Attribute, id=attr_id)
            data = json.loads(request.body)

            attribute.nomi = data.get('nomi', attribute.nomi)
            attribute.save()

            return JsonResponse({
                'success': True,
                'attribute': {
                    'id': attribute.id,
                    'nomi': attribute.nomi
                }
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=400)


@login_required(login_url='decision:admin_login')
@csrf_exempt
def delete_attribute(request, attr_id):
    """Atributni o'chirish"""
    if request.method == 'DELETE':
        try:
            attribute = get_object_or_404(Attribute, id=attr_id)
            attribute.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=400)


# ==================== ATTRIBUTE VALUE CRUD ====================

@login_required(login_url='decision:admin_login')
def get_values(request):
    """Barcha qiymatlarni olish"""
    values = AttributeValue.objects.select_related('attribute').all()
    data = [{
        'id': val.id,
        'attribute_id': val.attribute.id,
        'attribute_nomi': val.attribute.nomi,
        'qiymat': val.qiymat,
        'key': val.key
    } for val in values]
    return JsonResponse({'values': data})


@login_required(login_url='decision:admin_login')
@csrf_exempt
def create_value(request):
    """Yangi qiymat yaratish"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            attribute_id = data.get('attribute_id')
            qiymat = data.get('qiymat')
            key = data.get('key')

            if not all([attribute_id, qiymat, key]):
                return JsonResponse({'error': 'Barcha maydonlar to\'ldirilishi kerak'}, status=400)

            attribute = get_object_or_404(Attribute, id=attribute_id)
            value = AttributeValue.objects.create(
                attribute=attribute,
                qiymat=qiymat,
                key=key
            )

            return JsonResponse({
                'success': True,
                'value': {
                    'id': value.id,
                    'attribute_nomi': attribute.nomi,
                    'qiymat': value.qiymat,
                    'key': value.key
                }
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=400)


@login_required(login_url='decision:admin_login')
@csrf_exempt
def update_value(request, val_id):
    """Qiymatni yangilash"""
    if request.method == 'POST':
        try:
            value = get_object_or_404(AttributeValue, id=val_id)
            data = json.loads(request.body)

            if 'attribute_id' in data:
                attribute = get_object_or_404(Attribute, id=data['attribute_id'])
                value.attribute = attribute

            value.qiymat = data.get('qiymat', value.qiymat)
            value.key = data.get('key', value.key)
            value.save()

            return JsonResponse({
                'success': True,
                'value': {
                    'id': value.id,
                    'attribute_nomi': value.attribute.nomi,
                    'qiymat': value.qiymat,
                    'key': value.key
                }
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=400)


@login_required(login_url='decision:admin_login')
@csrf_exempt
def delete_value(request, val_id):
    """Qiymatni o'chirish"""
    if request.method == 'DELETE':
        try:
            value = get_object_or_404(AttributeValue, id=val_id)
            value.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=400)


# ==================== RULE CRUD ====================

@login_required(login_url='decision:admin_login')
def get_rules(request):
    """Barcha qoidalarni olish"""
    rules = Rule.objects.all().order_by('id')
    data = [{
        'id': rule.id,
        'shartlar': rule.shartlar,
        'natija': rule.natija,
        'shartlar_soni': len(rule.shartlar)
    } for rule in rules]
    return JsonResponse({'rules': data})


@login_required(login_url='decision:admin_login')
@csrf_exempt
def create_rule(request):
    """Yangi qoida yaratish"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            shartlar = data.get('shartlar')
            natija = data.get('natija')

            if not shartlar or natija is None:
                return JsonResponse({'error': 'Shartlar va natija kiritilishi kerak'}, status=400)

            rule = Rule.objects.create(
                shartlar=shartlar,
                natija=natija
            )

            return JsonResponse({
                'success': True,
                'rule': {
                    'id': rule.id,
                    'shartlar': rule.shartlar,
                    'natija': rule.natija
                }
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=400)


@login_required(login_url='decision:admin_login')
@csrf_exempt
def update_rule(request, rule_id):
    """Qoidani yangilash"""
    if request.method == 'POST':
        try:
            rule = get_object_or_404(Rule, id=rule_id)
            data = json.loads(request.body)

            rule.shartlar = data.get('shartlar', rule.shartlar)
            rule.natija = data.get('natija', rule.natija)
            rule.save()

            return JsonResponse({
                'success': True,
                'rule': {
                    'id': rule.id,
                    'shartlar': rule.shartlar,
                    'natija': rule.natija
                }
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=400)


@login_required(login_url='decision:admin_login')
@csrf_exempt
def delete_rule(request, rule_id):
    """Qoidani o'chirish"""
    if request.method == 'DELETE':
        try:
            rule = get_object_or_404(Rule, id=rule_id)
            rule.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=400)