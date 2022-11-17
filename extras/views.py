import urllib.parse

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import View

from peering.enums import DeviceStatus
from peering.models import InternetExchange
from peering.models.models import AutonomousSystem, InternetExchange
from peering_manager.views.generics import (
    BulkDeleteView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
    PermissionRequiredMixin,
)
from utils.tables import paginate_table

from .filters import (
    ConfigContextFilterSet,
    ExportTemplateFilterSet,
    IXAPIFilterSet,
    JobResultFilterSet,
    RipeIrrFilterSet,
)
from .forms import (
    ConfigContextAssignmentForm,
    ConfigContextFilterForm,
    ConfigContextForm,
    ExportTemplateFilterForm,
    ExportTemplateForm,
    IXAPIFilterForm,
    IXAPIForm,
    JobResultFilterForm,
    RipeIrrEntityUpdateForm,
    RipeIrrFilterForm,
    RipeIrrForm,
)
from .models import (
    IXAPI,
    ConfigContext,
    ConfigContextAssignment,
    ExportTemplate,
    JobResult,
    RipeIrr,
)
from .tables import (
    ConfigContextAssignmentTable,
    ConfigContextTable,
    ExportTemplateTable,
    IXAPITable,
    JobResultTable,
    RipeIrrTable,
)


class ConfigContextListView(ObjectListView):
    permission_required = "extras.view_configcontext"
    queryset = ConfigContext.objects.all()
    filterset = ConfigContextFilterSet
    filterset_form = ConfigContextFilterForm
    table = ConfigContextTable
    template_name = "extras/configcontext/list.html"


class ConfigContextView(ObjectView):
    permission_required = "extras.view_configcontext"
    queryset = ConfigContext.objects.all()

    def get_extra_context(self, request, instance):
        if request.GET.get("format") in ("json", "yaml"):
            format = request.GET.get("format")
            if request.user.is_authenticated:
                request.user.preferences.set(
                    "configcontext.format", format, commit=True
                )
        elif request.user.is_authenticated:
            format = request.user.preferences.get("configcontext.format", "json")
        else:
            format = "json"

        config_context_assignments = ConfigContextAssignment.objects.filter(
            config_context=instance
        )
        assignments_table = ConfigContextAssignmentTable(config_context_assignments)
        assignments_table.columns.hide("config_context")
        paginate_table(assignments_table, request)

        return {
            "assignments_table": assignments_table,
            "assignment_count": ConfigContextAssignment.objects.filter(
                config_context=instance
            ).count(),
            "configcontext_format": format,
            "active_tab": "main",
        }


class ConfigContextAddView(ObjectEditView):
    permission_required = "extras.add_configcontext"
    queryset = ConfigContext.objects.all()
    model_form = ConfigContextForm
    template_name = "extras/configcontext/add_edit.html"


class ConfigContextEditView(ObjectEditView):
    permission_required = "extras.change_configcontext"
    queryset = ConfigContext.objects.all()
    model_form = ConfigContextForm
    template_name = "extras/configcontext/add_edit.html"


class ConfigContextDeleteView(ObjectDeleteView):
    permission_required = "extras.delete_configcontext"
    queryset = ConfigContext.objects.all()


class ConfigContextBulkDeleteView(BulkDeleteView):
    permission_required = "extras.delete_configcontext"
    queryset = ConfigContext.objects.all()
    filterset = ConfigContextFilterSet
    table = ConfigContextTable


class ConfigContextAssignmentEditView(ObjectEditView):
    permission_required = "extras.edit_configcontextassignment"
    queryset = ConfigContextAssignment.objects.all()
    model_form = ConfigContextAssignmentForm
    template_name = "extras/configcontextassignment/add_edit.html"

    def alter_object(self, instance, request, args, kwargs):
        if not instance.pk:
            content_type = get_object_or_404(
                ContentType, pk=request.GET.get("content_type")
            )
            instance.object = get_object_or_404(
                content_type.model_class(), pk=request.GET.get("object_id")
            )
        return instance


class ConfigContextAssignmentDeleteView(ObjectDeleteView):
    permission_required = "extras.delete_configcontextassignment"
    queryset = ConfigContextAssignment.objects.all()


class ObjectConfigContextView(ObjectView):
    base_template = None
    template_name = "extras/object_configcontext.html"

    def get_extra_context(self, request, instance):
        if request.GET.get("format") in ("json", "yaml"):
            format = request.GET.get("format")
            if request.user.is_authenticated:
                request.user.preferences.set(
                    "configcontext.format", format, commit=True
                )
        elif request.user.is_authenticated:
            format = request.user.preferences.get("configcontext.format", "json")
        else:
            format = "json"

        return {
            "configcontext_format": format,
            "base_template": self.base_template,
            "active_tab": "config-context",
            "rendered_context": instance.get_config_context(),
        }


