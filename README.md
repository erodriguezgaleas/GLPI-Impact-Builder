# GLPI Impact Builder

Proyecto Open Source para automatizar, inspeccionar e importar mapas de impacto de GLPI, con foco especial en GLPI Cloud donde no existe acceso al código servidor.

## Estado

**v0.2.0 en desarrollo.** El proyecto ya incluye navegador Playwright, autenticación/sesiones, modelo de nodos y relaciones, inspección del objeto `GLPIImpact`, exportación/importación JSON, navegación al mapa, dry-run de relaciones, persistencia protegida mediante la propia UI y captura redactada de evidencia HTTP.

La persistencia en GLPI Cloud todavía debe validarse contra una instancia real antes de considerarse estable. El proyecto no asume que un HTTP 200 significa que una relación fue guardada: la verificación fuerte requiere reabrir el workspace y comprobar que el edge continúa presente.

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
playwright install chromium
```

En Windows PowerShell, activa el entorno con `.venv\Scripts\Activate.ps1`.

Copia `.env.example` a un archivo local `.env` o define las variables en tu shell. No subas credenciales ni archivos Playwright `storage_state` al repositorio.

## Flujo de investigación GLPI Cloud

```text
sesión autenticada
    -> abrir objeto GLPI
    -> pestaña Impact
    -> window.GLPIImpact
    -> inspeccionar nodos/edges y métodos runtime
    -> preparar cambio
    -> computeDelta()
    -> dry-run
    -> confirmación explícita
    -> Guardar mediante UI GLPI
    -> capturar XHR/fetch redactado + status HTTP
    -> reabrir workspace
    -> comprobar que el edge continúa presente
```

No se reproduce manualmente el endpoint privado `ajax/impact.php` hasta disponer de evidencia runtime suficiente.

## Caso de prueba actual

Los ejemplos de relaciones utilizan por defecto:

```text
Computer::15 -> Computer::16
```

Para inspeccionar los métodos runtime relevantes al flujo nativo de edges:

```bash
python examples/inspect_edge_runtime.py
```

Para probar la relación únicamente en el workspace, sin guardarla:

```bash
python examples/test_edge_workspace.py
```

Para preparar el cambio y ejecutar dry-run:

```bash
python examples/save_edge.py
```

El guardado real requiere `GLPI_CONFIRM_SAVE=YES`. Ese valor constituye una barrera deliberada contra escrituras accidentales.

Para descubrir el tráfico real de un Save nativo sin automatizar la escritura:

```bash
python examples/capture_impact_save.py
```

El script abre el workspace, inicia una ventana corta de captura y espera que se realice manualmente exactamente un Save. La captura local se guarda en `GLPI_CAPTURE_PATH`.

## Seguridad

El recorder de red oculta headers sensibles, parámetros de URL y campos conocidos de autenticación, contraseña, CSRF, tokens, secrets y API keys. Los cuerpos JSON y form-urlencoded se redactan antes de almacenarse; cuerpos opacos/no reconocidos se omiten por completo.

Aun así, revisa cualquier captura antes de compartirla públicamente. Los archivos `.env`, `*storage-state*.json`, `impact-network-capture*.json` e `impact-runtime-report*.json` están excluidos mediante `.gitignore`.

## Pruebas

```bash
pytest
```

Las pruebas unitarias cubren el modelo de grafo, reconocimiento de deltas, persistencia y redacción de evidencia de red. Las pruebas contra GLPI Cloud requieren una sesión/instancia real y no forman parte de las pruebas unitarias.

Existe un workflow de GitHub Actions para ejecutar `pytest -q` en Python 3.11. Su ejecución efectiva debe confirmarse en GitHub antes de considerar CI validado.

## Roadmap

- [x] Bootstrap del proyecto
- [x] Browser wrapper
- [x] Authentication/session state
- [x] Modelo Impact
- [x] Inspector runtime `GLPIImpact`
- [x] Export/import JSON
- [x] Navegación al workspace Impact
- [x] Dry-run de relaciones
- [x] Persistencia UI protegida
- [x] Captura segura de tráfico de persistencia
- [x] Verificación post-save mediante reapertura del workspace
- [x] Workflow CI configurado
- [ ] Confirmar ejecución CI en GitHub
- [ ] Validar `Computer::15 -> Computer::16` contra GLPI Cloud
- [ ] Replicar el flujo interno real de creación de edge si `cy.add()` no genera delta
- [ ] Importación Excel/CSV aplicada al workspace
- [ ] CLI
- [ ] GUI
- [ ] v1.0.0
