# Asistente de contexto de partido para aficionados y comentaristas

Fecha: 19 de octubre de 2026.
Estado: diseño aprobado por el participante en la conversación. El nombre comercial se elegirá después.

## 1. Propósito y decisiones acordadas

Ayudar a un aficionado que llega tarde o se pierde un tramo a recuperar el contexto del partido: qué ha cambiado, por qué merece atención y qué observar a continuación. Un modo profesional prepara esa misma información para un comentarista, con historias priorizadas, cifras e intervalos comprobables.

El aficionado es el usuario principal. El comentarista es un segundo usuario del mismo motor y de la misma evidencia. La participación es individual y se prioriza una experiencia útil y completa. La disponibilidad de tiempo no amplía automáticamente el alcance.

La propuesta combina recapitulación contextual, evidencia inspeccionable y respeto al punto de reproducción. No se afirmará que el concepto es exclusivo del concurso: las fichas revisadas incluyen propuestas cercanas.

## 2. Experiencia del aficionado

1. Abre un encuentro ficticio y ve su reproducción en un campo 2D, el marcador y una cronología.
2. Selecciona desde qué punto se ausentó y hasta qué punto quiere ponerse al día. El valor por defecto del segundo punto es su posición actual de reproducción.
3. Escoge idioma, español o inglés, y profundidad, sencilla o detallada. Puede indicar un equipo favorito ficticio.
4. Recibe una síntesis breve y hasta tres momentos que explican los cambios del intervalo.
5. Abre un momento para inspeccionar la secuencia de eventos, las métricas utilizadas y la explicación de sus límites.
6. Regresa a la reproducción sin perder su posición. Al terminar el encuentro puede solicitar una recapitulación completa.

La profundidad modifica la selección de contenido, las métricas visibles y la explicación. El equipo favorito cambia la relevancia editorial; no modifica los hechos ni el marcador. Las preferencias se conservan localmente, sin cuenta de usuario.

La reproducción y su velocidad se controlan desde la aplicación. Es un encuentro sintético con visualización propia, sin integración con reproductores comerciales. La vista 2D representa los eventos disponibles; no inventa el seguimiento continuo de los 22 jugadores.

## 3. Experiencia del comentarista

El modo profesional usa el mismo partido y permite seleccionar un intervalo. Su punto de referencia por defecto es el último evento recibido del encuentro simulado; puede retroceder para preparar una intervención sobre un momento anterior.

Entrega hasta tres tarjetas editoriales. Cada una incluye una propuesta de titular, qué ha cambiado, una frase sugerida, cifras con sus intervalos, eventos de respaldo y la distinción entre observación e interpretación. Si una explicación es tentativa, debe expresarlo junto a la afirmación correspondiente.

Una tarjeta puede abrir la misma vista de evidencia del aficionado y mostrarse en un panel de overlay con texto breve y tiempo de referencia. Se permite copiar el texto y exportar su contenido estructurado para una futura integración. La primera entrega no integra herramientas de realización ni emite gráficos a una retransmisión externa.

## 4. Alcance de la primera entrega

| Incluido | Límite |
| --- | --- |
| Encuentro y datos | Un encuentro principal de 90 minutos, más tres variantes reproducibles para evaluación. Equipos, jugadores y eventos ficticios. |
| Ingesta | Reproducción de eventos como flujo, con pausa, reinicio y velocidad configurable. |
| Análisis | Recuperaciones altas, evolución de ocasiones y cambios de control territorial basados en eventos. |
| Explicaciones | Síntesis del intervalo, momentos con evidencia y recapitulación final. |
| Personalización | Dos profundidades, español e inglés, equipo favorito opcional y dos roles de audiencia. |
| Presentación | Campo 2D, cronología, evidencia y tarjetas editoriales con vista de overlay. |
| Agentes | Analista, redactor y revisor con herramientas y estado compartido explícitos. |
| Operación | Aplicación desplegada en Azure, ejecución local reproducible y registro básico de errores, latencia y consumo del modelo. |

Quedan fuera del primer alcance la visión artificial sobre vídeo, un feed de fútbol real, predicciones de apuestas, reconocimiento de voz, cuentas, pagos, seguimiento de múltiples partidos y conexiones con equipos de emisión. Un chat abierto y la generación de vídeo tampoco forman parte del MVP.

## 5. Datos sintéticos y contrato de evento

Un generador con semilla produce eventos coherentes con posesiones, cambios de equipo, coordenadas válidas, periodos y marcador. El encuentro principal contiene un inicio equilibrado, un tramo de recuperaciones altas y un cambio posterior. Las variantes incluyen dominio territorial con pocas ocasiones, una evolución sin cambio destacado y una corrección de evento.

