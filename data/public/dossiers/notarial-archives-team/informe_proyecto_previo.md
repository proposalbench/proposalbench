> Documento ficticio creado para ProposalBench.

# Informe Final de Resultados: Proyecto NOTAR-NET (2021-2024)

*Fecha de emisión del informe: Septiembre 2024. Estado de repositorios confirmado vigente en Septiembre 2026.*

**Título del proyecto:** NOTAR-NET: Redes de crédito y agencia femenina en la Corona de Aragón (1350-1450)
**Referencia:** PB-UPR-2021-NN01 (ayuda institucional ficticia para grupos emergentes)
**Entidad financiadora:** Universitat de Puig-rodon.
**Presupuesto concedido:** 115.000 EUR. Costes directos: 115.000 EUR (incluye contrato del IP por 3 años [85.000 EUR, como condición de la ayuda institucional], contrato postdoctoral de 12 meses a tiempo parcial [15.000 EUR], equipamiento y viajes [15.000 EUR]).
**Periodo de ejecución:** 1 de septiembre de 2021 a 31 de agosto de 2024.
**Investigador Principal:** Dr. Oriol Guinovart i Balcells (Universitat de Puig-rodon).

## 1. Resumen ejecutivo y objetivos

El proyecto NOTAR-NET tuvo como objetivo principal aplicar técnicas de Reconocimiento Automático de Texto Manuscrito (HTR) y Análisis de Redes Sociales (SNA) a los protocolos notariales de los siglos XIV y XV conservados en el Archivo Histórico Comarcal de la Vall de Boira. El propósito histórico fue cuantificar y analizar el mercado de crédito rural y urbano tras la Peste Negra, prestando especial atención a la agencia económica de las mujeres viudas frente a los mercaderes profesionales.

## 2. Metodología y desarrollo técnico

### 2.1. Corpus documental y digitalización
El trabajo se centró en la serie de *Manuales* y *Protocolos* de cinco notarios activos entre 1350 y 1450. Se llevó a cabo una campaña de digitalización in situ que resultó en la captura de **45.200** folios en alta resolución (TIFF, 400 dpi). 

**Nota lingüística fundamental:** El corpus íntegro está compuesto por textos en **catalán antiguo y latín**. No existe presencia de castellano ni de otras lenguas romances en esta colección documental.

### 2.2. Reconocimiento de Texto Manuscrito (HTR)
Para el procesamiento HTR, utilizamos una arquitectura basada en redes neuronales convolucionales y recurrentes (CRNN) implementada en el motor Kraken. 
- Se generó un *Ground Truth* mediante la transcripción manual paleográfica de **2.500** folios (aprox. 4,5 millones de caracteres). La división se realizó a nivel de escribano (identificando 12 manos distintas) para asegurar la evaluación sobre manos no vistas en el entrenamiento: 8 manos (2.000 folios) para entrenamiento, 2 manos (250 folios) para validación y 2 manos (250 folios) para test.
- El modelo final alcanzó en el conjunto de test una Tasa de Error de Caracteres (CER) del **4,2%** (IC 95%: 3,9% - 4,5%, calculado mediante *bootstrapping* sobre 150 folios de test, n=270.000 caracteres) para la escritura gótica cursiva de finales del siglo XIV.
- **Limitación técnica:** El rendimiento del modelo en el conjunto de test disminuyó al procesar las escrituras cursivas más degeneradas de mediados del siglo XV (1440-1450), donde el CER aumentó al **8,5%** (IC 95%: 7,8% - 9,2%, n=180.000 caracteres).

### 2.3. Extracción de información y evaluación
Se diseñó un pipeline de Procesamiento de Lenguaje Natural (NLP) para identificar fórmulas diplomáticas de deuda. Esto permitió aislar y estructurar **12.540** escrituras anotadas de carácter crediticio.
La extracción de entidades y resolución de identidades se evaluó sobre una muestra aleatoria adjudicada manualmente de **500** escrituras (conteniendo 1.250 menciones de personas y 620 relaciones de deuda). Utilizando coincidencia exacta y promediado macro, el modelo alcanzó un F1-score de **0,92 (IC 95%: 0,89-0,95)** para roles (acreedor/deudor) y **0,89 (IC 95%: 0,85-0,93)** para cantidades. La vinculación de entidades presentó 45 errores sobre 750 decisiones de desambiguación de homónimos (tasa de error del **6,0%**). Para evaluar el impacto de estos errores en la red, se diseñó una simulación de Montecarlo (1.000 iteraciones) empíricamente calibrada: los errores adjudicados manualmente se mapearon a sus registros y aristas afectadas para modelar las tasas reales de fusión (*node-merge*) y división (*node-split*) de identidades. Aplicando estas tasas perturbadas a la red completa, la estimación de la centralidad de intermediación media (*betweenness* normalizada, promediada sobre todos los nodos en la red agregada) fue de **0,028**, con un intervalo de incertidumbre por simulación condicional del 95% de **[0,026, 0,030]**.

