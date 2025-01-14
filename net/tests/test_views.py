import ipaddress

from net.enums import ConnectionStatus
from net.models import Connection
from peering.enums import DeviceStatus
from peering.models import AutonomousSystem, InternetExchange, Router
from utils.testing import ViewTestCases


class ConnectionTestCase(ViewTestCases.ContextualObjectViewTestCase):
    model = Connection

    @classmethod
    def setUpTestData(cls):
        local_as = AutonomousSystem.objects.create(
            asn=64501, name="Autonomous System 1", affiliated=True
        )
        internet_exchange_point = InternetExchange.objects.create(
            name="Internet Exchange 1", slug="ix-1", local_autonomous_system=local_as
        )
        router = Router.objects.create(
            name="test",
            hostname="test.example.com",
            status=DeviceStatus.ENABLED,
            local_autonomous_system=local_as,
        )
        Connection.objects.bulk_create(
            [
                Connection(
                    status=ConnectionStatus.ENABLED,
                    vlan=2001,
                    ipv6_address="2001:db8::1/64",
                    internet_exchange_point=internet_exchange_point,
                    router=router,
                ),
                Connection(
                    status=ConnectionStatus.ENABLED,
                    vlan=2002,
                    ipv6_address="2001:db8::2/64",
                    internet_exchange_point=internet_exchange_point,
                    router=router,
                ),
                Connection(
                    status=ConnectionStatus.DISABLED,
                    vlan=2003,
                    ipv6_address="2001:db8::3/64",
                    internet_exchange_point=internet_exchange_point,
                    router=router,
                ),
            ]
        )

        cls.form_data = {
            "peeringdb_netixlan": None,
            "status": ConnectionStatus.ENABLED,
            "vlan": 2004,
            "ipv6_address": ipaddress.ip_interface("2001:db8::4/64"),
            "ipv4_address": None,
            "internet_exchange_point": internet_exchange_point.pk,
            "router": router.pk,
            "description": "",
            "interface": "",
            "comments": "",
            "tags": [],
        }

        cls.bulk_edit_data = {"status": ConnectionStatus.DISABLED}
