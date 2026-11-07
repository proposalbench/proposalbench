# Aprendizaje automático en el modelado de la propagación de ondas: De los métodos numéricos estándar a las redes neuronales informadas por la física en sismología

## Resumen

La propagación de ondas desempeña un papel fundamental en campos como la acústica, el electromagnetismo, la medicina y la geofísica. Los métodos numéricos estándar, como el método de diferencias finitas, el método de los elementos finitos y el método de los elementos de frontera, han sido ampliamente utilizados para simular fenómenos de propagación de ondas. Sin embargo, a menudo implican altos costos computacionales, especialmente en dominios no acotados y en problemas inversos, lo que motiva la exploración de técnicas alternativas de solución.

La investigación basada en el uso de aprendizaje automático ha crecido considerablemente en los últimos años. Por ejemplo, las redes neuronales informadas por la física (Physics Informed Neural Networks, PINNs) han surgido como una alternativa al combinar el aprendizaje automático con restricciones físicas para resolver ecuaciones en derivadas parciales. Estos métodos han demostrado tener potencial para equilibrar la eficiencia computacional y la precisión de la solución, especialmente en problemas inversos. Este trabajo se centra en investigar el alcance de estos abordajes como una alternativa o complemento a los métodos numéricos estándar.

Si bien estos métodos pueden aplicarse a una amplia gama de problemas, el enfoque de esta investigación es la propagación de ondas, particularmente en problemas con aplicaciones en sismología.

Como avance preliminar, se compararon las PINNs con el método de elementos de frontera para resolver el problema de la dispersión de ondas generada por un obstáculo cilíndrico, evaluando tiempos de cómputo y precisión bajo distintas configuraciones.

En etapas posteriores, se analizará el desempeño de las PINNs en un problema inverso de sismología, particularmente en la inversión de forma de onda completa (Full Waveform Inversion, FWI), con el objetivo de determinar si este enfoque puede reducir la alta carga computacional característica de dicho método. También, se buscará implementar técnicas que permitan escalar las PINNs u otros métodos basados en aprendizaje automático hacia problemas en sismología en contextos no controlados.

## 1. Planteamiento del problema

La propagación de ondas es un fenómeno físico descrito por ecuaciones en derivadas parciales (Partial Differential Equations, PDEs), ampliamente utilizadas en diversas ciencias aplicadas e ingenierías, debido a su aplicabilidad en campos como la medicina y la sismología. Sin embargo, las soluciones analíticas no siempre están disponibles en muchas situaciones prácticas, por lo que generalmente se requieren métodos numéricos para aproximarlas. En consecuencia, dichos métodos se han aplicado de manera reiterada para resolver ecuaciones en derivadas parciales (Seriani and Oliveira, 2020).

En el estudio de la propagación de ondas, existen numerosos métodos que abordan los desafíos asociados con este fenómeno. Entre los métodos estándar se incluyen las diferencias finitas, los elementos finitos y el método de los elementos de frontera (Igel, 2017; Virieux et al., 2011). En estos enfoques, el dominio espacial se discretiza para resolver la ecuación diferencial. En la Figura 1 se muestra la solución aproximada fˆ(x, y) obtenida mediante el método de diferencias finitas para la ecuación de Helmholtz:

$$
\begin{cases}\nabla^2 f + (5\pi)^2 f = 0, &\text{en }\Omega,\\ f = 0, &\text{en }\partial\Omega.\end{cases}\tag{1}
$$

La solución analítica correspondiente está dada por

$$
f(x,y)=\sin(5\pi x)\sin(5\pi y).
$$

En la Figura 1, mostramos cómo el refinamiento de la malla mejora la aproximación numérica, reduce el error relativo con respecto a la solución analítica y, al mismo tiempo, incrementa el tiempo de cómputo. En el modelado matemático, el objetivo principal es garantizar que los métodos de solución sean computacionalmente eficientes y presenten un error lo suficientemente bajo como para capturar los detalles físicos inherentes al sistema que son requeridos por el problema a resolver. Sin embargo, los métodos numéricos estándar a menudo enfrentan dificultades computacionales al abordar problemas complejos, especialmente en dominios no acotados y en problemas inversos. Por lo tanto, la demanda computacional asociada con muchos modelos comunes ha impulsado el desarrollo de estrategias innovadoras.

En este contexto, se ha sugerido que las implementaciones basadas en aprendizaje automático pueden hacer que sus aplicaciones sean más eficientes, como es el caso del modelado de la propagación de ondas, una tarea que comúnmente se ha abordado mediante métodos numéricos estándar. El marco de estudio de este trabajo se ilustra en la Figura 2, donde proponemos abordar la intersección entre el aprendizaje automático y el modelado de la propagación de ondas, específicamente en aplicaciones en sismología. De acuerdo con esto, planteamos el problema de investigación, junto con las preguntas que orientan el desarrollo del estudio.

A diferencia del aprendizaje automático, cuyo auge ha sido más reciente, el desarrollo de los métodos numéricos cuenta con una trayectoria consolidada de varias décadas, estrechamente ligada al avance del poder de cómputo y a la automatización de tareas complejas, así como a un soporte matemático que ofrece teoremas en diversos contextos (Rüde et al., 2018; Burden et al., 2016). Estos métodos han alcanzado un alto grado de madurez, con aplicaciones exitosas en numerosos campos de la ciencia y la ingeniería. Sin embargo, la rápida evolución del aprendizaje automático abre nuevas posibilidades para abordar problemas que de forma extensiva se han resuelto mediante enfoques numéricos estándar.

A partir de lo anterior, se plantea la siguiente pregunta de investigación: ¿De qué manera el aprendizaje automático puede constituir una alternativa o un complemento para las aplicaciones relacionadas con la propagación de ondas sísmicas?

Inicialmente, para responder esta pregunta, nos surge la necesidad de identificar qué métodos basados en aprendizaje automático se han aplicado y cuáles de ellos han demostrado ser una alternativa o complemento eficaz a los métodos numéricos estándar. Estos avances son particularmente relevantes en áreas como la sismología, donde la simulación de la propagación de ondas puede implicar altos costos computacionales.

Particularmente, los algoritmos basados en redes neuronales presentan la capacidad de aproximar funciones al mapear características de entrada hacia objetivos de salida de manera guiada por los datos. Una versión del teorema de aproximación universal, como se establece en Hornik et al. (1989), afirma que una red neuronal de propagación hacia adelante (feedforward neural network, FFNN) con una sola capa oculta y cierto número finito de neuronas puede aproximar de manera arbitraria cualquier función continua definida en un subconjunto compacto del espacio de entradas, siempre que la función de activación utilizada sea no constante, acotada y continua. Para ejemplificar este concepto, consideremos la siguiente función:

$$
f(x)=x^3+x^2-x-1.
$$

Para aproximar esta función dividimos el dominio en N segmentos de igual longitud. En cada segmento se define una contribución basada en la función de activación ReLU (Rectified Linear Unit), de modo que el tramo se representa como

$$
g_i(x)=w_i\operatorname{ReLU}(x-x_i^*)+y_i^{\mathrm{offset}},
$$

donde xᵢ* es el inicio del tramo, wᵢ es el peso que determina la pendiente y yᵢᵒᶠᶠˢᵉᵗ es un desplazamiento vertical que garantiza continuidad con los tramos anteriores. La función ReLU asegura que la contribución de cada tramo inicie en su región correspondiente y se define como

$$
\operatorname{ReLU}(x-x_i^*)=\operatorname{máx}(0,x-x_i^*),
$$

generando una función lineal a trozos en cada segmento. La Figura 3 ilustra este proceso, mostrando cómo cada tramo activado por ReLU contribuye a la reconstrucción de la función objetivo. Al finalizar todos los segmentos se obtiene la aproximación completa

$$
f(x)\approx\hat f_i(x)=\sum_{i=1}^N g_i(x).
$$