Cada evento tiene `event_id`, `match_id`, `sequence`, periodo, reloj mostrado, tipo, equipo, jugador cuando corresponda, coordenadas cuando existan y atributos específicos. Los tipos iniciales son pase, recuperación, pérdida, presión, tiro, gol, sustitución y corrección. `sequence` es el orden monotónico de disponibilidad; el reloj del partido es un dato de presentación y análisis.

Las correcciones se añaden como eventos nuevos con referencia al evento corregido. Se conserva el historial original para reconstruir lo que se sabía en cada punto. Las reglas del generador validan el marcador, los identificadores, los rangos espaciales y las relaciones entre eventos.

La calidad de ocasión será una medida heurística del simulador con definición visible. No se presentará como una probabilidad de gol calibrada sobre fútbol real. Los manifiestos de escenarios sirven para evaluar el sistema y no se entregan a los agentes como explicación del partido.

## 6. Límite temporal y protección de spoilers

Una solicitud define `from_sequence` exclusivo y `to_sequence` inclusivo. Para un resumen, el segundo valor también es el límite de conocimiento. El servidor valida que ambos pertenecen al mismo partido y que no superan los eventos recibidos.

Toda consulta de métricas, marcador, cronología, evidencia, prompts y caché utiliza ese límite. Los datos de referencia pueden incluir eventos anteriores al intervalo para comparar tendencias, pero nunca eventos posteriores a `to_sequence`. El cliente recibe únicamente los datos autorizados para su punto de reproducción; no precarga el partido completo.

El analista, el redactor y el revisor trabajan con la misma instantánea. Cada solicitud inicia un contexto acotado a esa instantánea; no reutiliza conversaciones ni memorias de otro espectador o de un punto posterior. Sus herramientas solo pueden consultar el partido dentro del límite autorizado. El caché incorpora partido, intervalo, límite temporal, rol, idioma y preferencias. Una corrección solo se aplica en instantáneas posteriores a su llegada. Las respuestas se identifican con su intervalo: una respuesta antigua no reemplaza el estado correspondiente a un nuevo punto de reproducción.

Dos espectadores del mismo encuentro pueden ver marcadores y narrativas distintos porque están en puntos distintos. Esto debe comprobarse también en peticiones, almacenamiento del cliente y respuestas del servidor, no solo en el texto visible.

## 7. Arquitectura y colaboración entre agentes

La arquitectura se divide en seis componentes con responsabilidades separadas:

1. **Generador y reproductor:** produce el flujo sintético y controla la ingesta.
2. **Almacén de eventos e instantáneas:** reconstruye el estado disponible en un punto concreto.
3. **Motor de métricas y patrones:** calcula estadísticas y detecta patrones mediante reglas comprobables.
4. **Orquestador de agentes:** selecciona historias, redacta y revisa con herramientas limitadas a la instantánea.
5. **API de contexto:** valida intervalos y entrega eventos, síntesis, evidencia y tarjetas.
6. **Aplicación web:** ofrece las dos experiencias y visualiza el contexto recibido.

Los cálculos numéricos y el control temporal pertenecen al código. Los agentes usan herramientas para consultar hechos, comparar patrones y adaptar historias; no inventan métricas ni pueden ampliar su límite de conocimiento.

| Agente | Responsabilidad | Entrega al siguiente paso |
| --- | --- | --- |
| Analista | Investigar patrones con las herramientas de métricas y evidencia, seleccionar hasta tres historias y explicar su relevancia. | Historias candidatas con referencias, intervalos y limitaciones. |
| Redactor | Preparar la síntesis y las tarjetas según rol, profundidad e idioma. | Afirmaciones estructuradas ligadas a las historias aprobables. |
| Revisor | Contrastar redacción, evidencia, intervalos y fuerza de las interpretaciones; pedir corrección o rechazar. | Contenido aceptado o motivos concretos de rechazo. |

La revisión combina controles deterministas de referencias, números y tiempos con revisión del lenguaje por el agente. Una segunda opinión del modelo no constituye por sí sola una prueba de veracidad. Cada afirmación factual necesita referencias resolubles; las interpretaciones deben conservar sus límites.

El contrato de salida incluye el intervalo, el límite de conocimiento, el perfil, una síntesis y tarjetas con `claim_id`, clase de afirmación, referencias de métricas y eventos. La implementación concretará el esquema y las herramientas en el plan técnico.

Se propone Microsoft Foundry para los modelos, Microsoft Agent Framework para la orquestación y Azure Container Apps para alojar la aplicación. El almacén inicial debe ser persistente y compartible, sin depender del disco efímero de un contenedor. La selección del servicio de almacenamiento, modelo, versiones y autenticación se resolverá en el plan técnico tras comprobar los recursos de Azure disponibles. El diseño evita depender de capacidades de un proveedor todavía no verificadas.

Los agentes se ejecutan cuando el usuario solicita contexto o cuando se necesita actualizar una tarjeta relevante. Los eventos ordinarios actualizan métricas sin disparar una llamada al modelo por evento.

