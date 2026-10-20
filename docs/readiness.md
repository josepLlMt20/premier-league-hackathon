# Preparación de Foundry

Comprobación realizada el 20 de octubre de 2026. Este documento registra la conexión; no declara implementadas las tareas del plan de producto.

## Recurso y acceso

| Dato | Valor comprobado |
| --- | --- |
| Suscripción | `Azure subscription 1`, estado `Enabled` mediante Azure CLI. |
| Recurso Foundry | `rg-premier-hackathon`, tipo `AIServices`. |
| Grupo de recursos | `foundry`. El nombre del recurso empieza por `rg-`, pero ese no es su grupo. |
| Región del recurso | `spaincentral`. El despliegue Global Standard no limita la inferencia a esta región. |
| Endpoint del proyecto | `https://rg-premier-hackathon.services.ai.azure.com/api/projects/rg-premier-hackathon` |
| Implementación | `gpt-5-mini`; versión `2025-08-07` y tipo Estándar global según el portal compartido por el participante. |
| Identidad local | Inicio de sesión mediante código de dispositivo de Microsoft Azure CLI; SDK con `AzureCliCredential`. |
| Crédito y facturación | El participante comunica prueba gratuita de 200 USD; el portal compartido muestra 175,99 EUR disponibles y coste mensual redondeado a cero. No se ha consultado el desglose de facturación mediante API. |

El participante asignó `Foundry User` a su cuenta sobre el recurso y confirmó que desapareció el aviso del portal. No se necesitan claves de API para esta conexión local.

## Entorno de la prueba

- Azure CLI 2.91.0, distribución ZIP oficial, extraída en `tmp/foundry-connection/azure-cli/`; no se ha modificado el PATH global.
- Entorno Python aislado en `tmp/foundry-connection/venv/`, con proveedor `agent-framework-foundry==1.15.0` y `azure-identity==1.26.0`. `pip check`: sin dependencias incompatibles.
- Dependencias resueltas registradas en `tmp/foundry-connection/requirements-probe.txt`. Este entorno provisional no sustituye los lockfiles del producto.
- `.env` local contiene únicamente el endpoint y el nombre de implementación. `.env` y `tmp/` están excluidos de Git.
- Script provisional: `tmp/foundry-connection/smoke_foundry.py`; resultado: `tmp/foundry-connection/smoke-result.json`. Ambos son artefactos locales ignorados.

## Resultado real

La ejecución de `tmp/foundry-connection/venv/Scripts/python.exe tmp/foundry-connection/smoke_foundry.py` terminó con código 0 y `status=passed`.

La prueba usa Microsoft Agent Framework y el endpoint de proyecto de Foundry. Una herramienta local devuelve hechos sintéticos hasta secuencia 2; existe un gol en secuencia 3 que la herramienta no entrega al modelo. La respuesta tipada se valida con Pydantic y se compara con los hechos esperados: un tiro, cero goles y referencias `e1`, `e2`. Se exige exactamente una invocación de herramienta.

| Medida | Observación de esta ejecución |
| --- | --- |
| Duración del recorrido del agente | 7,587 segundos. |
| Invocaciones de herramienta local | 1. |
| Tokens de entrada comunicados por el SDK | 611. |
| Tokens de salida comunicados por el SDK | 68. |
| Tokens totales comunicados por el SDK | 679. |

Se limitaron las iteraciones a tres, las llamadas de herramienta a dos, la salida a 1024 tokens por llamada y el tiempo global a 45 segundos; los reintentos HTTP del cliente se desactivaron. Se usó `store=False` y no se activaron búsqueda web ni herramientas alojadas de pago. Esto no describe todas las políticas de retención del proveedor.

El caso verifica autenticación desde código, acceso al modelo, invocación de herramienta y respuesta estructurada en un ejemplo mínimo. No demuestra todavía el aislamiento temporal del producto completo, las tres funciones de agentes, la latencia representativa ni la utilidad con personas. El coste monetario exacto de la prueba no se ha contrastado con el desglose de Azure.

## Pendiente para el producto

- Implementar el plan de aplicación y sus comprobaciones de dominio, API y dos espectadores.
- Medir consumo y latencia con solicitudes representativas y revisar cargos por recurso.
- Preparar almacenamiento persistente y despliegue de la aplicación cuando corresponda.
- Mantener la suscripción de prueba; no se ha autorizado pasar a pago por uso.

Referencias: [instalación ZIP oficial de Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-windows?view=azure-cli-latest), [agentes desde código con Foundry](https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/responses-api).