Cada tramo agrega una línea recta activada por ReLU que contribuye localmente a la forma de la función. La combinación de todos los tramos produce una aproximación por partes que captura la estructura de f (x).

Al aumentar el número de segmentos, la aproximación gana precisión y es capaz de representar funciones más complejas. A esta capacidad de representación se le conoce como la expresividad de la red. Con este procedimiento ejemplificamos la capacidad de aproximación de funciones mediante redes neuronales. Sin embargo, también debemos considerar que no hay garantía de que el algoritmo de entrenamiento pueda aprender la función deseada. El optimizador podría no encontrar los valores de los parámetros adecuados o elegir una función incorrecta debido a un sobreajuste. Por lo tanto, como señala Goodfellow et al. (2016), aunque una FFNN de una sola capa es capaz de aproximar cualquier función, dicha capa podría requerir un número de neuronas inviable y aun así no garantizar un aprendizaje y generalización adecuados.

De este modo, el aprendizaje automático se ha convertido en una herramienta numérica útil para modelar sistemas gobernados por leyes físicas y descritos por ecuaciones en derivadas parciales (Cuomo et al., 2022), donde la función a aproximar corresponde a la variable de interés. Los métodos basados en aprendizaje automático ofrecen ventajas significativas en términos de velocidad de evaluación y adaptabilidad, ya que pueden ajustarse a diferentes configuraciones del medio, condiciones de frontera o tipos de datos sin necesidad de reformular completamente el modelo físico. Además, son eficientes en contextos donde los modelos basados en ecuaciones son costosos o difíciles de construir, lo que los posiciona como una herramienta de alto potencial. No obstante, presentan limitaciones importantes, como su reducida interpretabilidad física (Zhang et al., 2020).

Una técnica que busca preservar las ventajas del aprendizaje automático mientras incorpora conocimiento físico explícito es el uso de redes neuronales informadas por la física (Physics Informed Neural Networks, PINNs) (Raissi et al., 2019). Esta ha sido utilizado en diversos problemas descritos por ecuaciones diferenciales, pero aún existen desafíos al comparar su desempeño con métodos estándar debido a diferencias en su formulación y enfoque computacional.

Las PINNs también ofrecen la posibilidad de abordar problemas inversos (Raissi et al., 2020; Haghighat et al., 2021; Hao et al., 2023), en los que se busca inferir los parámetros físicos del modelo a partir de observaciones experimentales. Este enfoque resulta especialmente valioso en sismología, donde la caracterización del subsuelo requiere métodos capaces de aprovechar información observacional y modelos físicos de propagación de ondas. Así, las PINNs surgen como una alternativa para estimar los parámetros de manera eficiente.

El uso de datos de observaciones experimentales introduce desafíos adicionales, como el ruido en las mediciones y el incremento en la dimensionalidad del problema. Frente a ello, se propone investigar métodos que integren modelos de aprendizaje automático en problemas sismológicos no controlados, entendidos como aquellos que trascienden los casos simplificados empleados para la evaluación de los métodos. El objetivo es abordar escenarios de mayor realismo y complejidad.

A partir de este escenario general, se plantean las siguientes preguntas específicas que guían la investigación:

1. ¿Qué técnicas de aprendizaje automático se han aplicado para modelar la propagación de ondas en el contexto de la sismología?

2. ¿Cómo pueden compararse los enfoques modernos basados en aprendizaje automático para resolver PDEs con los métodos numéricos estándar?

3. ¿En qué medida las PINNs pueden estimar de forma eficiente los parámetros físicos del modelo a partir de observaciones sísmicas, manteniendo una precisión comparable a la de los métodos de inversión estándar?

4. ¿De qué manera pueden los enfoques basados en aprendizaje automático escalarse para aprovechar datos provenientes de problemas sismológicos en contextos no controlados?

Estas preguntas configuran nuestro problema de investigación, centrado en evaluar el papel de las técnicas de aprendizaje automático en la modelación de la propagación de ondas sísmicas, así como su viabilidad como herramientas complementarias o alternativas a los métodos numéricos estándar.

## 2. Justificación

En esta sección presentamos la justificación del proyecto de tesis, abordando su novedad, viabilidad y aportes potenciales al estado actual del conocimiento. Inicialmente, la relevancia de esta investigación se sustenta en el creciente interés por integrar técnicas de aprendizaje automático en áreas tradicionalmente dominadas por métodos numéricos estándar, como la sismología.

La figura 4 muestra el número relativo de publicaciones, con respecto al número total de publicaciones indexadas, que relacionan métodos basados en aprendizaje automático y métodos numéricos estándar con el modelado de ecuaciones en derivadas parciales, incluyendo específicamente el modelado de la propagación de ondas de 2010 a 2024. Entre estos trabajos, las PINNs se encuentran entre los métodos que han recibido mayor atención en los últimos años, siendo citadas en más de 10,000 publicaciones (Raissi et al., 2019).

Estos datos reflejan un creciente interés científico en los métodos basados en aprendizaje automático, así como en la combinación de métodos numéricos estándar y aprendizaje automático, con una tasa de publicaciones que aumenta notablemente a partir de 2016. La investigación en aprendizaje automático fue impulsada por avances en hardware como las unidades de procesamiento gráfico (Graphics Processing Unit, GPU), un incremento significativo en la disponibilidad de datos, así como el desarrollo de herramientas computacionales de acceso abierto para la implementación de estos métodos (Abadi et al., 2016; Paszke et al., 2019; Bradbury et al., 2018). La misma figura también ilustra el interés en tres de los frameworks de Python más populares desde 2015: TensorFlor, PyTorch y JAX.

Se han realizado revisiones relevantes sobre el uso de aprendizaje automático en diversas áreas de la ingeniería y la ciencia (e.g. Vadyala et al., 2022; Deng et al., 2023; Lino et al., 2023), incluyendo su aplicación en problemas de inversión sísmica (JingBo et al., 2023). Sin embargo, dada la rápida expansión del campo, persiste la incertidumbre respecto a qué técnicas se han aplicado realmente con éxito, cuáles han demostrado ventajas significativas frente a los métodos estándar y en qué contextos (McGreivy and Hakim, 2024; Grossmann et al., 2024). En principio, los abordajes con aprendizaje automático tienen el potencial de aprender modelos sustitutos, es decir, representaciones aproximadas de un modelo que permiten estimar sus resultados sin resolver directamente las ecuaciones originales. que aproximen soluciones de PDEs reduciendo considerablemente el tiempo de evaluación, una ventaja crucial en contextos de alta demanda computacional como la sismología computacional. No obstante, esta ventaja no siempre se reporta ni se verifica sistemáticamente en la literatura. Explorar en profundidad estas técnicas permite construir un panorama actualizado del estado del arte, identificar sus principales aplicaciones y reconocer los desafíos que aún persisten.

Por otro lado, aunque se han propuesto métodos como las PINNs para diversas aplicaciones, su evaluación comparativa frente a los métodos numéricos estándar sigue siendo limitada. Se emplean líneas base inadecuadas y carece de métricas de comparación justas, lo que impide valorar objetivamente las fortalezas y limitaciones de cada enfoque. Una revisión sistemática en mecánica de fluidos reporta que el 79 % de los solucionadores basados en aprendizaje automático que afirman superar a los métodos estándar no utilizan líneas base adecuadas (McGreivy and Hakim, 2024). Además, aspectos como la capacidad de generalización fuera del dominio de entrenamiento y el tratamiento de condiciones físicas específicas pueden no estar correctamente representados por las PINNs sin modificaciones adicionales al enfoque originalmente propuesto (Bonfanti et al., 2024). En este contexto, resulta fundamental establecer criterios comparativos que permitan evaluar el rendimiento de estos enfoques modernos bajo condiciones controladas. A través de este tipo de análisis, es posible identificar en qué escenarios los nuevos métodos presentan ventajas, dónde pueden integrarse de forma complementaria con los enfoques estándar y qué limitaciones deben abordarse para mejorar su aplicabilidad.

