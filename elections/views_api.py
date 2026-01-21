from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Candidate, Party, District



def districts_by_province(request): 
    """
    Returns districts for a given province (AJAX helper)
    GET param: province_id
    """
    province_id = request.GET.get('province_id') 
    districts_list = []

    if province_id:
        districts = District.objects.filter(province_id=province_id).values('id', 'name')
        districts_list = list(districts)

    return JsonResponse(districts_list, safe=False)

@login_required
def voter_profile(request):
    user = request.user
    return JsonResponse({
        "username": user.username,
        "province": {"id": user.province.id, "name": user.province.name},
        "district": {"id": user.district.id, "name": user.district.name},
        "electoral_area": {
            "id": user.electoral_area.id,
            "name": user.electoral_area.name
        }
    })


@login_required
def candidate_list(request):
    candidates = Candidate.objects.filter(
        electoral_area=request.user.electoral_area
    ).values("id", "name")
    return JsonResponse(list(candidates), safe=False)


@login_required
def party_list(request):
    parties = Party.objects.filter(is_active=True).values("id", "name", "symbol")
    return JsonResponse(list(parties), safe=False)