## 8. Fallos y comportamiento degradado

- Un evento inválido se rechaza y registra; un duplicado no altera dos veces las métricas.
- Si faltan datos o no hay un cambio suficientemente respaldado, el resultado lo indica y no fabrica una historia destacada.
- Una salida inválida o rechazada admite un único intento de reparación con motivos explícitos. Después se descarta esa historia.
- Si el modelo falla, la reproducción y las estadísticas siguen disponibles. Se puede mostrar un resumen factual mediante plantillas, identificado como tal; no se presentará como una ejecución exitosa de los agentes.
- Si cambia el punto de reproducción durante una generación, la respuesta conserva su intervalo y no sobrescribe la vista actual.
- Si la ingesta se detiene, la interfaz muestra el último evento disponible y el estado del flujo.

El producto mantiene el texto neutral respecto a los datos: una coincidencia temporal con una sustitución no se convierte en una causa demostrada.

## 9. Criterios de aceptación

| Área | Comprobación necesaria |
| --- | --- |
| Recorrido principal | Generar el encuentro, ingerirlo, seleccionar un intervalo, recibir contexto y abrir la evidencia sin pasos manuales en el backend. |
| Protección temporal | Cero referencias posteriores al límite en una batería de escenarios con dos espectadores, goles futuros y correcciones tardías; inspeccionar también respuestas y caché. |
| Exactitud | Todas las referencias factuales resuelven y las cifras coinciden con las funciones de métricas y sus intervalos. Ninguna historia rechazada llega a una tarjeta publicada. |
| Patrones | Los escenarios positivos muestran el patrón introducido; el escenario neutral permite responder que no hay un cambio claro. |
| Personalización | Ambos idiomas mantienen hechos equivalentes. Rol y profundidad cambian selección y presentación sin modificar resultados. |
| Colaboración | Una traza muestra consulta de herramientas, selección, redacción, revisión y recuperación o rechazo ante un fallo inducido. |
| Operación | Despliegue accesible para el jurado y reinicio reproducible. Medir latencia de las solicitudes y llamadas al modelo; el objetivo inicial de contexto es menos de diez segundos en las condiciones declaradas de la demo. |
| Uso | Probar con tres personas que puedan identificar los dos cambios principales tras consultar la experiencia. Para el modo profesional, validar al menos con una persona que prepare un breve comentario usando las tarjetas y sus evidencias. Si no tiene experiencia de retransmisión, registrar esa limitación. |

Las pruebas sintéticas demuestran propiedades dentro del simulador. La utilidad en fútbol real y la ausencia de errores fuera de los casos evaluados no se darán por demostradas.

## 10. Demo y entrega de la hackathon

La demo objetivo dura 110 segundos:

| Tiempo | Contenido |
| --- | --- |
| 0 a 15 s | Situación del aficionado y encuentro sintético en marcha. |
| 15 a 45 s | Recuperar el intervalo perdido y abrir una evidencia. |
| 45 a 65 s | Mostrar dos puntos de reproducción y el respeto al límite temporal. |
| 65 a 90 s | Preparar el briefing del comentarista desde la misma evidencia. |
| 90 a 110 s | Mostrar la colaboración de agentes, el manejo de un rechazo y el valor del producto. |

La entrega incluirá pitch en inglés, repositorio GitHub público, instrucciones de ejecución, demo accesible y vídeo público de menos de dos minutos. Se documentarán las tecnologías Microsoft utilizadas, las reglas del simulador y las limitaciones. El plazo oficial es el 27 de octubre de 2026 a las 23:59 del Pacífico, equivalente al 28 de octubre a las 07:59 en Madrid. El acceso para evaluación debe mantenerse hasta finalizar el periodo de evaluación.

Fuente: [bases oficiales, apartados 1, 4 y 6](https://github.com/microsoft/insidethegamehackathon/blob/main/OFFICIAL%20RULES.md). El alcance funcional también se apoya en el brief completo de Challenge compartido por el participante.

## 11. Orden de prioridad y decisiones pendientes del plan técnico

Primero se construirá el recorrido completo del aficionado con límites temporales y evidencia. Después, el modo comentarista reutilizando ese recorrido. La presentación de overlay, la observabilidad y el ensayo de la demo completan la entrega; las ampliaciones se reconsideran únicamente cuando el recorrido principal supera sus comprobaciones.

Para preparar el plan técnico se comprobarán la suscripción de Azure, el acceso a Foundry y sus modelos, los permisos de despliegue y las versiones vigentes de las herramientas. Si alguno no está disponible, se concretará una alternativa compatible antes de prometer una integración. Estos son requisitos de preparación, no funciones adicionales del producto.

La aprobación de esta especificación permite preparar un plan de implementación. La construcción del producto comienza después de revisar ese plan y acordar su ejecución.