Las PINNs implican un proceso de optimización de coeficientes en el que no sólo se ajustan los parámetros de la red, sino que también pueden estimarse los parámetros de las ecuaciones diferenciales que rigen el fenómeno en estudio. Esto las convierte en un enfoque particularmente adecuado para el tratamiento de problemas inversos, en los cuales se busca determinar las causas a partir de un conjunto de observaciones. Dado que en este tipo de problemas se conocen los efectos y se intenta inferir las causas subyacentes, se les denomina problemas inversos.

En el contexto de la propagación de ondas, se han desarrollado diversas técnicas para abordar este tipo de problemas, siendo una de las más destacadas la estimación de las propiedades del subsuelo a partir de registros de ondas sísmicas. Por ejemplo, la inversión de forma de onda completa (Full Waveform Inversion, FWI). Esta técnica permite estimar propiedades del medio a partir de registros sísmicos y se considera de alta resolución en geofísica porque aprovecha toda la información contenida en la forma de onda registrada, y no únicamente los tiempos de llegada, como ocurre en métodos más convencionales. Sin embargo, la FWI requiere recursos computacionales significativos, ya que implica minimizar de forma iterativa la diferencia entre los datos observados y las simulaciones numéricas de la propagación de ondas. Actualmente, existen implementaciones de esta técnica con alta precisión pero con costos computacionales elevados (Louboutin et al., 2019; Vikas et al., 2024). De acuerdo con esto, surge la hipótesis de que las PINNs podrían constituir una alternativa para reducir la carga computacional manteniendo una buena capacidad de resolución.

A pesar del creciente interés en las técnicas de aprendizaje automático y de sus de aplicaciones en sismología, muchas de estas metodologías aún se encuentran en etapas exploratorias. Con frecuencia, su validación se realiza en entornos controlados, utilizando versiones simplificadas del problema. Sin embargo, al intentar escalar estos enfoques, surgen nuevos desafíos relacionados con su aplicación a escenarios que involucran registros obtenidos en contextos no controlados. Uno de estos desafíos es el sesgo espectral en las redes neuronales, que se refiere a la tendencia de estos modelos a aprender primero las componentes de baja frecuencia de una función antes que las de alta frecuencia (Rahaman et al., 2019). Este aspecto resulta especialmente relevante en sismología, por ejemplo en FWI, donde la resolución espacial está limitada por la longitud de onda de las señales que se propagan en el medio.

De acuerdo con lo anterior, la presente investigación se justifica por su valor científico y metodológico al proponer una identificación de los enfoques actuales, destacando sus capacidades, limitaciones y oportunidades de mejora. Buscamos establecer criterios claros que permitan comparar objetivamente los métodos modernos con los enfoques numéricos consolidados, contribuyendo así al desarrollo de marcos de evaluación. Asimismo, abordar las limitaciones observadas en estudios previos para favorecer la aplicabilidad de estos métodos en entornos no controlados.

## 3. Objetivos de investigación

En esta sección mostramos el objetivo general y los objetivos específicos de esta investigación:

### 3.1. Objetivo general

Desarrollar enfoques de aprendizaje automático que puedan constituir una alternativa o complemento a los métodos numéricos estándar en la modelación de la propagación de ondas, con énfasis en la evaluación de su rendimiento computacional y aplicabilidad en sismología.

### 3.2. Objetivos específicos

- Mapear las técnicas de aprendizaje automático utilizadas en el modelado de la ecuación de ondas

aplicadas a la sismología, resaltando sus aplicaciones, alcances y desafíos actuales.

- Comparar métodos representativos de aprendizaje automático, frente a enfoques numéricos están-

dares, evaluando su precisión y eficiencia computacional, destacando sus ventajas, limitaciones y

potencial de integración.

- Evaluar la capacidad de las PINNs para resolver problemas inversos en sismología, en lo referente

a mantener una precisión comparable a la de los métodos estándar y, al mismo tiempo, reducir

los costos computacionales.

- Escalar los enfoques basados en aprendizaje automático para favorecer el uso de datos provenientes

de problemas en sismología en escenarios no controlados.

## 4. Estado del arte

En esta sección presentamos una revisión de los avances en el modelado directo e inverso de la propagación de ondas y en la aplicación del aprendizaje automático en sismología. Describimos los métodos utilizados para modelar matemáticamente ondas sísmicas y estimar las propiedades del subsuelo, así como los enfoques recientes que integran redes neuronales informadas por la física con métodos numéricos estándar.

### 4.1. Modelado de la propagación de ondas

En sismología, se usa la propagación de ondas sísmicas para comprender la estructura interna de la tierra. Sus aplicaciones abarcan desde la prospección de recursos energéticos hasta la identificación de fallas activas y el estudio de los procesos asociados a las placas tectónicas (Stein and Wysession, 2009; Alsadi, 2017). Estas aplicaciones requieren descripciones matemáticas capaces de reproducir el comportamiento de las ondas sísmicas, lo que motiva el uso de modelos matemáticos.

Un modelo matemático que describe la propagación de ondas en un medio busca representar, mediante una función, cómo evoluciona un sistema a lo largo del tiempo y en el espacio. Este tipo de modelos suele basarse en ecuaciones diferenciales, que permiten caracterizar la evolución temporal y espacial del sistema. En el modelado matemático, es común emplear dos enfoques generales: el problema directo y el problema inverso. El problema inverso consiste en determinar las causas a partir de un conjunto de observaciones (Röth and Tarantola, 1994; Tarantola, 2005); por ejemplo, inferir las propiedades de un medio, e.g. las velocidades de propagación en cada material, a partir de su respuesta ante la propagación de ondas.

Este enfoque es el opuesto al problema directo, en el cual se calculan los efectos a partir de propiedades del medio conocidas. Dado que el problema inverso parte de los efectos y busca identificar las causas, suele requerir la solución iterativa de modelos directos, lo que lo convierte en un proceso computacionalmente exigente.

En la Figura 5 se muestra de forma esquemática la relación entre el problema directo y el problema inverso en sismología: mientras el primero simula la propagación de ondas sísmicas a través de un modelo de velocidades conocido, el segundo utiliza los datos registrados para inferir las velocidades del subsuelo. En este ejemplo, se emplea el modelo de velocidades Overthrust (Aminzadeh et al., 1994) como referencia.

La ecuación escalar de ondas acústicas se utiliza ampliamente para el estudio de la propagación sísmica. Por ejemplo, en el trabajo de Moseley (2022) se utilizaron PINNs para modelar la propagación de ondas acústicas. En este contexto, los campos de densidad y velocidad pueden considerarse de manera independiente (Zhang et al., 2023). También, bajo la suposición de soluciones armónicas en el tiempo, la ecuación de onda acústica puede transformarse en la ecuación de Helmholtz, la cual se aplica frecuentemente en sismología (Song and Wang, 2023, 2022). Esta última describe la distribución espacial de los campos de onda para una frecuencia dada.

En la simulación numérica de ondas sísmicas, las condiciones de frontera desempeñan un papel esencial, ya que permiten evitar reflexiones artificiales en los límites del dominio computacional. Tradicionalmente, los métodos numéricos requieren técnicas de truncamiento del dominio, como las condiciones de frontera absorbentes (Absorbing Boundary Conditions, ABC) o las capas perfectamente acopladas (Perfectly Matched Layers, PML), para representar medios abiertos y minimizar reflexiones de ondas en las fronteras. Sin embargo, en el contexto de la inversión sísmica mediante PINNs, este requisito puede omitirse. De hecho, se ha demostrado que es posible realizar la inversión sísmica de manera efectiva con PINNs sin necesidad de imponer condiciones de frontera absorbentes explícitas (Zhang et al., 2023).

