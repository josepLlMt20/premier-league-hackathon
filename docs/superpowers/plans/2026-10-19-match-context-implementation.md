# Match Context Assistant Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar una aplicación Azure que ponga al día a aficionados sin revelar eventos posteriores a su reproducción y prepare briefings verificables para comentaristas.

**Architecture:** Un backend Python sirve una web React compilada y ejecuta el análisis, las consultas temporales y tres agentes. Un registro inmutable de eventos separa el momento ocurrido de su disponibilidad; todas las salidas se construyen desde una instantánea acotada. SQLite cubre desarrollo local y Azure Table Storage la persistencia del despliegue, mediante el mismo contrato.

**Tech Stack:** Python 3.13, FastAPI, Pydantic, Microsoft Agent Framework con proveedor Foundry, Azure Identity, Azure Data Tables; Node 22, React, TypeScript y Vite; pytest, Vitest, Testing Library y Playwright; Azure Container Apps y Bicep.

**Spec:** [Diseño aprobado](../specs/2026-10-19-match-context-design.md).

## Global Constraints

- «El aficionado es el usuario principal. El comentarista es un segundo usuario del mismo motor y de la misma evidencia.»
- «Un encuentro principal de 90 minutos, más tres variantes reproducibles para evaluación. Equipos, jugadores y eventos ficticios.»
- «Dos profundidades, español e inglés, equipo favorito opcional y dos roles de audiencia.»
- «Los cálculos numéricos y el control temporal pertenecen al código.»
- «Una solicitud define `from_sequence` exclusivo y `to_sequence` inclusivo.»
- «El cliente recibe únicamente los datos autorizados para su punto de reproducción; no precarga el partido completo.»
- «Cada solicitud inicia un contexto acotado a esa instantánea; no reutiliza conversaciones ni memorias de otro espectador o de un punto posterior.»
- «Una salida inválida o rechazada admite un único intento de reparación con motivos explícitos. Después se descarta esa historia.»
- «Si el modelo falla, la reproducción y las estadísticas siguen disponibles.»
- «La demo objetivo dura 110 segundos.»
- El alcance excluye vídeo real, voz, cuentas, apuestas y múltiples partidos. No publicar mocks como ejecuciones reales del modelo.
- Ninguna creación de recursos de pago, llamada facturable o publicación se ejecuta durante la preparación de este plan. La fase Azure requiere acceso y presupuesto confirmados.
- Cada tarea termina con su comprobación y un commit. Los tests de red usan opt-in; las pruebas habituales no consumen cuota de Foundry.

## Review Focus

1. Dos espectadores y respuestas fuera de orden: una generación del minuto posterior no puede aparecer al retroceder; pruebas en tareas 5 y 6.
2. Correcciones tardías, identificadores repetidos y datos de otro partido: preservar la historia conocida en cada límite; pruebas en tareas 1, 2 y 3.
3. Inicio del partido, intervalo vacío y pocas observaciones: mostrar contexto limitado sin fabricar una tendencia; pruebas en tareas 3 y 5.
4. Contexto previo del modelo y evidencia manipulada: herramientas, prompts, números y referencias quedan limitados a una instantánea nueva; pruebas en tarea 4.
5. Reinicio del contenedor, paginación del almacén y caída del proveedor: conservar eventos y mantener el modo factual explícito; pruebas en tareas 2, 4 y 8.

## Decisiones técnicas

Un contenedor sirve `/api/*` y los recursos de `web/dist`; Vite usa proxy al backend durante desarrollo. La separación es por módulos, sin microservicios ni agentes alojados individualmente. El despliegue inicial tiene una sola réplica para que exista un único escritor de ingesta.

Las versiones directas comprobadas en los registros el 19 de octubre son Python local 3.13.2 y Node 22.23.1; Foundry 1.15.0, core 1.22.0, FastAPI 0.149.0, Pydantic 2.14.1, Data Tables 12.7.0, Identity 1.26.0, pytest 9.1.1 y httpx 0.28.1; React 19.3.1, Vite 8.3.4, TypeScript 7.0.2, plugin-react 6.1.2, Vitest 5.0.5 y Playwright 1.64.1. La tarea 0 resuelve y fija las dependencias transitivas en lockfiles; estas versiones aún no se han instalado ni probado juntas.

La integración de agentes usa `Agent` y `agent_framework.foundry.FoundryChatClient`. El deployment se lee de `FOUNDRY_MODEL`; no se presupone un modelo disponible en la cuenta. Autenticación local con Azure CLI y en Azure con identidad administrada. No se necesita crear una clave de OpenAI Platform.