## 3. Resultados históricos y cuantitativos

Cada instrumento crediticio (n=12.540) genera una o más aristas dirigidas (del acreedor al deudor). En caso de deudores solidarios, el valor monetario se dividió equitativamente entre las aristas para no duplicar el capital. Las relaciones repetidas se agregaron sumando sus pesos. La red económica reconstruida está compuesta por **3.450** individuos únicos (nodos) y **15.800** relaciones de deuda (aristas). 
El volumen total nominal de crédito analizado ascendió a **1.450.000** sueldos jaqueses. Todas las cantidades originales (expresadas principalmente en florines de Aragón, sueldos barceloneses y dineros jaqueses) fueron convertidas a una unidad analítica común (el sueldo jaqués de cuenta) utilizando las equivalencias de mercado documentadas en los manuales de mercaderes de Barcelona y Zaragoza (con anclajes en 1362, 1389 y 1412). Para los años fuera de estos anclajes, se aplicó interpolación lineal y extrapolación plana (1350-1361 y 1413-1450). Un análisis de sensibilidad utilizando tasas alternativas extraídas de registros notariales de cambio arrojó una desviación máxima del **±5%** en el volumen total de crédito respecto a la serie principal. La red se dividió en **10** ventanas temporales no superpuestas de 10 años (de 1350-1359 a 1440-1449; el material datado en 1450 fue excluido del análisis de red) para evitar conectar individuos no contemporáneos.

### 3.1. La agencia económica de las viudas
El análisis de un subconjunto de **6.200** escrituras (comparaciones restringidas al periodo 1360-1400) reveló una participación asimétrica de las mujeres viudas:
- Las viudas que actuaron como acreedoras (n=315) constituyeron el **22,0%** de los 1.432 acreedores únicos en la red de ese periodo.
- Las viudas que actuaron como deudoras (n=228) representaron el **8,0%** de los 2.850 deudores únicos. (Nota: 45 viudas ocuparon ambos roles en distintos momentos).
- El tamaño medio del préstamo otorgado por viudas (n=1.850 préstamos) fue de **45** sueldos jaqueses (DE = 12), sugiriendo la hipótesis de una preferencia por el microcrédito de consumo, posiblemente derivado de la restitución de dotes, que deberá ser investigada en futuros proyectos mediante el cruce con los capítulos matrimoniales (contratos de dote) conservados en la misma serie notarial. Sin embargo, los capítulos matrimoniales por sí solos no demuestran el pago efectivo de la restitución ni la fecha exacta de viudedad (dado que los registros parroquiales sistemáticos no existen para esta época). Hasta la fecha no se han localizado recibos de restitución o cartas de pago equivalentes, por lo que su búsqueda constituirá una fase de viabilidad planificada, con una estrategia alternativa basada en asociaciones temporales.

### 3.2. El papel de los mercaderes
Los mercaderes profesionales (n=85 individuos) mostraron un patrón topológico distinto:
- Mostraron una centralidad de intermediación (*betweenness* normalizada, promediada a través de las 10 ventanas) de 0,045 (DE = 0,012), un **40,6%** superior a la media del grupo comparador de artesanos urbanos (n=145 individuos; media 0,032, DE = 0,008), conectando el crédito rural con los circuitos comerciales urbanos.
- El tamaño medio del préstamo otorgado por mercaderes (n=3.420 préstamos) fue de **120** sueldos jaqueses (DE = 45).

## 4. Gestión de datos y ciencia abierta

- Las imágenes digitales (45.200 folios) están depositadas en el repositorio institucional de la Universitat de Puig-rodon bajo acceso restringido para investigación no comercial (requiere registro), conforme al convenio con el archivo.
- Las transcripciones XML-ALTO, el modelo HTR y el conjunto de datos tabulares de la red de crédito han sido publicados en Zenodo bajo licencia CC BY-NC 4.0.