En las últimas décadas, se han propuesto diversos métodos numéricos para describir sistemas físicos mediante PDEs, como la ecuación de onda. Entre ellos, el método de diferencias finitas es uno de los más populares para resolver PDEs, y en particular la ecuación de ondas. Esto se debe posiblemente a su concepto sencillo y a su fácil implementación. Una revisión completa del método de diferencias finitas aplicado a la propagación de ondas puede encontrarse en el trabajo de Moczo et al. (2007). En este enfoque, las derivadas parciales se aproximan mediante operadores discretos que involucran diferencias entre puntos adyacentes de la malla. El método de diferencias finitas es adecuado para abordar problemas relacionados con estructuras geométricas simples. En contraste, otros métodos, como el de elementos finitos, ofrecen mayor flexibilidad en la malla, lo que facilita el manejo de fronteras geométricas complejas.

En las simulaciones de propagación de ondas, las ecuaciones en derivadas parciales se discretizan típicamente en una malla escalonada (Madariaga, 1976; Virieux, 1986). Este enfoque facilita la resolución del problema de la propagación de la ruptura. En particular, en el trabajo de Zhou et al. (2021) se propuso un método de diferencias finitas con operadores temporales y espaciales de longitud variable, con el fin de aumentar la estabilidad y eficiencia del método estándar. Asimismo, Liu et al. (2023) combinaron un esquema de diferencias finitas en malla escalonada estándar con PML para resolver ecuaciones de primer orden de velocidad–esfuerzo en 3D en acustoelasticidad, con el objetivo de simular la propagación de ondas.

Los métodos de elementos finitos son apropiados para tratar formas complejas y materiales heterogéneos debido a que permiten el uso de mallas irregulares. Ofrecen flexibilidad en el tamaño, la forma y el orden de aproximación. No obstante, una desventaja es la alta demanda de recursos computacionales. Esta metodología consiste en transformar el problema en un sistema de ecuaciones lineales utilizando la formulación débil de la ecuación diferencial correspondiente. Dicha transformación se lleva a cabo mediante una base de interpolación compuesta por polinomios definidos sobre dominios disjuntos, comúnmente llamados elementos.

Existen implementaciones de código abierto disponibles para aplicar métodos numéricos a la solución de la ecuación de ondas. Por ejemplo, SPECFEM, especializado en la propagación de ondas sísmicas, es ampliamente utilizado en simulaciones implementadas en Fortran para estructuras geológicas con elementos espectrales (Komatitsch et al., 2023, 2024; Hateley et al., 2020). DEVITO y SEISMIC_CPML utilizan diferencias finitas para el modelado (Louboutin et al., 2019; Komatitsch and Martin, 2007). Estas implementaciones de métodos estándar han permitido realizar simulaciones efectivas de la ecuación de propagación de ondas en medios elásticos (Moseley et al., 2020; Roncoroni et al., 2021; Mosser et al., 2020; Guo et al., 2024).

### 4.2. Métodos basados en aprendizaje automático

El campo del aprendizaje automático ha mostrado recientemente un potencial significativo en la aproximación de predicciones de fenómenos físicos. Estos métodos son capaces de capturar la física no lineal y ofrecen tiempos de inferencia sustancialmente más rápidos en comparación con las simulaciones estándar. En consecuencia, el aprendizaje automático se ha utilizado como una alternativa a los métodos convencionales, aprovechando su capacidad como aproximador universal de funciones Hornik (1991). Por ejemplo, las máquinas de vectores de soporte (Support Vector Machines, SVM) se han empleado para resolver ecuaciones diferenciales ordinarias y en derivadas parciales. Aunque este método fue diseñado originalmente para tareas de clasificación, se ha propuesto una extensión que aplica mínimos cuadrados a la función objetivo para resolver ecuaciones diferenciales (Mehrkanoon et al., 2012; Mehrkanoon and Suykens, 2015).

Los métodos basados en redes neuronales constituyen un subconjunto del aprendizaje automático, cuyos modelos están conformados por una red neuronal artificial con una o múltiples capas de procesamiento (ver Figura 6). Estos métodos han mostrado potencial para superar las limitaciones de diversos enfoques en campos como la visión por computador, el procesamiento de lenguaje natural y la genómica (LeCun et al., 2015; Goodfellow et al., 2016). La arquitectura fundamental de una red neuronal se compone de una capa de entrada, una capa de salida y un número arbitrario de capas ocultas. En particular, en una red neuronal completamente conectada, las neuronas en capas adyacentes están interconectadas, mientras que las neuronas dentro de una misma capa no comparten conexiones. Además, los métodos basados en redes neuronales han surgido como una herramienta atractiva para complementar y ampliar los solucionadores numéricos convencionales de ecuaciones en derivadas parciales.

Los métodos de redes neuronales guiados por datos son capaces de aprender directamente la solución de un sistema de ecuaciones en derivadas parciales a partir de los datos disponibles (Li et al., 2020, 2021). En particular, se pueden utilizar tanto datos experimentales de un fenómeno conocido o datos sintéticos generados por métodos numéricos estándar para entrenar la red neuronal. De este modo, es posible construir un modelo sustituto que prediga la solución de la ecuación diferencial parcial a un costo computacional reducido, manteniendo al mismo tiempo un nivel aceptable de precisión. Por ejemplo, uno de los tipos más populares de redes neuronales profundas son las redes neuronales convolucionales. Este método realiza convoluciones de características aprendidas con los datos de entrada y utiliza capas convolucionales 2D, lo que hace que esta arquitectura sea especialmente adecuada para el procesamiento de datos bidimensionales. Este tipo de método se ha implementado principalmente como herramientas que pueden ignorar la descripción matemática del fenómeno físico. Sin embargo, no siempre esto es lo deseado, porque esta información podría ser aprovechada, por ejemplo en el caso de contar con una cantidad limitada de datos. Con el fin de superar esta limitación, se ha propuesto utilizar PINNs.

Las PINNs constituyen un marco de aprendizaje automático diseñado para resolver PDEs (ver Figura 7). Estas redes aproximan la solución entrenando una red neuronal que minimiza una función de pérdida que incorpora el residual de la PDE, junto con términos que imponen las condiciones iniciales y de frontera. Dissanayake and Phan-Thien (1994) fueron de los primeros en introducir ideas clave para el uso de redes neuronales en la resolución de PDEs. Ellos trataron las redes neuronales como aproximadores de funciones y reformularon el problema como una tarea de optimización no restringida.

Posteriormente, Lagaris et al. (1998) perfeccionaron este enfoque al proponer una solución de prueba compuesta por dos partes: una diseñada para satisfacer inherentemente las condiciones iniciales o de frontera, y otra representada por una red neuronal para aproximar la solución de la ecuación diferencial. Basándose en estas contribuciones fundamentales, Raissi et al. (2019) reintrodujeron y extendieron la metodología utilizando técnicas modernas de aprendizaje profundo, lo que dio lugar al desarrollo de las PINNs. Las PINNs aproximan la solución de PDEs incorporando las ecuaciones gobernantes, y las condiciones de frontera e iniciales directamente en la función de pérdida. Esta estrategia impone las restricciones físicas del problema al minimizar la pérdida total, asegurando que la solución obtenida por la red neuronal sea coherente con la física subyacente. En particular, se considera una PDE general definida sobre un dominio Ω con frontera Γ:

$$
\mathcal{N}[u(\mathbf{x},t);\lambda]=0,\quad \mathbf{x}\in\Omega,\quad t\in[0,T],
$$

donde N es un operador diferencial parametrizado por los parámetros del modelo λ, u(x, t) es la solución desconocida, y Ω denota el dominio físico. Las condiciones de frontera e iniciales se especifican como:

$$
\mathcal{B}[u(\mathbf{x},t)]=0,\quad \mathbf{x}\in\Gamma,\quad t\in[0,T],
$$

y

$$
u(\mathbf{x},0)=u_0(\mathbf{x}),\quad \mathbf{x}\in\Omega.
$$