Fuentes técnicas: [patrón de agentes en código con Foundry](https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/responses-api), [cambios del SDK Python](https://learn.microsoft.com/en-us/agent-framework/support/upgrade/python-2026-significant-changes), [cliente de Azure Tables](https://learn.microsoft.com/en-us/python/api/overview/azure/data-tables-readme?view=azure-python), [identidad de Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/managed-identity).

## Estructura de archivos

| Ruta | Responsabilidad |
| --- | --- |
| `pyproject.toml`, `requirements.lock`, `requirements-dev.lock` | Dependencias Python fijadas y configuración de pruebas. |
| `.env.example`, `src/match_context/config.py` | Configuración tipada y modos `foundry`, `scripted` y `factual`. |
| `src/match_context/domain/{events,contracts}.py` | Eventos, límites, preferencias y contratos de respuesta. |
| `src/match_context/simulation/{generator,fixtures,ingest}.py` | Escenarios reproducibles y escritor de eventos recibidos. |
| `src/match_context/storage/{base,sqlite,azure_tables}.py` | Contrato de registro y adaptadores persistentes. |
| `src/match_context/analysis/{snapshot,metrics,patterns,evidence}.py` | Reconstrucción temporal, métricas, patrones y referencias. |
| `src/match_context/agents/{base,tools,foundry,orchestrator,validation,fallback}.py` | Agentes, herramientas acotadas, revisión y degradación. |
| `src/match_context/service/{context,cache}.py` | Solicitudes de contexto y caché por perfil e instantánea. |
| `src/match_context/api/{app,routes,schemas}.py` | API, errores, recursos estáticos y contratos públicos. |
| `scripts/{preflight,export_openapi,evaluate,seed_cloud,smoke_cloud}.py` | Preparación, contratos, evaluación y comprobaciones de entorno. |
| `web/src/{api,domain,features,components,styles}` | Cliente tipado, reproducción y vistas de aficionado y comentarista. |
| `tests/{unit,integration,live}` y `web/{src,e2e}` | Casos de dominio, almacenes, API, componentes y recorridos. |
| `infra/{main,storage,app,roles}.bicep`, `Dockerfile`, `.dockerignore` | Despliegue de un contenedor y persistencia Azure. |
| `docs/{readiness,data-dictionary,evaluation,demo-script,submission}.md` | Preparación, datos, resultados medidos, demo y entrega. |

## Contratos compartidos

Todos los modelos Pydantic rechazan campos adicionales y los identificadores externos se validan antes de formar consultas. El reloj canónico es un entero de segundos transcurridos, de 0 a 5400; los eventos simultáneos se ordenan por secuencia. El MVP no modela tiempo añadido ni una pausa real de descanso.

- `MatchEvent`: `match_id`, `event_id` único, `sequence` positiva, `occurred_second`, `available_second`, `period`, `kind`, `team_id`, `player_id` opcional, `start`/`end` opcionales y atributos tipados por evento. `kind` pertenece a `pass|recovery|turnover|pressure|shot|goal|substitution|correction`. Una corrección referencia un evento anterior del mismo partido y puede anularlo; no elimina registros.
- `ContextRequest`: `match_id`, `from_sequence >= 0`, `to_sequence >= from_sequence`, `role=fan|commentator`, `depth=simple|detailed`, `language=es|en`, `favorite_team_id` opcional.
- `BoundedSnapshot`: metadata estática, eventos conocidos, eventos efectivos tras correcciones, marcador, límite y hash del prefijo. Sus datos son inmutables.
- `MetricFact`: `fact_id`, nombre, valor numérico, unidad, intervalo y `event_ids`. `StoryCandidate`: patrón, prioridad, `fact_ids`, `event_ids` y limitaciones.
- `Claim`: `claim_id`, `kind=observed|interpretation`, texto con marcadores de hechos, `fact_ids`, `event_ids` y límites. Los números y nombres del partido se insertan desde hechos validados, no desde cifras libres del modelo.
- `ContextResult`: solicitud, `snapshot_id`, `status=verified|factual|insufficient`, síntesis, hasta tres tarjetas, hechos públicos, referencias, motivos de rechazo no sensibles y `trace_id`. Cada tarjeta incluye titular, explicación, frase sugerida, limitación opcional y `overlay_text` de hasta 140 caracteres.
- `Trace`: roles ejecutados, herramientas, decisiones, duración y uso del proveedor; nunca secretos ni razonamientos privados del modelo. El cliente recibe una traza resumida, no prompts ni cuerpos internos completos.

Propiedad de los tipos: `domain/events.py` define `MatchMetadata` (equipos, jugadores y dirección de ataque), `MatchEvent` y `GeneratedMatch` (metadata y eventos); `domain/contracts.py` define los restantes contratos de dominio, incluidos `ContextCard`, `EvidenceBundle` y `OverlayPayload`. `agents/base.py` define `AgentOutput` (claims o decisiones del revisor), `ScopedTools` y `ValidationReport` (aceptados, rechazados y códigos). `api/schemas.py` define `MatchView` (snapshot, reloj y eventos recientes) y `ResolvedCursor` (secuencia y segundo disponible). Los reportes de preparación, smoke y evaluación se definen en sus respectivos scripts; cada caso de evaluación contiene solicitud, hechos esperados y referencias prohibidas.

`AgentRunner.run`, `orchestrate` y `ContextService.get_context` son asíncronos. `EventLog` mantiene un contrato síncrono; el servicio ejecuta su E/S mediante `asyncio.to_thread`, fuera del bucle de la API.

Las fixtures completas y sus manifiestos permanecen en recursos privados del backend. La protección de spoilers es una propiedad de los contratos de la aplicación: no pretende ocultar el desenlace a quien abra deliberadamente los datos sintéticos del repositorio público.

## Task 0: Entorno reproducible y preparación de Azure

**Files:** crear `pyproject.toml`, locks, `.env.example`, `src/match_context/__init__.py`, `src/match_context/config.py`, `scripts/preflight.py`, `tests/unit/test_config.py`, `web/package.json`, `web/package-lock.json`, `docs/readiness.md`; ampliar `.gitignore` con `.venv/`, `.pytest_cache/`, `__pycache__/`, `web/node_modules/`, `web/dist/` y reportes temporales.

**Interfaces:** `Settings.from_env() -> Settings`; `check_readiness(settings: Settings) -> ReadinessReport`. Campos: `app_env=development|test|production`, `storage_backend`, `agent_mode`, `foundry_project_endpoint`, `foundry_model`, `azure_table_endpoint`, `azure_client_id`, `max_model_calls=7`, `max_tool_calls=8`, `max_output_tokens=1200`, `context_timeout_seconds=10`. Sus variables de entorno usan los mismos nombres en mayúsculas. El reporte expone disponibilidad y faltas de configuración, sin valores de credenciales.

- [ ] Escribir y ejecutar pruebas de configuración: sin endpoint o modelo, `foundry` falla con un error de campo; `factual` arranca sin Azure. `scripted` exige entorno de pruebas o desarrollo. Ejecutar `python -m pytest tests/unit/test_config.py -q` y confirmar fallo inicial atribuible al módulo ausente.
- [ ] Crear `.venv` con Python 3.13, instalar las versiones indicadas y sus herramientas de test, generar locks y repetir la prueba hasta PASS. Crear el paquete frontend con versiones fijadas y `npm.cmd --prefix web install --package-lock-only`; comprobar resolución y scripts sin construir UI todavía. Registrar versiones realmente resueltas.
- [ ] Confirmar con el usuario suscripción, acceso a Foundry y presupuesto antes de tareas facturables. Azure CLI no está en el PATH inspeccionado; instalarla desde su distribución oficial cuando se ejecute la preparación. El usuario completa el login. `preflight` debe informar recursos inaccesibles, no inventar permisos ni cambiar de proveedor silenciosamente. Guardar estado y modelo disponible en `docs/readiness.md`, sin secretos.
- [ ] Commit: `chore: establish reproducible runtime and readiness checks`.

**Salida verificable:** instalación reproducible y diagnóstico honesto. Las tareas locales 1 a 3 pueden avanzar mientras se resuelve Azure; el smoke real de agentes y el despliegue quedan condicionados al acceso y presupuesto.

## Task 1: Eventos y cuatro escenarios coherentes

**Files:** crear `domain/events.py`, `domain/contracts.py`, `simulation/generator.py`, `simulation/fixtures.py`, `tests/conftest.py`, `tests/unit/test_simulation.py`, `docs/data-dictionary.md`.

**Interfaces:** `generate_match(scenario: str, seed: int) -> GeneratedMatch`; `validate_event(event: MatchEvent) -> None`. `GeneratedMatch` contiene metadata y eventos; el manifiesto de evaluación se guarda aparte. En `tests/conftest.py`, definir factories `make_event(**overrides) -> MatchEvent` y fixtures `scenario_main`, `scenario_neutral`, `scenario_sterile`, `scenario_correction`.

- [x] Añadir pruebas: misma semilla produce el mismo hash; secuencias únicas y contiguas; reloj y coordenadas válidos; tiros y goles conservan marcador; una corrección no puede apuntar a otro partido ni a un evento futuro. Ejecutar `python -m pytest tests/unit/test_simulation.py -q` y observar los fallos antes de implementar.
- [x] Implementar escenarios `main/7`, `neutral/11`, `sterile/19`, `correction/23`, equipos Ámbar FC y Cobalto United y jugadores ficticios. Coordenadas globales: campo de 105 por 68 metros; metadata fija dirección de ataque por equipo y periodo. Al menos diez eventos útiles por ventana evaluada. El patrón principal contiene cuatro recuperaciones altas frente a una en la ventana anterior, con tiros posteriores; el neutral no incluye un cambio intencional.
- [x] Separar el manifiesto de verdad del contenido disponible a agentes. Documentar cada atributo y la calidad de ocasión como heurística del simulador. Repetir pruebas, inspeccionar un encuentro generado y confirmar PASS.
- [x] Commit: `feat: generate coherent synthetic match scenarios`.

## Task 2: Registro persistente e ingesta reproducible

**Files:** crear `storage/base.py`, `storage/sqlite.py`, `storage/azure_tables.py`, `simulation/ingest.py`, `tests/integration/test_event_log.py`, `tests/integration/test_azure_tables.py`.

**Interfaces:** `EventLog.append(event: MatchEvent) -> bool` devuelve falso solo para un duplicado idéntico; `head(match_id: str) -> int`; `read_through(match_id: str, cutoff: int) -> tuple[MatchEvent, ...]`. `Ingestor.tick(match_id: str, available_second: int) -> int` añade únicamente el prefijo disponible. Un duplicado con contenido distinto produce `EventConflict`.

- [x] Escribir los casos de contrato para ambos adaptadores: insertar dos veces no duplica; conflicto no muta; reiniciar la instancia conserva el prefijo; paginación no omite eventos; `read_through(..., 10)` nunca devuelve 11; un evento inválido no avanza la cabecera. Ejecutar `python -m pytest tests/integration/test_event_log.py tests/integration/test_azure_tables.py -q` con transporte falso del SDK Azure y confirmar fallo inicial.
- [x] Implementar SQLite con transacciones. En Azure usar tabla `MatchEvents`, `PartitionKey=match_id`, `RowKey` de doce dígitos para secuencia y una entidad de cabecera separada dentro de la partición. Crear evento y actualizar cabecera con ETag en una transacción. Consumir toda la paginación del SDK y aplicar filtros parametrizados por partición y cutoff. Resolver respuestas ambiguas leyendo la clave antes de repetir una escritura.
- [x] Implementar un único escritor de ingesta a velocidad 30x configurable, con estado persistente e inserción idempotente. Pausa, reinicio y velocidad de un espectador afectan su reproducción; no reinician el flujo compartido. Si la ingesta falla, detener avance y exponer último evento recibido. Repetir pruebas y confirmar PASS.
- [x] Commit: `feat: persist immutable event prefixes and replay ingestion`.

## Task 3: Instantáneas, métricas y evidencia temporal

**Files:** crear `analysis/snapshot.py`, `analysis/metrics.py`, `analysis/patterns.py`, `analysis/evidence.py`, `tests/unit/test_snapshot.py`, `tests/unit/test_metrics.py`, `tests/unit/test_patterns.py`.

**Interfaces:** `build_snapshot(events: tuple[MatchEvent, ...], cutoff: int, metadata: MatchMetadata) -> BoundedSnapshot`; `compute_facts(snapshot: BoundedSnapshot, start: int, end: int) -> tuple[MetricFact, ...]`; `detect_stories(snapshot: BoundedSnapshot, request: ContextRequest) -> tuple[StoryCandidate, ...]`; `resolve_evidence(snapshot: BoundedSnapshot, ids: tuple[str, ...]) -> EvidenceBundle`.

- [x] Probar corrección tardía: gol en secuencia 10 y anulación en 30; marcador en 20 es 1-0 y en 30 es 0-0. Probar evidencia ajena o posterior, inicio con menos datos, ventana vacía, empate de prioridades y ausencia de tendencia en neutral. Ejecutar `python -m pytest tests/unit/test_snapshot.py tests/unit/test_metrics.py tests/unit/test_patterns.py -q` y confirmar fallos pertinentes.
- [x] Reconstruir solo registros con disponibilidad hasta cutoff; aplicar anulaciones únicamente desde su llegada. Calcular con ese conjunto marcador, tiros, recuperaciones, presión y actividad territorial. El intervalo de selección es `(from_sequence, to_sequence]`; la comparación usa ventanas de hasta 300 segundos de juego anteriores al final, sin mirar al futuro.
- [x] Fijar reglas iniciales visibles: recuperación alta en tercio ofensivo normalizado y aumento de al menos dos recuperaciones; ocasiones con al menos dos tiros y aumento de al menos 30 puntos de calidad acumulada; actividad territorial con mínimo diez pases completados por ventana y cambio de cuota de al menos 20 puntos porcentuales. Calidad de tiro = `round(100 * max(0, 1 - distancia_m / 50) * factor_presion, 2)`, con distancia euclídea al centro de la portería contraria y factor 0,7 bajo presión o 1 en otro caso. Es una heurística, no xG calibrado. Clasificar insuficiencia cuando falta muestra. Cada hecho conserva denominador e intervalo.
- [x] Mantener ranking reproducible; el agente puede elegir entre candidatos respaldados, pero no cambiar sus números. Evidencia incluye todo evento usado en el cálculo y comparación, dentro del cutoff. Repetir pruebas y añadir un caso donde un equipo favorito no cambia los hechos.
- [x] Commit: `feat: derive bounded match facts and explainable patterns`.

## Task 4: Tres agentes con revisión y fallos controlados

**Files:** crear `agents/base.py`, `agents/tools.py`, `agents/foundry.py`, `agents/orchestrator.py`, `agents/validation.py`, `agents/fallback.py`, `tests/unit/test_orchestration.py`, `tests/unit/test_claim_validation.py`, `tests/live/test_foundry.py`.

**Interfaces:** `AgentRunner.run(role: str, payload: dict, tools: ScopedTools) -> AgentOutput`; `make_scoped_tools(snapshot: BoundedSnapshot, facts: tuple[MetricFact, ...]) -> ScopedTools`; `orchestrate(snapshot: BoundedSnapshot, request: ContextRequest, runner: AgentRunner) -> ContextResult`; `validate_claims(result: ContextResult, snapshot: BoundedSnapshot, facts: tuple[MetricFact, ...]) -> ValidationReport`; `build_factual_result(snapshot, request, facts) -> ContextResult`.

- [x] Crear runners de prueba que inventen un hecho, pidan eventos posteriores, emitan JSON inválido y rechacen dos veces una historia. Assert: herramientas deniegan acceso futuro, referencias inválidas no se publican, hay como máximo una reparación, timeout produce `status='factual'`, y una nueva solicitud no recibe mensajes de otra. Ejecutar `python -m pytest tests/unit/test_orchestration.py tests/unit/test_claim_validation.py -q` y confirmar fallo antes de implementación.
- [x] Implementar pipeline analista -> redactor -> revisor. Herramientas solo de lectura: listar candidatos, consultar hechos e inspeccionar referencias dentro de una instantánea cerrada. Sesiones nuevas por solicitud, sin búsquedas externas ni memoria persistente. El analista limita candidatos a tres; el redactor entrega claims tipados; el revisor devuelve aceptación o códigos de rechazo. Tras una reparación rechazada, descartar la historia y sintetizar solo lo aceptado.
- [x] Insertar nombres y números desde hechos validados mediante marcadores `{{fact:ID}}` y `{{entity:ID}}`; rechazar marcadores desconocidos y cifras libres del modelo antes de renderizar. Revisar también referencias semánticas, interpretaciones y lenguaje causal, admitiendo la limitación de esa revisión. Compartir validación para síntesis, tarjetas y overlay. Crear fallback factual bilingüe identificado; no completar con narrativas rechazadas.
- [x] Crear adaptador Foundry con las versiones fijadas y `response_format` Pydantic. Contabilizar llamadas reales incluyendo invocación de herramientas y reparaciones: límites de configuración 7 llamadas de modelo, 8 herramientas, 1200 tokens de salida por llamada y deadline total de 10 s. Registrar uso y decisión, no razonamiento privado. Con Azure y presupuesto confirmados, ejecutar `python -m pytest tests/live/test_foundry.py -m live -q`: debe mostrar llamadas y herramientas reales, una salida validada y aislamiento entre solicitudes. Sin acceso, marcar este smoke pendiente explícitamente.
- [x] Commit: `feat: orchestrate grounded Foundry briefings with review`.

## Task 5: API pública acotada y servicio de contexto

**Files:** crear `service/context.py`, `service/cache.py`, `api/app.py`, `api/routes.py`, `api/schemas.py`, `scripts/export_openapi.py`, `tests/integration/test_api.py`, `tests/unit/test_cache.py`.

**Interfaces:** `ContextService.get_context(request: ContextRequest) -> ContextResult`; `ContextCache.key(request, snapshot_hash: str) -> str`; `create_app(settings: Settings, log: EventLog, runner: AgentRunner) -> FastAPI`.

Rutas: `GET /healthz`; `GET /api/matches` devuelve solo metadata estática; `GET /api/matches/{id}/head` devuelve secuencia y reloj de ingesta, sin marcador futuro; `GET /api/matches/{id}/cursor?available_second=S` devuelve la última secuencia disponible hasta S, o cero, y rechaza S posterior al reloj ingerido; `GET /api/matches/{id}/view?to_sequence=N` devuelve estado y hasta cien eventos recientes del prefijo; `POST /api/context`; `POST /api/evidence` con partido, cutoff y referencias. El cursor permite buscar cualquier instante ya recibido sin descargar el encuentro entero. El esquema OpenAPI se exporta a `web/openapi.json`; `web/src/api/schema.d.ts` se genera con openapi-typescript.

- [x] Escribir pruebas HTTP: cutoff posterior a cabecera produce 422; partido inexistente 404; evidencia posterior nunca devuelve datos; inicio vacío devuelve `insufficient`; caché separa idioma, rol, profundidad, favorito, intervalo y hash. Resolver un cursor anterior a los cien eventos recientes, eventos simultáneos y una corrección tardía según disponibilidad; pedir un segundo futuro produce 422. Simular respuestas B y A completadas en orden inverso conservando la solicitud correspondiente. Ejecutar `python -m pytest tests/integration/test_api.py tests/unit/test_cache.py -q` y confirmar fallo inicial.
- [x] Construir solicitudes desde un único snapshot, propagar deadline, devolver errores con códigos estables y excluir fixture, manifiesto, prompts y configuración del JSON público. Usar caché en memoria de máximo 128 resultados; al reiniciar se reconstruye desde el registro persistente. Dos generaciones concurrentes como máximo y error 429 explícito con reintento; las consultas de datos no requieren un modelo operativo.
- [x] Arrancar backend local con ingesta, repetir pruebas y exportar OpenAPI. Comprobar que un resultado factual se distingue de uno verificado. Commit: `feat: expose temporal match context and evidence API`.

## Task 6: Recorrido completo del aficionado

**Files:** crear `web/index.html`, configuración Vite/TS/Vitest, `web/src/main.tsx`, `web/src/App.tsx`, `web/src/api/client.ts`, `web/src/domain/playback.ts`, `web/src/features/viewer/{Viewer,PlaybackControls,CatchUpPanel,EvidencePanel}.tsx`, `web/src/components/{Pitch,Timeline,Status}.tsx`, `web/src/styles/{tokens,app}.css`, `web/src/features/viewer/Viewer.test.tsx`, `web/e2e/fan.spec.ts`.

**Interfaces:** `resolveCursor(matchId: string, second: number, signal: AbortSignal): Promise<ResolvedCursor>`, `fetchView(matchId: string, cutoff: number, signal: AbortSignal): Promise<MatchView>` y `requestContext(request: ContextRequest, signal: AbortSignal): Promise<ContextResult>` usan tipos generados. `PlaybackState` conserva cursor, desde, velocidad, preferencias y `requestKey`; `applyContext(state, result, requestKey)` ignora respuestas obsoletas. `requestKey` es un contador local creciente capturado por cada petición; no se toma del contenido cacheado.

- [ ] Probar que retroceder no muestra el resultado de una solicitud posterior; cambiar idioma conserva cursor; abrir evidencia y regresar mantiene reproducción; controles de pausa y velocidad no mutan la ingesta. Ejecutar `npm.cmd --prefix web test -- --run` y comprobar fallos funcionales iniciales.
- [ ] Construir la vista con marcador al cutoff, campo SVG que representa el evento y su trayectoria, cronología disponible y panel de contexto. Precargar únicamente metadata estática. Resolver el segundo elegido mediante `resolveCursor`, acotado por la cabecera ingerida, y cargar después su vista; cancelar solicitudes anteriores con AbortController y validar también requestKey en ambas respuestas. Persistir solo preferencias, no datos del partido, en localStorage.
- [ ] Aplicar diseño visual deliberado durante ejecución con las habilidades de frontend pertinentes; usar tokens, etiquetas, foco, teclado, contraste y movimiento reducido. La síntesis aparece primero; la evidencia se abre bajo demanda. Mantener un recorrido usable en 390 px y en escritorio.
- [ ] Ejecutar recorrido contra backend real en modo scripted explícito mediante `npm.cmd --prefix web run test:e2e -- fan.spec.ts`; inspeccionar escritorio y móvil, red y localStorage para detectar contenido futuro. La prueba scripted no reemplaza la evaluación Foundry de tarea 9. Commit: `feat: deliver spoiler-aware fan catch-up experience`.

## Task 7: Briefing profesional y overlay desde la misma evidencia

**Files:** crear `web/src/features/commentator/{Commentator,BriefingCard,OverlayPreview,TracePanel}.tsx`, `web/src/features/commentator/export.ts`, `web/src/features/commentator/Commentator.test.tsx`, `web/e2e/commentator.spec.ts`; modificar `web/src/App.tsx` y el selector de audiencia.

**Interfaces:** `exportBriefing(result: ContextResult): Blob`; `overlayFor(card: ContextCard, snapshotId: string): OverlayPayload`, con texto <= 140 caracteres, cutoff, tiempo mostrado y referencias. Consumir `ContextService`, sin motor separado para el profesional.

- [ ] Probar que cambiar de rol conserva el partido y que las tarjetas incluyen intervalos y referencias; una tarjeta rechazada no se puede exportar; exportar una instantánea anterior no usa marcador actual. Ejecutar Vitest y confirmar fallo antes de implementar.
- [ ] Construir hasta tres tarjetas con titular, frase, evidencia e interpretación diferenciada. Añadir copiar texto, descargar JSON y vista de overlay que recorta sin cambiar el sentido ni eliminar la limitación esencial; si no cabe, usar una versión breve validada. Mostrar resumen de roles y decisiones, sin prompts ni cadenas privadas de razonamiento.
- [ ] Ejecutar `npm.cmd --prefix web run test:e2e -- commentator.spec.ts`, abrir la misma evidencia desde ambos modos y comprobar cifras equivalentes. Commit: `feat: add commentator briefings and bounded overlay export`.

## Task 8: Despliegue Azure y persistencia comprobada

**Files:** crear `infra/main.bicep`, `infra/storage.bicep`, `infra/app.bicep`, `infra/roles.bicep`, `Dockerfile`, `.dockerignore`, `scripts/seed_cloud.py`, `scripts/smoke_cloud.py`, `tests/integration/test_cloud_contract.py`; actualizar `docs/readiness.md`.

**Interfaces:** configuración `STORAGE_BACKEND=azure_tables`, `AGENT_MODE=foundry`, `FOUNDRY_PROJECT_ENDPOINT`, `FOUNDRY_MODEL`, `AZURE_TABLE_ENDPOINT`, identidad y límites de llamadas. `smoke_cloud(base_url: str) -> SmokeReport` verifica salud, dos cutoffs y referencia de evidencia. El deployment usa un recurso Foundry existente y un nombre de deployment confirmado; Bicep no compra ni despliega modelos por su cuenta.

- [ ] Probar que un modo Foundry incompleto impide declarar readiness y que el contrato HTTP se conserva con almacén Azure. Ejecutar `python -m pytest tests/integration/test_cloud_contract.py -q` con adaptador controlado y comprobar fallo inicial.
- [ ] Preparar imagen multietapa: build Node y runtime Python, usuario no root, puerto 8000, un worker y una réplica ACA. Dar identidad a la aplicación y permisos de datos mínimos para Tables y el proyecto Foundry, confirmados contra los roles disponibles del recurso. No guardar claves ni incluir `.env`, tmp, manifiestos privados de evaluación o el PDF de competidores en la imagen.
- [ ] Presentar recursos y parámetros concretos al usuario antes de provisionar recursos de pago o publicar. Tras autorización aplicable, desplegar en una región con el modelo disponible, usar identidad administrada, sembrar datos sintéticos idempotentemente y confirmar que un reinicio conserva eventos. El smoke registra resultados, sin imprimir tokens.
- [ ] Ejecutar `python scripts/smoke_cloud.py --url <url-devuelta-por-el-despliegue>` y repetir tras reinicio. Verificar backend Foundry real, límites de llamadas y estado de ingesta. Commit: `deploy: host match context assistant on Azure`.

## Task 9: Evaluación, utilidad y material de entrega

**Files:** crear `scripts/evaluate.py`, `tests/integration/test_spoiler_matrix.py`, `web/e2e/dual-viewer.spec.ts`, `docs/evaluation.md`, `docs/demo-script.md`, `docs/submission.md`, `README.md`; guardar reportes generados bajo `tmp/evaluation/`.

**Interfaces:** `evaluate_cases(base_url: str, cases: tuple[EvaluationCase, ...]) -> EvaluationReport`; cada caso fija escenario, cutoffs, perfil y afirmaciones prohibidas o esperadas. Los reportes separan runner scripted, fallback factual y Foundry real.

- [ ] Añadir matriz con los cuatro escenarios, cortes antes/después de gol y corrección, dos idiomas, dos profundidades y ambos roles; añadir dos pestañas con reproducción distinta. Assert: cero referencias posteriores al cutoff en respuestas, evidencia y almacenamiento cliente; números resueltos; ausencia de falsa tendencia neutral; una corrección solo afecta los cortes adecuados. Ejecutar la matriz y confirmar fallos reales si falta cobertura antes de corregir.
- [ ] Ejecutar `python -m pytest tests/unit tests/integration -q`, `npm.cmd --prefix web test -- --run`, `npm.cmd --prefix web run build` y `npm.cmd --prefix web run test:e2e`. Con presupuesto y acceso habilitados, ejecutar casos seleccionados contra Foundry, medir latencia sin caché y con caché, llamadas, tokens y rechazos. Documentar condiciones y valores observados; si el objetivo de diez segundos no se cumple, optimizar o registrar el límite sin falsificar el modo utilizado.
- [ ] Hacer las sesiones de utilidad de la especificación: tres personas para aficionado y una revisión del briefing profesional, declarando la experiencia del revisor. Registrar si identifican los dos cambios principales y qué evidencia consultan. Si faltan participantes, dejar esa validación expresamente pendiente; no simular resultados.
- [ ] Preparar README reproducible, pitch y materiales en inglés, datos y licencias, instrucciones del jurado y demo de 110 segundos con margen hasta dos minutos. La creación del vídeo seguirá la habilidad de vídeo que corresponda cuando se ejecute. Publicar repositorio, vídeo y entrega únicamente con la autorización aplicable y adjuntar sus URLs reales. Mantener la app accesible durante evaluación y documentar cómo observar errores y consumo.
- [ ] Commit: `docs: publish verified evaluation and hackathon handoff`.

## Hitos y comprobación de cobertura

| Hito | Tareas | Resultado verificable |
| --- | --- | --- |
| Base de confianza | 0 a 3 | Cuatro escenarios, persistencia y evidencia temporal comprobada. |
| Primera experiencia | 4 a 6 | Aficionado con flujo completo y al menos un smoke Foundry real. |
| Segundo usuario | 7 | Briefing y overlay con los mismos hechos. |
| Entrega revisable | 8 y 9 | URL Azure, pruebas, sesiones de utilidad y materiales listos. |

La cobertura de las secciones 1 a 4 de la especificación está en tareas 5 a 7; datos en 1 y 2; límite temporal en 2 a 6 y 9; arquitectura y agentes en 3 a 5; fallos en 2, 4 y 5; aceptación en 6 a 9; demo en 9; preparación y prioridad en 0 y estos hitos.

## Revisión y método de ejecución

El 23 de octubre el participante autorizó implementar el generador y el motor de métricas y evidencia. Esta entrega ejecutó directamente las tareas 1 y 3, con el prerrequisito mínimo de empaquetado Python, en la carpeta actual y una rama nueva elegida por el participante. La revisión independiente y las comprobaciones se registran en `docs/engine-validation.md`. Las demás tareas permanecen pendientes; su estado no se infiere de la conexión Foundry ni de esta entrega local.

El participante autorizó después la tarea 2, en una rama nueva y con otra PR tras las pruebas. SQLite, el adaptador Azure Tables probado con transporte simulado y la ingesta reanudable están implementados; las comprobaciones y límites se registran en `docs/ingestion-validation.md`. La persistencia en Azure real sigue pendiente del despliegue.

El participante autorizó integrar la PR 2 y continuar con tarea 4. La integración quedó en master como 5b3eea9, con 158 pruebas verdes. Los agentes, herramientas, validación, fallback y adaptador Foundry están implementados en la rama siguiente. Tras renovar el acceso el 24 de octubre y optimizar el intercambio interno, el smoke real bilingüe pasa con los tres agentes y referencias validadas. La revisión completa previa a integrar detectó y corrigió una etiqueta ambigua de recuperaciones altas y la falta de reparación ante revisión mal formada. Las comprobaciones detalladas posteriores activaron respaldo factual al agotar el tiempo reparando texto rechazado. Los resultados, incluidos los fallos y los datos históricos, están en `docs/agents-validation.md`; no prueban latencia garantizada, estabilidad del modo profesional, veracidad semántica absoluta ni despliegue de la aplicación.

Después de integrar la PR 3 como 3053a13, el participante autorizó tarea 5 en una rama nueva y con PR. La API temporal, el servicio/caché, la configuración mínima de backend y los contratos OpenAPI/TypeScript están implementados y comprobados en local. La revisión independiente detectó y se corrigió la cancelación de generación al desconectar HTTP; 255 pruebas pasan, incluida conexión TCP real y petición de reemplazo. Comprobaciones y decisiones en `docs/api-validation.md`. No se ha implementado la web ni desplegado la aplicación, ni se ha repetido Foundry real durante esta entrega.

Tras integrar la PR 4 como bf9bbbcb, el participante autorizó la primera experiencia del aficionado y eligió Heyclicky. La tarea 6 y el andamiaje frontend necesario están implementados y probados: 23 pruebas de web, ocho recorridos reales HTTP/SQLite en escritorio/móvil, build/tipos/formato y 255 pruebas Python verdes. La revisión independiente detectó y corrigió la cancelación continua de cargas lentas durante reproducción y completó unidades/definiciones de evidencia; detalles y límites en `docs/web-validation.md`. La experiencia profesional, el despliegue y la evaluación con usuarios/modelo real siguen en tareas 7–9.