class ExportTemplateListView(ObjectListView):
    permission_required = "extras.view_exporttemplate"
    queryset = ExportTemplate.objects.all()
    filterset = ExportTemplateFilterSet
    filterset_form = ExportTemplateFilterForm
    table = ExportTemplateTable
    template_name = "extras/exporttemplate/list.html"


class ExportTemplateView(ObjectView):
    permission_required = "extras.view_exporttemplate"
    queryset = ExportTemplate.objects.all()

    def get_extra_context(self, request, instance):
        return {"active_tab": "main"}


class ExportTemplateAddView(ObjectEditView):
    permission_required = "extras.add_exporttemplate"
    queryset = ExportTemplate.objects.all()
    model_form = ExportTemplateForm
    template_name = "extras/exporttemplate/add_edit.html"


class ExportTemplateEditView(ObjectEditView):
    permission_required = "extras.change_exporttemplate"
    queryset = ExportTemplate.objects.all()
    model_form = ExportTemplateForm
    template_name = "extras/exporttemplate/add_edit.html"


class ExportTemplateDeleteView(ObjectDeleteView):
    permission_required = "extras.delete_exporttemplate"
    queryset = ExportTemplate.objects.all()


class ExportTemplateBulkDeleteView(BulkDeleteView):
    permission_required = "extras.delete_exporttemplate"
    queryset = ExportTemplate.objects.all()
    filterset = ExportTemplateFilterSet
    table = ExportTemplateTable


class IXAPIListView(ObjectListView):
    permission_required = "extras.view_ixapi"
    queryset = IXAPI.objects.all()
    filterset = IXAPIFilterSet
    filterset_form = IXAPIFilterForm
    table = IXAPITable
    template_name = "extras/ixapi/list.html"


class IXAPIView(ObjectView):
    permission_required = "extras.view_ixapi"
    queryset = IXAPI.objects.all()

    def get_extra_context(self, request, instance):
        return {
            "internet_exchange_points": InternetExchange.objects.filter(
                ixapi_endpoint=instance
            ),
            "active_tab": "main",
        }


class IXAPIAddView(ObjectEditView):
    permission_required = "extras.add_ixapi"
    queryset = IXAPI.objects.all()
    model_form = IXAPIForm
    template_name = "extras/ixapi/add_edit.html"


class IXAPIEditView(ObjectEditView):
    permission_required = "extras.change_ixapi"
    queryset = IXAPI.objects.all()
    model_form = IXAPIForm
    template_name = "extras/ixapi/add_edit.html"


class IXAPIDeleteView(ObjectDeleteView):
    permission_required = "extras.delete_ixapi"
    queryset = IXAPI.objects.all()


class JobResultListView(ObjectListView):
    permission_required = "extras.view_jobresult"
    queryset = JobResult.objects.all()
    filterset = JobResultFilterSet
    filterset_form = JobResultFilterForm
    table = JobResultTable
    template_name = "extras/jobresult/list.html"


class JobResultDeleteView(ObjectDeleteView):
    permission_required = "extras.delete_jobresult"
    queryset = JobResult.objects.all()


class JobResultBulkDeleteView(BulkDeleteView):
    permission_required = "extras.delete_jobresult"
    queryset = JobResult.objects.all()
    filterset = JobResultFilterSet
    table = JobResultTable


class JobResultView(ObjectView):
    permission_required = "extras.view_jobresult"
    queryset = JobResult.objects.all()


class RipeIrrListView(ObjectListView):
    permission_required = "extras.view_ripeirr"
    queryset = RipeIrr.objects.all()
    filterset = RipeIrrFilterSet
    filterset_form = RipeIrrFilterForm
    table = RipeIrrTable
    template_name = "extras/ripeirr/list.html"


class RipeIrrView(ObjectView):
    permission_required = "extras.view_ripeirr"
    queryset = RipeIrr.objects.all()

    def get_context(self, request, **kwargs):
        instance = get_object_or_404(RipeIrr, **kwargs)
        return {
            "instance": instance,
            "active_tab": "main",
        }


class RipeIrrAddView(ObjectEditView):
    permission_required = "extras.add_ripeirr"
    queryset = RipeIrr.objects.all()
    model_form = RipeIrrForm
    template_name = "extras/ripeirr/add_edit.html"


class RipeIrrEditView(ObjectEditView):
    permission_required = "extras.change_ripeirr"
    queryset = RipeIrr.objects.all()
    model_form = RipeIrrForm
    template_name = "extras/ripeirr/add_edit.html"


class RipeIrrDeleteView(ObjectDeleteView):
    permission_required = "extras.delete_ripeirr"
    queryset = RipeIrr.objects.all()
    return_url = "extras:ripeirr_list"


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