La función de pérdida total se compone de tres términos:

$$
L=L_{\Omega}+L_{\Gamma}+L_{\mathrm{IC}},
$$

donde LΩ impone la PDE en el dominio, LΓ impone las condiciones de frontera sobre Γ, y LIC impone las condiciones iniciales en t = 0. Esta formulación permite a la red neuronal aprender la solución mientras cumple inherentemente con las restricciones impuestas por la PDE, como se detalla en el Algoritmo 1.

```text
Algoritmo 1. Red Neuronal Informada por la Física para resolver PDEs
Entradas:
Conjunto de puntos de muestreo del dominio Ω con la PDE gobernante
Condiciones iniciales
Condiciones de frontera
Salidas:
Aproximación de la solución u(x, t)
En el caso de problemas inversos, parámetros estimados λ
  Inicializar parámetros: θ (y λ si se infieren)
  Definir hiperparámetros: tol, maxiter > 0, αₖ
  para cada método de optimización en {Adam, L-BFGS} hacer
      Inicializar contador de iteraciones: k = 0
      mientras k < maxiter y L(θ⁽ᵏ⁾ ) > tol hacer
          Evaluar: u(x, t; θ⁽ᵏ⁾ )
          Calcular pérdida total:
                                               L(θ⁽ᵏ⁾ ) = L_Ω + L_Γ + L_IC
          Actualizar:
                                             θ⁽ᵏ⁺¹⁾ = θ⁽ᵏ⁾ − αₖ ∇L(θ⁽ᵏ⁾ )
          Incrementar iteración: k = k + 1
       Terminar mientras
    Terminar para cada
    Retornar Modelo entrenado: u(x, t; θ)
```

Se consideran dos enfoques. El primero se centra en soluciones dirigidas por datos para problemas directos, con el objetivo de inferir el estado oculto u(x, t) a partir de parámetros del modelo λ conocidos. El segundo se orienta a la identificación de parámetros en problemas inversos, buscando los valores de λ que mejor se ajusten a los datos observados. Para cada caso, se implementan dos modelos: el modelo en tiempo continuo, que aproxima una función espacio-temporal, y el modelo en tiempo discreto, que utiliza métodos de Runge-Kutta para la integración temporal.

El desempeño de la PINN al resolver el mismo problema de Helmholtz bidimensional descrito en la Ecuación 1 se muestra en la Figura 8. Se utilizaron los hiperparámetros optimizados en el trabajo de Escapil-Inchauspé and Ruz (2023) y hard-constrains para las condiciones de frontera de Dirichlet.

$$
\hat f_\theta(x,y)=x(1-x)y(1-y)f_\theta(x,y),
$$

donde fθ (x, y) representa la salida libre de restricciones de la red neuronal, es decir, la función que la PINN aprende durante el entrenamiento. El factor x(1 − x)y(1 − y) garantiza que fˆθ (x, y) se anule en el contorno del dominio [0, 1]² , cumpliendo exactamente las condiciones de frontera homogéneas especificadas en la Ecuación 1.

Se observa que, al aumentar la cantidad de puntos de entrenamiento, la red mejora su capacidad para aproximar la solución analítica, reduciendo el error relativo. Este comportamiento es consecuencia de una mejor cobertura espacial del dominio, lo que permite capturar de manera más detallada las variaciones de la solución. En contraste, el tiempo de evaluación del modelo, una vez entrenado, permanece prácticamente constante, independientemente del número de puntos empleados. Esto se debe a que la fase de inferencia depende únicamente del tamaño del conjunto de puntos de evaluación y de la arquitectura de la red, y no del proceso de optimización previo. Dicho resultado evidencia la eficiencia del modelo PINN para realizar predicciones una vez finalizado el entrenamiento. No obstante, el tiempo de entrenamiento alcanza valores del orden de 10¹ s, lo que representa dos órdenes de magnitud más que el tiempo máximo registrado con el método de diferencias finitas en el ejemplo anterior.

El abordaje del problema inverso mediante PINNs ha sido aplicado en sismología, con el objetivo de avanzar en métodos como la FWI. Originalmente, las PINNs se implementaron utilizando una única FFNN. Sin embargo, también es posible emplear dos redes de manera independiente. Una para estimar el campo de desplazamientos y otra para el campo de velocidades y densidades (Zhang et al., 2023).

Los métodos de aprendizaje automático pueden complementar a las técnicas numéricas estándar en la resolución de PDEs. Por ejemplo, Yang and Ma (2021) propusieron el uso de una Red Generativa Adversativa de Wasserstein con Penalización de Gradiente (Wasserstein Generative Adversarial Network with Gradient Penalty, WGAN-GP), aplicada al problema de FWI, demostrando que los modelos basados en aprendizaje automático pueden aproximar operadores de propagación de ondas y ofrecer un complemento a los métodos estándar.

En resumen, el modelado de ondas en sismología avanza hacia la integración de métodos numéricos estándar y enfoques basados en aprendizaje automático. Los primeros destacan por su precisión, mientras que los segundos permiten reducir los costos asociados a la discretización mediante herramientas como las redes neuronales como aproximador de funciones, la diferenciación automática y las GPUs. La integración de ambos enfoques busca mejorar el desempeño en tareas de simulación e inversión sísmica.

## 5. Metodología

Inicialmente, realizamos una revisión exploratoria de la literatura con el propósito de identificar las técnicas de aprendizaje automático aplicadas al modelado de la ecuación de ondas en sismología. Según lo definido por Arksey and O’Malley (2005), una revisión exploratoria tiene como objetivo “mapear de manera rápida los conceptos clave que sustentan un área de investigación, así como las principales fuentes y tipos de evidencia disponibles”. Esta etapa permitió consolidar una base conceptual sobre los enfoques actuales, identificar sus limitaciones y reconocer oportunidades de mejora. Con base en estos hallazgos, estructuramos nuestra investigación en tres partes principales que orientaron el desarrollo del trabajo (ver Figura 9):

## 1. Comparación: En esta parte se analizan y comparan métodos representativos de aprendizaje au-

tomático con enfoques numéricos convencionales empleados en sismología. El objetivo es evaluar su precisión y eficiencia computacional, identificando las ventajas, limitaciones y el potencial de integración de las técnicas basadas en redes neuronales con los métodos estándar. Para ello, se aplican los criterios y métricas propuestos en McGreivy and Hakim (2024) y Grossmann et al. (2023). Estos criterios y métricas servirán también como referencia para los ejes siguientes, garantizando coherencia en el análisis comparativo y en la evaluación del desempeño de los modelos. Este análisis permite comprender los factores que influyen en el rendimiento de cada enfoque y determinar las condiciones bajo las cuales las técnicas de aprendizaje automático pueden ofrecer mejoras significativas.

## 2. Evaluación: En esta parte se evalúa la capacidad de las PINNs para abordar problemas inversos

en sismología. Para ello, se consideran enfoques propuestos en la literatura, como el de Zhang et al. (2023), donde se emplean redes independientes para estimar el campo de velocidades y el de desplazamientos, con el fin de evitar que la solución de una red influya o sesgue los resultados de la otra. El objetivo principal es determinar si estos modelos pueden mantener una precisión comparable a la de los métodos inversos estándar, reduciendo la complejidad computacional. Además, se explorarán estrategias de integración entre las PINNs y los métodos existentes, con el propósito de establecer un marco híbrido que combine las ventajas de ambos enfoques. La evaluación sigue los criterios y métricas definidos en el eje de comparación, lo que permite una valoración consistente del rendimiento de los modelos.

## 3. Escalamiento: En esta última parte, tras haber identificado los principales retos de los métodos

