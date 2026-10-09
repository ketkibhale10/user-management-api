"""Custom API documentation pages: styled Swagger UI (/docs), Scalar (/scalar) and ReDoc (/redoc)."""
from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import HTMLResponse

from app.core.config import settings

SWAGGER_PARAMETERS = {
    "persistAuthorization": True,       # keep the token after a page refresh
    "displayRequestDuration": True,     # show how long "Try it out" calls take
    "filter": True,                     # search box for endpoints
    "docExpansion": "none",             # start with all sections collapsed
    "defaultModelsExpandDepth": -1,     # hide the bulky "Schemas" section
    "tryItOutEnabled": True,            # no need to click "Try it out" each time
    "syntaxHighlight.theme": "monokai",
}

SWAGGER_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root { --brand: #6366f1; --brand-dark: #4f46e5; --bg: #f5f7fb; --text: #1e293b; }

body { background: var(--bg); font-family: 'Inter', sans-serif; }
.swagger-ui, .swagger-ui .opblock .opblock-summary-description, .swagger-ui .btn,
.swagger-ui table thead tr th, .swagger-ui .tab li, .swagger-ui label,
.swagger-ui .opblock-tag, .swagger-ui .parameter__name, .swagger-ui .model-title {
  font-family: 'Inter', sans-serif !important; color: var(--text);
}
.swagger-ui code, .swagger-ui pre, .swagger-ui .opblock-summary-path {
  font-family: 'JetBrains Mono', monospace !important;
}

/* Page header */
.swagger-ui .info { margin: 0; padding: 40px 32px; border-radius: 16px; margin-top: 24px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 55%, #ec4899 100%); }
.swagger-ui .info .title, .swagger-ui .info p, .swagger-ui .info a, .swagger-ui .info li { color: #fff !important; }
.swagger-ui .info .title { font-weight: 700; font-size: 2.2rem; }
.swagger-ui .info .title small { background: rgba(255,255,255,.25); }
.swagger-ui .info .title small.version-stamp pre { background: transparent; }

/* Authorize + scheme bar */
.swagger-ui .scheme-container { background: transparent; box-shadow: none; padding: 20px 0; }
.swagger-ui .btn.authorize { border-color: var(--brand); color: var(--brand); border-radius: 10px; font-weight: 600; }
.swagger-ui .btn.authorize svg { fill: var(--brand); }
.swagger-ui .btn.authorize:hover { background: var(--brand); color: #fff; }
.swagger-ui .btn.authorize:hover svg { fill: #fff; }
.swagger-ui .btn.execute { background: var(--brand); border-color: var(--brand); border-radius: 8px; }
.swagger-ui .btn.execute:hover { background: var(--brand-dark); }

/* Tag headings */
.swagger-ui .opblock-tag { font-size: 1.25rem; font-weight: 600; border-bottom: 1px solid #e2e8f0; }

/* Endpoint cards */
.swagger-ui .opblock { border-radius: 12px; border-width: 1px; box-shadow: 0 2px 8px rgba(15,23,42,.06);
  margin-bottom: 14px; overflow: hidden; background: #fff; }
.swagger-ui .opblock .opblock-summary { padding: 8px 12px; }
.swagger-ui .opblock .opblock-summary-method { border-radius: 8px; font-weight: 700; min-width: 80px; }
.swagger-ui .opblock.opblock-get    { border-color: #3b82f6; background: rgba(59,130,246,.05); }
.swagger-ui .opblock.opblock-post   { border-color: #10b981; background: rgba(16,185,129,.05); }
.swagger-ui .opblock.opblock-patch  { border-color: #f59e0b; background: rgba(245,158,11,.06); }
.swagger-ui .opblock.opblock-delete { border-color: #ef4444; background: rgba(239,68,68,.05); }
.swagger-ui .opblock.opblock-get    .opblock-summary-method { background: #3b82f6; }
.swagger-ui .opblock.opblock-post   .opblock-summary-method { background: #10b981; }
.swagger-ui .opblock.opblock-patch  .opblock-summary-method { background: #f59e0b; }
.swagger-ui .opblock.opblock-delete .opblock-summary-method { background: #ef4444; }

/* Code blocks and inputs */
.swagger-ui .highlight-code > .microlight, .swagger-ui .opblock-body pre.microlight { border-radius: 10px; }
.swagger-ui input[type=text], .swagger-ui textarea, .swagger-ui select { border-radius: 8px; }
"""

SCALAR_HTML = f"""<!doctype html>
<html>
  <head>
    <title>{settings.APP_NAME} - Scalar</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
  </head>
  <body>
    <script id="api-reference" data-url="/openapi.json"></script>
    <script>
      document.getElementById('api-reference').dataset.configuration = JSON.stringify({{
        theme: 'purple', layout: 'modern', darkMode: true
      }});
    </script>
    <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
  </body>
</html>"""


def register_docs(app: FastAPI) -> None:
    """Attach the three documentation UIs. FastAPI's default /docs and /redoc must be disabled."""

    @app.get("/docs", include_in_schema=False)
    def swagger_ui() -> HTMLResponse:
        page = get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{settings.APP_NAME} - Swagger UI",
            swagger_ui_parameters=SWAGGER_PARAMETERS,
            oauth2_redirect_url=None,
        )
        html = page.body.decode("utf-8").replace("</head>", f"<style>{SWAGGER_CSS}</style></head>")
        return HTMLResponse(html)

    @app.get("/redoc", include_in_schema=False)
    def redoc() -> HTMLResponse:
        return get_redoc_html(openapi_url=app.openapi_url, title=f"{settings.APP_NAME} - ReDoc")

    @app.get("/scalar", include_in_schema=False)
    def scalar() -> HTMLResponse:
        return HTMLResponse(SCALAR_HTML)