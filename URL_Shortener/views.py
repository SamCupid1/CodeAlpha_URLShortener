import json
from json import JSONDecodeError

import qrcode
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, F
from django.db.models.functions import TruncDate
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST
from django_ratelimit.core import is_ratelimited

from .forms import RegistrationForm, URLCreateForm
from .models import ClickEvent, ShortURL


def home(request):
    return render(
        request,
        "URL_Shortener/home.html",
        {"url_form": URLCreateForm()},
    )


def _dashboard_context(user, url_form=None):
    links = user.short_urls.all()
    today = timezone.localdate()
    start_date = today - timezone.timedelta(days=13)
    daily_clicks = (
        ClickEvent.objects.filter(short_url__user=user, clicked_at__date__gte=start_date)
        .annotate(day=TruncDate("clicked_at"))
        .values("day")
        .annotate(total=Count("id"))
        .order_by("day")
    )
    click_totals = {row["day"].isoformat(): row["total"] for row in daily_clicks}
    chart_labels = [(start_date + timezone.timedelta(days=offset)).isoformat() for offset in range(14)]
    chart_values = [click_totals.get(day, 0) for day in chart_labels]

    return {
        "links": links,
        "total_clicks": sum(link.clicks for link in links),
        "chart_labels": chart_labels,
        "chart_values": chart_values,
        "url_form": url_form or URLCreateForm(),
    }


@login_required
def dashboard(request):
    return render(
        request,
        "URL_Shortener/dashboard.html",
        _dashboard_context(request.user),
    )


@require_POST
def shorten(request):
    if not request.user.is_authenticated and is_ratelimited(
        request,
        group="anonymous_url_creation",
        key="ip",
        rate="10/h",
        method="POST",
        increment=True,
    ):
        return render(
            request,
            "URL_Shortener/home.html",
            {"url_form": URLCreateForm(request.POST), "rate_limited": True},
            status=429,
        )

    form = URLCreateForm(request.POST)
    if not form.is_valid():
        if request.user.is_authenticated:
            return render(
                request,
                "URL_Shortener/dashboard.html",
                _dashboard_context(request.user, form),
                status=400,
            )
        return render(request, "URL_Shortener/home.html", {"url_form": form}, status=400)

    short_url = ShortURL.create(
        original_url=form.cleaned_data["url"],
        user=request.user if request.user.is_authenticated else None,
    )
    return redirect("shortener:created", code=short_url.short_code)


def created(request, code):
    short_url = get_object_or_404(ShortURL, short_code=code)
    return render(request, "URL_Shortener/created.html", {"short_url": short_url})


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created. Sign in to continue.")
            return redirect("login")
    else:
        form = RegistrationForm()
    return render(request, "URL_Shortener/register.html", {"form": form})


@require_http_methods(["GET", "POST"])
@login_required
def api_urls(request):
    if request.method == "GET":
        page_number = request.GET.get("page", "1")
        if not page_number.isdecimal() or int(page_number) < 1:
            return JsonResponse({"error": "Page must be a positive integer."}, status=400)
        page = Paginator(request.user.short_urls.all(), 50).get_page(page_number)
        results = [_serialize_url(request, item) for item in page.object_list]
        return JsonResponse(
            {
                "count": page.paginator.count,
                "next": page.next_page_number() if page.has_next() else None,
                "previous": page.previous_page_number() if page.has_previous() else None,
                "results": results,
            }
        )

    try:
        payload = json.loads(request.body)
    except (JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Request body must contain valid JSON."}, status=400)
    if not isinstance(payload, dict):
        return JsonResponse({"error": "Request body must be a JSON object."}, status=400)

    form = URLCreateForm({"url": payload.get("url", "")})
    if not form.is_valid():
        return JsonResponse({"errors": form.errors.get_json_data()}, status=400)
    short_url = ShortURL.create(original_url=form.cleaned_data["url"], user=request.user)
    return JsonResponse(_serialize_url(request, short_url), status=201)


@require_http_methods(["GET", "DELETE"])
@login_required
def api_url_detail(request, code):
    short_url = get_object_or_404(request.user.short_urls, short_code=code)
    if request.method == "DELETE":
        short_url.delete()
        return HttpResponse(status=204)
    return JsonResponse(_serialize_url(request, short_url))


def _serialize_url(request, short_url):
    short_link = request.build_absolute_uri(
        reverse("shortener:redirect", args=[short_url.short_code])
    )
    return {
        "id": short_url.pk,
        "url": short_url.original_url,
        "short_code": short_url.short_code,
        "short_url": short_link,
        "clicks": short_url.clicks,
        "created_at": short_url.created_at.isoformat(),
    }


def redirect_short_url(request, code):
    short_url = get_object_or_404(ShortURL, short_code=code)
    with transaction.atomic():
        ClickEvent.objects.create(short_url=short_url)
        ShortURL.objects.filter(pk=short_url.pk).update(clicks=F("clicks") + 1)
    return redirect(short_url.original_url)


def qr_code(request, code):
    short_url = get_object_or_404(ShortURL, short_code=code)
    short_link = request.build_absolute_uri(
        reverse("shortener:redirect", args=[short_url.short_code])
    )
    image = qrcode.make(short_link)
    response = HttpResponse(content_type="image/png")
    image.save(response, format="PNG")
    response["Cache-Control"] = "public, max-age=86400"
    return response


@require_POST
@login_required
def delete_url(request, code):
    short_url = get_object_or_404(request.user.short_urls, short_code=code)
    short_url.delete()
    messages.success(request, "Short link deleted.")
    return redirect("shortener:dashboard")