de aprendizaje automático y mapeado implementaciones exitosas, se busca llevar estos enfoques al ámbito sismológico. Para ello, se desarrollarán implementaciones que permitan escalar los métodos basados en aprendizaje automático hacia contextos sismológicos menos controlados. La revisión de literatura se complementará con una búsqueda dirigida a identificar estrategias que hayan demostrado abordar con éxito los desafíos del escalamiento en otros campos, especialmente aquellas que aún no han sido exploradas en aplicaciones sismológicas.

## 6. Cronograma

En esta sección se presenta el plan de trabajo y el cronograma de actividades definidos para alcanzar los objetivos planteados (ver Tabla 1). El proyecto tiene una duración total de 48 meses, con inicio en enero de 2024 y finalización en diciembre de 2027. Contempla una serie de fases interrelacionadas que incluyen la revisión de la literatura, el desarrollo de los tres ejes propuestos que orientan la investigación y la redacción tanto de artículos científicos como del manuscrito final.

## 7. Avances preliminares

En esta sección presentamos los resultados preliminares obtenidos hasta el momento de la redacción de este documento. Estos resultados corresponden principalmente a los dos primeros objetivos específicos definidos en la Sección 3.2. El primero se relaciona con la revisión exploratoria sobre el uso de técnicas de aprendizaje automático en la modelación de la propagación de ondas, con énfasis en aplicaciones en sismología, revisión que sustenta el estado del arte descrito en la Sección 4. Cabe señalar que este trabajo se encuentra actualmente en la fase final de redacción del borrador.

Como complemento de la revisión exploratoria, implementamos un repositorio de reproducibilidad en el cual se documentan y ponen a disposición los experimentos realizados con PINNs utilizando PyTorch. Este repositorio, tomado del enfoque original propuesto por Raissi et al. (2019), que fue inicialmente implementado en TensorFlow, ofrece código abierto y los ejemplos reproducibles que permiten verificar resultados, comparar implementaciones y facilitar el aprendizaje. De esta manera, se buscó garantizar la reproducibilidad del trabajo, y también ayudar en la adopción de estas metodologías por parte de investigadores interesados en profundizar en el método. El repositorio está disponible en: https://github.com/oscar-rincon/ReScience-PINNs.

En cumplimiento del segundo objetivo, desarrollamos un análisis comparativo entre dos enfoques de modelación numérica: el método de los elementos de frontera y las PINNs. Los principales resultados de esta investigación fueron presentados en el congreso internacional MadeAI2025, realizado en Porto, Portugal, en julio de 2025, y han sido sometidos para publicación en la revista indexada Engineering Computations, como parte de un número especial. La versión preimpresa del manuscrito se encuentra disponible en: https://doi.org/10.48550/arXiv.2509.12483. A continuación, se incluye el título y el resumen del trabajo:

### Comparative Analysis of Wave Scattering Numerical Modeling Using the Boundary Element Method and PINNs

Purpose: This study compares the Boundary Element Method (BEM) and Physics-Informed Neural Networks (PINNs) for solving the two-dimensional Helmholtz equation in wave scattering problems. The objective is to evaluate the performance of both methods under the same conditions. Design/methodology/approach: We solve the Helmholtz equation using BEM and PINNs for the same scattering problem. The PINNs are trained by minimizing the residual of the governing equations and boundary conditions, with their configuration determined through hyperparameter optimization, while the BEM is applied using boundary discretization. Both methods are evaluated in terms of solution accuracy, computation time, and generalization capacity. Findings: Numerical experiments were conducted by varying the number of integration points for BEM and the number of layers and neurons per layer for PINNs. Hyperparameter tuning identified an adequate PINN configuration for this particular problem as a network with 3 hidden layers, 25 neurons per layer, a learning rate of 10⁻² and a Sine activation function. At comparable accuracy, PINNs required training time is on the order of 10² s, one orders of magnitude longer than BEM (order 10¹ s). However, once trained, PINNs achieved evaluation times on the order of 10⁻¹ s, two orders of magnitude faster than BEM. The generalization capacity was also assessed outside the PINN training domain, where the relative error increased three orders of magnitude, while BEM maintained a consistent error level in the extended region. Originality/value: This work presents a direct comparison between PINNs and BEM for the Helmholtz equation. The analysis provides quantitative data on the performance of both methods, supporting their selection in future research on wave propagation problems and establishing future challenges and directions.

Otro resultado derivado de este proyecto corresponde al trabajo de grado desarrollado en el programa de Ingeniería Física por el estudiante Gregorio Pérez Bernal, enmarcado dentro del tercer objetivo específico planteado. Los principales hallazgos de esta investigación fueron presentados en la 5a Semana de la Geofísica, realizada en Bucaramanga, Colombia, en noviembre de 2025. Además, a partir de este trabajo se ha elaborado un borrador de artículo que propone un enfoque alternativo para el tratamiento de problemas en dominios no acotados. A continuación, se presentan el título y el resumen del trabajo:

### Evaluación de estrategias de aprendizaje automático para resolver problemas inversos en dominios semi-infinitos, usando redes neuronales informadas por la física

En este trabajo se propone y evalúa una estrategia alternativa de muestreo para resolver problemas inversos asociados a la ecuación de Helmholtz, con aplicaciones en geofísica usando redes neuronales informadas por la física (PINNs). El objetivo es abordar dominios semi-infinitos para resolver problemas afines a esta área. Para ello, se comparan dos formulaciones de PINNs: una entrenada con puntos muestreados uniformemente, la cual cuenta con condiciones de frontera absorbentes, y otra con un muestreo basado en las distribuciones normal y exponencial negativa, donde la densidad de puntos tiende a cero hacia el infinito. Los resultados muestran que ambas estrategias logran aproximaciones precisas de la solución del campo de ondas u y de la velocidad del medio c, aunque presentan diferencias notables en la distribución del error. Mientras que las fronteras absorbentes requieren menos hiperparámetros y convergen más rápido, el muestreo alternativo alcanza errores relativos menores para c cuando se dispone de suficientes datos. Estos hallazgos sugieren que la estrategia de muestreo propuesta puede ser una alternativa viable para representar dominios no acotados en problemas de propagación de ondas, con una limitación importante: la necesidad de contar con información de u y c en todo el dominio de entrenamiento.

Figura 1. Convergencia de la solución numérica de la ecuación de Helmholtz en 2D. (Fila superior) Distribuciones de puntos empleadas en las simulaciones, correspondientes a N = 10 × 10, 20 × 20 y 30 × 30. (Segunda fila) Mapas de contorno de la solución aproximada fˆ(x, y) para cada resolución. (Tercera fila) Cortes unidimensionales de fˆ(x, 0.375) que comparan la variación espacial de la solución aproximada (líneas en azul claro, azul oscuro y negro) con la solución analítica (línea gris). (Fila inferior) Gráficas de convergencia que muestran el error relativo y el tiempo de cómputo en función del número total de puntos.

Figura 2. La intersección entre el aprendizaje automático, el modelado de la propagación de ondas y la sismología, como marco de estudio de nuestra investigación.

Figura 3. Aproximación de una función objetivo mediante una red neuronal de una sola capa oculta con distinto número de neuronas. La curva gris indica la función original, mientras que las curvas azules muestran las aproximaciones obtenidas al aumentar gradualmente el número de neuronas. La curva negra es la aproximación final con el total de neuronas.

Figura 4. Crecimiento de la literatura y tendencias en framework de Python de aprendizaje automático. El panel superior izquierdo muestra la fracción de publicaciones relacionadas con métodos numéricos estándar y aprendizaje automático, mientras que el panel superior derecho presenta aquellas específicamente asociadas al modelado de la propagación de ondas. El panel inferior izquierdo muestra el interés relativo promedio en las principales frameworks de aprendizaje automático (TensorFlow, PyTorch y JAX), calculado como el promedio de sus valores normalizados de búsqueda en Google para este periodo de tiempo. El panel inferior derecho presenta la evolución temporal de dicho interés, medido como búsquedas en Google relativas al valor máximo observado (2015–2025). Los valores relativos de publicaciones se calcularon con respecto al número total de publicaciones indexadas en Scopus durante el mismo período (2010–2024).

