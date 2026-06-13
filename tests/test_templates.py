import httpx
import respx

from tests.helpers import BASE_URL, request_body


@respx.mock
def test_list_templates(client):
    respx.get(f"{BASE_URL}/v1/templates").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "slug": "welcome",
                        "channel": "email",
                        "description": "Welcome email",
                        "status": "active",
                        "updatedAt": "2026-01-01T00:00:00Z",
                    }
                ]
            },
        )
    )
    templates = client.templates.list()
    assert len(templates) == 1
    assert templates[0].slug == "welcome"
    assert templates[0].channel == "email"


@respx.mock
def test_get_template_with_version(client):
    respx.get(f"{BASE_URL}/v1/templates/welcome").mock(
        return_value=httpx.Response(
            200,
            json={
                "slug": "welcome",
                "channel": "email",
                "description": None,
                "status": "active",
                "updatedAt": "2026-01-01T00:00:00Z",
                "currentVersion": {
                    "versionNumber": 3,
                    "variables": [{"name": "name", "type": "string", "required": True}],
                    "publishedAt": "2026-01-01T00:00:00Z",
                },
            },
        )
    )
    detail = client.templates.get("welcome")
    assert detail.slug == "welcome"
    assert detail.current_version.version_number == 3
    assert detail.current_version.variables[0].name == "name"
    assert detail.current_version.variables[0].required is True


@respx.mock
def test_render_template(client):
    route = respx.post(f"{BASE_URL}/v1/templates/welcome/render").mock(
        return_value=httpx.Response(
            200,
            json={
                "channel": "email",
                "output": {"subject": "Hi Ada", "html": "<p>Hi Ada</p>"},
                "missing": ["dashboardUrl"],
            },
        )
    )
    result = client.templates.render("welcome", {"name": "Ada"})
    assert result.channel == "email"
    assert result.output["subject"] == "Hi Ada"
    assert result.missing == ["dashboardUrl"]
    assert request_body(route.calls.last.request) == {"vars": {"name": "Ada"}}
