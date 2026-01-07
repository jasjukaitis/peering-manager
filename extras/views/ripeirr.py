import urllib.parse

import requests
from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import View

from devices.enums import DeviceStatus
from peering.models import AutonomousSystem, InternetExchange
from peering_manager.views.generic import (
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
)
from utils.views import PermissionRequiredMixin, register_model_view

from ..filtersets import RipeIrrFilterSet
from ..forms import RipeIrrEntityUpdateForm, RipeIrrFilterForm, RipeIrrForm
from ..models import RipeIrr
from ..tables import RipeIrrTable

__all__ = (
    "RipeIrrDeleteView",
    "RipeIrrEditView",
    "RipeIrrListView",
    "RipeIrrUpdateEntityView",
    "RipeIrrView",
)


@register_model_view(RipeIrr, name="list", path="", detail=False)
class RipeIrrListView(ObjectListView):
    permission_required = "extras.view_ripeirr"
    queryset = RipeIrr.objects.all()
    filterset = RipeIrrFilterSet
    filterset_form = RipeIrrFilterForm
    table = RipeIrrTable
    template_name = "extras/ripeirr/list.html"


@register_model_view(RipeIrr)
class RipeIrrView(ObjectView):
    permission_required = "extras.view_ripeirr"
    queryset = RipeIrr.objects.all()

    def get_extra_context(self, request, instance):
        return {
            "active_tab": "main",
        }


@register_model_view(model=RipeIrr, name="add", detail=False)
@register_model_view(model=RipeIrr, name="edit")
class RipeIrrEditView(ObjectEditView):
    queryset = RipeIrr.objects.all()
    form = RipeIrrForm
    template_name = "extras/ripeirr/add_edit.html"


@register_model_view(RipeIrr, name="delete")
class RipeIrrDeleteView(ObjectDeleteView):
    permission_required = "extras.delete_ripeirr"
    queryset = RipeIrr.objects.all()


class RipeIrrUpdateEntityView(PermissionRequiredMixin, View):
    permission_required = "extras.update_ripeirr_entity"

    def _get_body_object(self, instance):
        ixps = {}
        for ixp in InternetExchange.objects.all():
            all_as = ixp.get_autonomous_systems()
            if all_as:
                ixps[ixp.name] = {
                    4: {"import": [], "export": []},
                    6: {"import": [], "export": []},
                }

                for single_as in all_as:
                    if not single_as.irr_as_set:
                        continue
                    ixp_peering_connections = (
                        single_as.get_ixp_peering_sessions()
                        .select_related("ixp_connection")
                        .filter(
                            ixp_connection__internet_exchange_point_id=ixp.id,
                            status=DeviceStatus.ENABLED,
                        )
                        .order_by("autonomous_system_id", "ip_address")
                        .distinct("autonomous_system_id", "ip_address")
                        .all()
                    )
                    for ixp_peering_connection in ixp_peering_connections:
                        version = ixp_peering_connection.ip_address.version
                        # Sanitize
                        irr_as_set = (
                            single_as.irr_as_set.split(" ")[0]
                            .replace(",", "")
                            .split(":")[-1]
                        )
                        if (single_as.asn, irr_as_set) in ixps[ixp.name][version][
                            "import"
                        ]:
                            continue
                        ixps[ixp.name][version]["import"].append(
                            (single_as.asn, irr_as_set)
                        )
                        ixps[ixp.name][version]["export"].append(
                            (single_as.asn, instance.irr_as_set)
                        )

        custom_body = [
            ("remarks", "+---------------------------------------------------------+")
        ]
        for name, ixp in ixps.items():
            if ixp[4]["import"]:
                custom_body.append(("remarks", f"| Peering {name} IPv4"))
                custom_body.append(
                    (
                        "remarks",
                        "+---------------------------------------------------------+",
                    )
                )

                for from_as, accept_irr in ixp[4]["import"]:
                    custom_body.append(
                        ("import", f"from AS{from_as} accept {accept_irr}")
                    )

                custom_body.append(("remarks", "+"))

                for to_as, announce in ixp[4]["export"]:
                    custom_body.append(("export", f"to AS{to_as} announce {announce}"))

            if ixp[4]["import"] and ixp[6]["import"]:
                custom_body.append(
                    (
                        "remarks",
                        "+---------------------------------------------------------+",
                    )
                )

            if ixp[6]["import"]:
                custom_body.append(("remarks", f"| Peering {name} IPv6"))
                custom_body.append(
                    (
                        "remarks",
                        "+---------------------------------------------------------+",
                    )
                )

                for from_as, accept_irr in ixp[6]["import"]:
                    custom_body.append(
                        (
                            "mp-import",
                            f"afi ipv6.unicast from AS{from_as} accept {accept_irr}",
                        )
                    )

                custom_body.append(("remarks", "+"))

                for to_as, announce in ixp[6]["export"]:
                    custom_body.append(
                        (
                            "mp-export",
                            f"afi ipv6.unicast to AS{to_as} announce {announce}",
                        )
                    )

            if ixp[4]["import"] or ixp[6]["import"]:
                custom_body.append(
                    (
                        "remarks",
                        "+---------------------------------------------------------+",
                    )
                )

        response = requests.get(
            f"{settings.RIPE_IRR_BASE_URL}aut-num/AS{instance.asn}",
            headers={"accept": "application/json"},
        )

        body = []
        add_line = True
        for row in response.json()["objects"]["object"][0]["attributes"]["attribute"]:
            if row["name"] == "admin-c":
                add_line = True
            if add_line:
                body.append((row["name"], row["value"]))
            if row["value"] == "| IX - Internet Exchange":
                add_line = False
                body.extend(custom_body)

        return body

    def get(self, request, *args, **kwargs):
        instance = get_object_or_404(AutonomousSystem, pk=kwargs["pk"])

        preview = "\n".join(
            f"{key}:{' ' * (16 - len(key))}{value}"
            for key, value in self._get_body_object(instance)
        )

        form = RipeIrrEntityUpdateForm()
        return render(
            request,
            "extras/ripeirr/update_entity.html",
            {"instance": instance, "form": form, "preview": preview},
        )

    def post(self, request, *args, **kwargs):
        instance = get_object_or_404(AutonomousSystem, pk=kwargs["pk"])
        form = RipeIrrEntityUpdateForm(data=request.POST)
        if not form.is_valid():
            raise
        ripe_irr = form.cleaned_data["ripe_irr"]

        data = {
            "objects": {
                "object": [
                    {
                        "source": {"id": "RIPE"},
                        "attributes": {
                            "attribute": [
                                {"name": name, "value": value}
                                for name, value in self._get_body_object(instance)
                            ]
                        },
                    }
                ]
            }
        }
        response = requests.put(
            f"{settings.RIPE_IRR_BASE_URL}aut-num/AS{instance.asn}?password={urllib.parse.quote_plus(ripe_irr.password)}",
            json=data,
            headers={"accept": "application/json"},
        )
        if response.status_code == 200:
            messages.success(request, "Entity updated successfully.")
        else:
            messages.error(request, "Entity could not be updated.")
        return redirect(instance.get_absolute_url())