Figura 5. Esquema ilustrativo de un problema directo e inverso en sismología. La simulación directa modela la propagación de ondas sísmicas en un medio de velocidades dado (Aminzadeh et al., 1994), superpuesto al campo de ondas generado por una fuente puntual (escala de azules y rojos) y registrado por una red de geófonos en superficie (triángulos negros). El problema inverso utiliza los datos registrados (sismogramas en la parte inferior) para estimar las propiedades del subsuelo.

Figura 6. Relación entre los subconjuntos de la inteligencia artificial y esquema básico de una red neuronal artificial. A la izquierda se muestra cómo las redes neuronales forman parte del aprendizaje automático y de la inteligencia artificial, destacando las redes neuronales informadas por la física (Physics Informed Neural Networks, PINNs) como una variante que integra leyes físicas en su entrenamiento. A la derecha se presenta la estructura general de una red neuronal utilizada como modelo sustituto, donde las variables de entrada (x, t) pasan por capas ocultas con funciones de activación (σ) para generar una salida u. El modelo se entrena con datos sintéticos o experimentales mediante un optimizador que ajusta los parámetros para reducir la función de pérdida.

Figura 7. Esquema representativo de una red neuronal informada por la física (PINN) aplicada a la ecuación de onda. A la izquierda se ilustra la relación entre el conocimiento físico y los datos: las redes neuronales puras dependen principalmente de grandes volúmenes de datos, mientras que las PINNs integran información física, permitiendo trabajar con conjuntos de datos reducidos. A la derecha se muestra la estructura del modelo, donde la red neuronal predice el campo u(x, t) y las derivadas espaciales y temporales se incorporan en la función de pérdida mediante la ecuación de onda, garantizando la consistencia física durante el proceso de optimización.

Figura 8. Desempeño de la PINN para el problema de Helmholtz en 2D con diferentes densidades de puntos de entrenamiento. (Fila superior) Distribuciones de muestreo aleatorias utilizadas durante el entrenamiento, correspondientes a 60, 80 y 100 puntos. (Segunda fila) Campos predichos fˆ(x, y) para cada caso. (Tercera fila) Cortes horizontales en y = 0.375, comparando la predicción de la PINN (línea de color azul, azul oscuro y negro) con la solución analítica (línea gris). (Fila inferior) Gráficas de convergencia que muestran el error relativo (izquierda) y los tiempos computacionales (derecha), ambos en escala logarítmica. En este caso, la red neuronal se definió como

Figura 9. Esquema general de la metodología propuesta. El diagrama ilustra el proceso seguido para la revisión exploratoria de la literatura, que inicia con la definición de términos de búsqueda y la consulta en las bases de datos Scopus y OpenAlex. Tras aplicar las restricciones de investigación y eliminar los registros duplicados, se obtuvo un conjunto depurado de estudios relevantes que permitió identificar los principales retos y oportunidades en el uso de PINNs para problemas sísmicos. A partir de estos resultados se formularon tres ejes metodológicos: Comparación, Evaluación y Escalamiento, que guían el desarrollo del estudio. En la etapa de comparación, se plantea un problema de dispersión de ondas por un obstáculo cilíndrico con solución analítica, resuelto mediante el método de elementos de frontera (Boundary Elements Method, BEM) y una PINN, a fin de establecer métricas de precisión y tiempo de cómputo. Durante la evaluación, se contrastará el desempeño de las PINNs frente a métodos inversos estándar, tomando la FWI como referencia, para analizar la hipótesis planteada sobre su eficiencia y precisión. Finalmente, para la fase de escalamiento hemos identificado retos en contextos no controlados, tales como el sesgo frecuencial, la cuantificación de la incertidumbre y los tiempos de entrenamiento. Posteriormente exploraremos y aplicaremos métodos que hayan sido aplicados con éxito en contextos no controlados.

Tabla 1. Cronograma de actividades de la investigación. El asterisco (∗ ) señala el mes correspondiente al examen preliminar, previsto como hito de evaluación intermedia del proyecto.

## References

Abadi, M., Barham, P., Chen, J., et al. (2016). {TensorFlow}: A System for {Large-Scale} Machine Learning. In Proceedings of the 12th USENIX Symposium on Operating Systems Design and Implementation (OSDI 16), pages 265–283.

Alsadi, H. N. (2017). Seismic Hydrocarbon Exploration. Advances in Oil and Gas Exploration & Production. Springer International Publishing, Cham.

Aminzadeh, F., Burkhard, N., Nicoletis, L., et al. (1994). SEG/EAEG 3-D modeling project: 2nd update. The Leading Edge, 13(9):949–952. Publisher: Society of Exploration Geophysicists.

Arksey, H. and O’Malley, L. (2005). Scoping studies: towards a methodological framework. International Journal of Social Research Methodology, 8(1):19–32. Publisher: Routledge _eprint: https://doi.org/10.1080/1364557032000119616.

Bonfanti, A., Santana, R., Ellero, M., and Gholami, B. (2024). On the generalization of PINNs outside the training domain and the hyperparameters influencing it. Neural Computing and Applications, 36(36):22677–22696.

Bradbury, J., Frostig, R., Hawkins, P., et al. (2018). JAX: composable transformations of Python+ NumPy programs.

Burden, R. L., Faires, J. D., and Burden, A. M. (2016). Numerical Analysis. Cengage Learning, Boston, MA.

Cuomo, S., Di Cola, V. S., Giampaolo, F., et al. (2022). Scientific Machine Learning Through Physics–Informed Neural Networks: Where we are and What’s Next. Journal of Scientific Computing, 92(3):88.

Deng, W., Nguyen, K. T. P., Medjaher, K., et al. (2023). Physics-informed machine learning in prognostics and health management: State of the art and challenges. Applied Mathematical Modelling, 124:325–352.

Dissanayake, M. W. M. G. and Phan-Thien, N. (1994). Neural-network-based approximations for solving partial differential equations. Communications in Numerical Methods in Engineering, 10(3):195– 201. _eprint: https://onlinelibrary.wiley.com/doi/pdf/10.1002/cnm.1640100303.

Escapil-Inchauspé, P. and Ruz, G. A. (2023). Hyper-parameter tuning of physics-informed neural networks: Application to Helmholtz problems. arXiv:2205.06704 [math].

Goodfellow, I., Bengio, Y., and Courville, A. (2016). Deep Learning. MIT Press. Google-Books-ID: omivDQAAQBAJ.

Grossmann, T. G., Komorowska, U. J., Latz, J., and Schönlieb, C.-B. (2023). Can Physics-Informed Neural Networks beat the Finite Element Method? arXiv:2302.04107 [cs, math].

Grossmann, T. G., Komorowska, U. J., Latz, J., and Schönlieb, C.-B. (2024). Can physics-informed neural networks beat the finite element method? IMA Journal of Applied Mathematics, 89(1):143– 174.

Guo, K., Zong, Z., Yang, J., and Tan, Y. (2024). Parametric elastic full waveform inversion with convolutional neural network. Acta Geophysica, 72(2):673–687.

Haghighat, E., Raissi, M., Moure, A., et al. (2021). A physics-informed deep learning framework for inversion and surrogate modeling in solid mechanics. Computer Methods in Applied Mechanics and Engineering, 379:113741.

Hao, Z., Liu, S., Zhang, Y., et al. (2023). Physics-Informed Machine Learning: A Survey on Problems, Methods and Applications. arXiv:2211.08064 [cs, math].

Hateley, J. C., Roberts, J., Mylonakis, K., and Yang, X. (2020). Deep learning seismic substructure detection using the Frozen Gaussian approximation. Journal of Computational Physics, 409:109313.

Hornik, K. (1991). Approximation capabilities of multilayer feedforward networks. Neural Networks, 4(2):251–257.

