# GLPI Impact Builder

Proyecto Open Source para automatizar, inspeccionar e importar mapas de impacto de GLPI, con foco especial en GLPI Cloud donde no existe acceso al código servidor.

## Estado

**v0.2.0 en desarrollo.** El proyecto ya incluye navegador Playwright, autenticación/sesiones, modelo de nodos y relaciones, inspección del objeto \`GLPIImpact\`, exportación/importación JSON, navegación al mapa, dry-run de relaciones y persistencia protegida mediante la propia UI.

La persistencia en GLPI Cloud todavía debe validarse contra una instancia real antes de considerarse estable. El proyecto no asume que un HTTP 200 significa que una relación fue guardada.

## Instalación

\`\`\`bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
playwright install chromium
\`\`\`

En Windows PowerShell, activa el entorno con \`.venv\\Scripts\\Activate.ps1\`.

Copia \`.env.example\` a un archivo local \`.env\` o define las variables en tu shell. No subas credenciales ni archivos Playwright \`storage_state\` al repositorio.

## Flujo de investigación GLPI Cloud

El enfoque actual utiliza el objeto JavaScript que GLPI carga en el navegador:

\`\`\`text
sesión autenticada
    -> abrir objeto GLPI
    -> pestaña Impact
    -> window.GLPIImpact
    -> inspeccionar nodos/edges
    -> preparar cambio
    -> computeDelta()
    -> dry-run
    -> confirmación explícita
    -> Guardar mediante UI GLPI
    -> capturar petición redactada
    -> comprobar delta posterior
\`\`\`

No se reproduce manualmente el endpoint privado \`ajax/impact.php\` hasta disponer de evidencia runtime suficiente.

## Caso de prueba actual

Los ejemplos de relaciones utilizan por defecto:

\`\`\`text
Computer::15 -> Computer::16
\`\`\`

Para inspeccionar un mapa:

\`\`\`bash
python examples/inspect_impact.py
\`\`\`

Para probar la relación únicamente en el workspace, sin guardarla:

\`\`\`bash
python examples/test_edge_workspace.py
\`\`\`

Para preparar el cambio y ejecutar dry-run:

\`\`\`bash
python examples/save_edge.py
\`\`\`

El guardado real requiere además:

\`\`\`text
GLPI_CONFIRM_SAVE=YES
\`\`\`

Ese valor constituye una barrera deliberada contra escrituras accidentales.

## Seguridad

El recorder de red oculta headers sensibles y campos conocidos de autenticación, contraseña, CSRF, tokens, secrets y API keys antes de exponer las peticiones capturadas. Aun así, revisa cualquier captura antes de compartirla públicamente.

Los archivos \`.env\` y \`*storage-state*.json\` están excluidos mediante \`.gitignore\`.

## Pruebas

\`\`\`bash
pytest
\`\`\`

Las pruebas unitarias cubren actualmente el modelo de grafo, detección de cambios de persistencia y redacción de secretos. Las pruebas contra GLPI Cloud requieren una sesión/instancia real y no forman parte de las pruebas unitarias.

## Roadmap

- [x] Bootstrap del proyecto
- [x] Browser wrapper
- [x] Authentication/session state
- [x] Modelo Impact
- [x] Inspector runtime \`GLPIImpact\`
- [x] Export/import JSON
- [x] Navegación al workspace Impact
- [x] Dry-run de relaciones
- [x] Persistencia UI protegida
- [x] Captura segura de tráfico de persistencia
- [ ] Validar \`Computer::15 -> Computer::16\` contra GLPI Cloud
- [ ] Replicar el flujo interno real de creación de edge si \`cy.add()\` no genera delta
- [ ] Importación Excel/CSV aplicada al workspace
- [ ] CLI
- [ ] CI
- [ ] GUI
- [ ] v1.0.0