Hornik, K., Stinchcombe, M., and White, H. (1989). Multilayer feedforward networks are universal approximators. Neural Networks, 2(5):359–366.

Igel, H. (2017). Computational seismology: a practical introduction. Oxford University Press.

JingBo, Z. O. U., Cai, L. I. U., and PengFei, Z. (2023). Research progress of physics-informed neural network in seismic wave modeling. Progress in Geophysics, 38(1):430–448. Publisher: Progress in Geophysics.

Komatitsch, D. and Martin, R. (2007). An unsplit convolutional Perfectly Matched Layer improved at grazing incidence for the seismic wave equation. Geophysics, 72.

Komatitsch, D., Tromp, J., Garg, R., et al. (2024). SPECFEM/specfem3d: SPECFEM3D v4.1.1.

Komatitsch, D., Tromp, J., Gharti, H. N., et al. (2023). SPECFEM/specfem2d: SPECFEM2D v8.1.0.

Lagaris, I., Likas, A., and Fotiadis, D. (1998). Artificial neural networks for solving ordinary and partial differential equations. IEEE Transactions on Neural Networks, 9(5):987–1000.

LeCun, Y., Bengio, Y., and Hinton, G. (2015). Deep learning. Nature, 521(7553):436–444.

Li, Z., Kovachki, N., Azizzadenesheli, K., et al. (2020). Neural Operator: Graph Kernel Network for Partial Differential Equations. arXiv:2003.03485 [cs, math, stat].

Li, Z., Kovachki, N., Azizzadenesheli, K., et al. (2021). Fourier Neural Operator for Parametric Partial Differential Equations. arXiv:2010.08895 [cs, math].

Lino, M., Fotiadis, S., Bharath, A. A., and Cantwell, C. D. (2023). Current and emerging deep-learning methods for the simulation of fluid dynamics. Proceedings of the Royal Society A: Mathematical, Physical and Engineering Sciences, 479(2275):20230058. Publisher: Royal Society.

Liu, S., Zhou, Z., and Zeng, W. (2023). Simulation of Elastic Wave Propagation Based on Meshless Generalized Finite Difference Method with Uniform Random Nodes and Damping Boundary Condition. Applied Sciences (Switzerland), 13(3). Publisher: MDPI.

Louboutin, M., Lange, M., Luporini, F., et al. (2019). Devito (v3.1.0): an embedded domain-specific language for finite differences and geophysical exploration. Geoscientific Model Development, 12(3):1165–1187. Publisher: Copernicus GmbH.

Madariaga, R. (1976). Dynamics of an expanding circular fault. Bulletin of the Seismological Society of America, 66(3):639–666.

McGreivy, N. and Hakim, A. (2024). Weak baselines and reporting biases lead to overoptimism in machine learning for fluid-related partial differential equations. arXiv:2407.07218 [physics].

Mehrkanoon, S., Falck, T., and Suykens, J. A. K. (2012). Approximate Solutions to Ordinary Differential Equations Using Least Squares Support Vector Machines. IEEE Transactions on Neural Networks and Learning Systems, 23(9):1356–1367. Conference Name: IEEE Transactions on Neural Networks and Learning Systems.

Mehrkanoon, S. and Suykens, J. A. K. (2015). Learning solutions to partial differential equations using LS-SVM. Neurocomputing, 159:105–116.

Moczo, P., Robertsson, J. O., and Eisner, L. (2007). The Finite-Difference Time-Domain Method for Modeling of Seismic Wave Propagation. Advances in Geophysics, 48:421–516. Publisher: Academic Press Inc.

Moseley, B. (2022). Physics-informed machine learning: from concepts to real-world applications. http://purl.org/dc/dcmitype/Text, University of Oxford.

Moseley, B., Nissen-Meyer, T., and Markham, A. (2020). Deep learning for fast simulation of seismic waves in complex media. Solid Earth, 11(4):1527–1549.

Mosser, L., Dubrule, O., and Blunt, M. (2020). Stochastic Seismic Waveform Inversion Using Generative Adversarial Networks as a Geological Prior. Mathematical Geosciences, 52(1):53–79.

Paszke, A., Gross, S., Massa, F., et al. (2019). PyTorch: An Imperative Style, High-Performance Deep Learning Library. In Advances in Neural Information Processing Systems, volume 32. Curran Associates, Inc.

Rahaman, N., Baratin, A., Arpit, D., et al. (2019). On the Spectral Bias of Neural Networks. arXiv:1806.08734.

Raissi, M., Perdikaris, P., and Karniadakis, G. E. (2019). Physics-informed neural networks: A deep learning framework for solving forward and inverse problems involving nonlinear partial differential equations. Journal of Computational Physics, 378:686–707. Publisher: Academic Press.

Raissi, M., Yazdani, A., and Karniadakis, G. E. (2020). Hidden fluid mechanics: Learning velocity and pressure fields from flow visualizations. Science, 367(6481):1026–1030. Publisher: American Association for the Advancement of Science.

Roncoroni, G., Fortini, C., Bortolussi, L., et al. (2021). Synthetic seismic data generation with deep learning. Journal of Applied Geophysics, 190.

Röth, G. and Tarantola, A. (1994). Neural networks and inversion of seismic data. Journal of Geophysical Research: Solid Earth, 99(B4):6753–6768. _eprint: https://onlinelibrary.wiley.com/doi/pdf/10.1029/93JB01563.

Rüde, U., Willcox, K., McInnes, L. C., and Sterck, H. D. (2018). Research and Education in Computational Science and Engineering. SIAM Review, 60(3):707–754. Publisher: Society for Industrial and Applied Mathematics.

Seriani, G. and Oliveira, S. P. (2020). Numerical modeling of mechanical wave propagation. Rivista del Nuovo Cimento, 43(9):459–514. Publisher: Springer Science and Business Media Deutschland GmbH.

Song, C. and Wang, Y. (2022). High-frequency wavefield extrapolation using the Fourier neural operator. Journal of Geophysics and Engineering, 19(2):269–282.

Song, C. and Wang, Y. (2023). Simulating seismic multifrequency wavefields with the Fourier feature physics-informed neural network. Geophysical Journal International, 232(3):1503–1514.

Stein, S. and Wysession, M. (2009). An Introduction to Seismology, Earthquakes, and Earth Structure. Wiley-Blackwell, Malden, Mass. Berlin.

Tarantola, A. (2005). Inverse problem theory and methods for model parameter estimation. SIAM.

Vadyala, S. R., Betgeri, S. N., Matthews, J. C., and Matthews, E. (2022). A review of physics-based machine learning in civil engineering. Results in Engineering, 13:100316.

Vikas, Roy, S., and Ghosal, D. (2024). ShaVi-1.0: An interface enabled open source 2D acoustic full waveform inversion package. Computers & Geosciences, 187:105592.

Virieux, J. (1986). P-sv wave propagation in heterogeneous media: Velocity-stress finite-difference method. GEOPHYSICS, 51(4):889–901.

Virieux, J., Calandra, H., and Plessix, R.-E. (2011). A review of the spectral, pseudo-spectral, finite-difference and finite-element modelling techniques for geophysical imaging. Geophysical Prospecting, 59(5):794–813.

Yang, F. and Ma, J. (2021). Revisit Geophysical Imaging in A New View of Physics-informed Generative Adversarial Learning.

Zhang, Y., Tiňo, P., Leonardis, A., and Tang, K. (2020). A Survey on Neural Network Interpretability.

Zhang, Y., Zhu, X., and Gao, J. (2023). Seismic Inversion Based on Acoustic Wave Equations Using Physics-Informed Neural Network. IEEE Transactions on Geoscience and Remote Sensing, 61:1–11.

Zhou, H., Liu, Y., and Wang, J. (2021). Acoustic finite-difference modeling beyond conventi-onal Courant-Friedrichs-Lewy stability limit: Approach based on variable-length temporal and spatial operators. Earthquake Science, 34:123–236.
