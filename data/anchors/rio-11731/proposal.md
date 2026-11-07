# Applying machine learning and image feature extraction techniques to the problem of cerebral aneurysm rupture

## Motivation and problem presentation

At the beginning of our 21<sup>st</sup> century, the brain, its functioning and its pathologies, remain in great proportion a mystery to us. Yet, brain dysfunctions can have tremendous impact on a person's health, as the brain is the center of the nervous system. Among the problems seen with frequency are cerebral bleeding, or subarachnoid hemorrhages (SAH), due to rupture of aneurysm. An aneurysm consists in the apparition of a weakness of the arterial blood vessel that leads to local vessel dilation. If the aneurism breaks, the subsequent cortical region irrigation is interrupted, with potential brain damage as a consequence, or even death. Usually aneurysms do not cause any symptoms, unless they break and lead to SAH. With some frequency, aneurysms are detected in images undertaken for other reasons, whether of Computed Tomography (CT) Magnetic Resonance Imaging (MRI). Sometimes, the aneurism might swell so that it compresses nearby structures, leads to symptoms and is thus detected.

In Chile, subarachnoid hemorrhages have been found to be the 4th cause of cerebrovascular disease, which translates into an estimation of 700 new cases each year (Ministerio de Salud and República de Chile 2007). Three quarters of the new episodes of SAH occurs in persons between 25 and 65 years old, that is to say in the active portion of the population. According to this study, mortality due to SAH is of 40% monthly, and 46% at a 6-months-time; 30% of the non-deceased stays with some degree of dependence or incapacity.

There is a need to understand the mechanisms leading to the apparition of aneurysms, their growth and more important, to their rupture. Many efforts have been done, each exploring one direction at a time: broadly speaking either exploring biochemical or biomechanical factors (Sadasivan et al. 2013). The idea being that, for some biochemical reasons still to be defined, the local properties of the blood vessel wall seem to be affected; then the addition of hemodynamics parameters adding biomechanical stress on this portion of the wall would lead to rupture of the vessel. Yet, so far no clear factor could have been described that provides sufficient explanation of the apparition, or rupture, of aneurysm. Some authors suggest that, even if hemodynamics factors and purely mechanical explanations might be necessary, more than one factor might be playing a role (Sadasivan et al. 2013).

**The purpose of this study is to study the impact on aneurysm rupture of the***combination***of different parameters, instead of focusing on only one factor at a time as what is found in the literature, using machine learning and feature extraction techniques**. Up to now, variables acquired from medical images that are hypothetically related to the rupture risk are, as synthesised by (Sadasivan et al. 2013) :

- Aneurysms with an irregular or multilobulated shape

- Aneurysms with higher aspect ratios (height to neck)

- Anomalies in the vascular tree around the circle of Willis

- Larger aneurysm sizes

- Hemodynamic factors (flow impingement, pressure, wall shear stress)

Some known risk factors derived from the patient clinical history are, according to (Ministerio de Salud and República de Chile 2007, Sadasivan et al. 2013)

- Direct blood relatives with SAH in their health histories

- Previous SAH antecedents

- Renal polycystic disease

- Fibromuscular dysplasia

- Some connective tissue disorders

- Smoking habits

- Arterial hypertension

The discussion of understanding which factors, and in which combination, take part in aneurysm rupture takes relevance in the context of the complex decision to be taken of which therapy to apply. The options are: therapeutic abstention (no intervention); surgical intervention to clip the aneurysm; or endovascular intervention to treat the aneurysm with coils. Each intervention bares its own risks, and implies to use a complex ensemble of resources (human resources, OR, etc.) in hospitals, especially public hospitals, always under very high workload. In a few words: the decision is not easy and must be taken with care, so additional information will be of help to support this decision. Up to now, decisions are essentially made based on the patient’s clinical conditions, his/her age, and the aneurysm localization and size, besides considering the patient’s option (Ministerio de Salud and República de Chile 2007).

### Machine learning and feature extraction

Machine learning is an interdisciplinary field combining computer science and mathematics to develop models with the intent of delivering maximal predictive accuracy. This is done by detecting patterns from an incomplete set of examples composed of past data. For this reason, this is a data-driven discovery process. The quality of the predictions of machine learning algorithms rely mainly on the number of samples and the quality (amount of information contained) of the variables used to describe each sample of the phenomena (Bishop 2007). The following books are good references of these techniques and their applications (Bishop 2007, Kelleher et al. 2015, Schölkopf and Smola 2001, Vapnik 1998). Machine Learning is very promising in the field of neuroimage, where techniques as artificial neural networks, support vector machine, random forest, k-means, nearest neighbor, decision tree have been successfully applied (Huang and Chaovalitwongse 2015, Wernick et al. 2010). Currently Deep Learning Techniques have attracted the attention of the scientific comunity (Chen and Lin 2014). In this project we are going to explore both classical and novel machine learning techniques as a data scientist to find the best suitable techniques in a data mining process.

With medical data, there exist several practical, technical and ethical issues with acquiring great amounts of examples compared to other research fields such as information retrieval where millions of examples are freely available. Therefore, it is of utmost importance to extract the maximum amount of information of each example. This is why an exhaustive feature extraction phase is done.

Several machine learning techniques have been used in medicine in the past to diagnose patients (Hu et al. 2013), to provide support to the radiologist in the detection of aneurysms (Suniaga et al. 2012) and to predict radiation therapy outcomes among other things. Pubmed indicates an 52.4% increment in the number of publications (from 1204 to 1911) related with the keywords “machine learning” between years 2014 and 2015, being this a very active field of research.

Depending on the problem, different kinds of features are needed. Nowadays, machine learned features extracted from raw data are becoming more used, as deep learning approaches have been very successful. However, the interpretation of those features is an open problem, as the clear understanding of the role of each feature is what could give a deeper insight into the aneurysms causes and risk factors.

### Feature extraction methods employed with aneurysm data

Up to now, what has been used in features extraction methods based on angiographic image analysis is the following: the first step in the feature extraction step corresponds to the vascular geometry creation. Using the angiographic images a three-dimensional triangulated surface is obtained using an automatic segmentation method based on geodesic active regions in combination with an image standardization technique (Hernandez and Frangi 2007). Employing this model, different features are extracted. Morphological features, such as the aneurysm aspect ratio, non-sphericity index (Raghavan et al. 2005), volume and surface. Other more sophisticated descriptors to characterize its shape are the three-dimensional Zernike moment invariants (Millán et al. 2007). Hemodynamics (blood flow) is also analyzed extracting information like maximum and mean velocities defined at peak systole and averaged over the cardiac cycle, this based on a blood flow simulation that use the three-dimensional geometry obtained in the first step (Villa-Uriol et al. 2011). Other measurements computed on the model surface are areas of elevated pressure, impingement jet location, maximum static pressure and the wall shear stress (Villa-Uriol et al. 2011). A problem is that these measures depend on the location of the aneurysm neck, which is not detected reliably by the existing automated algorithms (Villa-Uriol et al. 2011). Additionally, an accurate structural analysis of the blood vessels would possibly have the best predictive capabilities. Nevertheless, in practice it requires too many assumptions and simplifications, not being sufficiently reliable (Ma et al. 2007).

A possible contribution to the state of the art would be a better aneurysm neck detection method. Also, it has been noted in (Villa-Uriol et al. 2011) that the feature extraction process could be enhanced by the use of additional information of the patient, such as known diseases that could give prior information to take into account, instead of using the same model for everyone. A different approach is to optimize different existing methods, as most of them are time expensive, taking several minutes, being sub-optimal for the very high loads in hospitals.

### Feature Selection

Having the features to feed a machine learning algorithm, the predicted rupture risk can be computed. However, to understand the underlying principles involved in the rupture process, having a great amount of features is counterproductive, since most features may not be involved in the process. The process of finding the most relevant features is known as feature selection.

Nowadays, the reasons of aneurysm formation and rupture are unknown. Therefore, even if the feature selection process may only give a set of important features (in a statistical sense) without any further descriptions, it may give some hints about what variables are correlated with the rupture in dependent (if they only affect the process if other variables have a range of values) and independent ways.

Bisbal et al. (2011) initiated work on cerebral aneurysm description using data mining approach based on demographic, clinical and images data on 157 cases. However, there are several aspects to improve in the feature selection process, such as not assuming independency and linearity between the different variables. For example, in (Izbicki et al. 2011) variable pairs where found to be significant for assessing the rupture risk of abdominal aneurysms. It is also important to take the different error types into account in order to define with greater precision the performance of the proposed prediction.

## Hypothesis

The identification and combined use of relevant variables extracted from clinical, demographical, environmental and medical imaging data sources will improve the estimation of the intracranial aneurysm rupture risk, with respect to the actual practiced method.

## Objectives

To identify relevant variables that may help in the process of predicting the risk of intracranial aneurysm rupture using machine learning and image processing techniques based on structured and non-structured data from multiple sources.

### Specific objectives

1. Collection and storage of data from multiple sources

2. Features extraction from multiple sources:medical images, demographic, environmental and epidemic information and the patient history record.

3. Use every feature available to build a rupture risk prediction model, taking into account difficulties such as missing data, error cost, imbalanced classes and the use of features in different feature spaces.

4. Identify the relevant features for the prediction model and their respective correlation, that is what sets of variables are correlated and their relevance in the model.

## Methodology and work plan

The research methodology will be an experimental methodology. This study corresponds to an analytic transversal study with prospective and retrospective characteristics. This has a focus on evaluating new solutions for problems. Two main phases are distinguished. The first one is an exploratory phase where the problem is studied in search of relevant questions about the studied system. The second phase will attempt to answer these questions with thoughtful experiments.

In this project, the object of study is the rupture risk of aneurysms and its relationship with the observable variables.

The steps involved in the methodology are:

1. Up-to-date revision and study of the state of the art.

2. Questions identification and hypothesis proposal.

3. Design and implement a method to test the hypothesis.

4. Design, implement and run adequate experiments.

5. Analyze, discuss and document the results.

Additional practices transversal to the study consider testing every software piece within a Testing Driven Development framework to avoid small errors, use a Concurrent Versions System to be able to reproduce past results and to have better diagnose tools in case of software bugs appear. Moreover, not only the experiments results should be documented, also the experiments setup (data, parameters, software revision) and the software itself.

We are going to use public available data of weather conditions together with clinical and demographic data with the intracranial aneurysm images obtained from the angiograph of the Hospital Carlos van Buren of Valparaíso.

The time to accomplish the proposal is 3 years. The project is divided in four phases, closely related to the specific objectives:

- Phase 1 – Data collection and storage (March 2017 – July 2017)

- Phase 2 – Feature extraction from multiple sources (May 2017 – November 2018)

- Phase 3 – Build model describing aneurysm rupture through the extracted feature combination (November 2018 – September 2019)

- Phase 4 – Identify relevant variables in the rupture process (September 2019 – February 2020)

The following is a brief summary of the phases’ activities (described in greater depth in the Proposal description section) with their respective scheduling.

### Phase I

#### Aneurysm causes - state of the art (March 2017 – May 2017)

At the beginning, the first task is to confirm that our prior conception of the information that is hypothesized to be relevant to estimate the risk of rupture is exhaustive. This information will be used to guide the data collection and feature extraction processes.

#### Hospital data collection (March 2017 – June 2017 retrospective, December 2018, December 2019 prospective)

The first step will be focus on data recollection from the Hospital Carlos van Buren (HCvB). It is important to mention that this project is inserted in a work team, namely in the HCvB: Dr. Pablo Cox and Dr. Rodrigo Riveros, interventional neuro-radiologists, and RT Maximiliano Godoy. HCvB is the public hospital of the Valparaíso region and this Hospital is a center of reference in neurology and neurosurgery in Chile.

The proposal is to undertake a retrospective and prospective study, to include patients from 2014 to 2016 retrospectively and from June 2017 up to December 2019 prospectively, counting on the approval by the local Ethical Committee. Inclusion criteria will be based on presenting a confirmed diagnostic of cerebral aneurysm. Patients will be enrolled through the Angiography Department of the Hospital, by the interventional neuro-radiologists of this project. No change will be applied in the way the patient is diagnosed or treated, only his/her data will be included in the present study. According to the registries from previous years, the Angiography Department of HCvB receives 100 patients per year with diagnostic of cerebral aneurysm, 83% of them ruptured. Specifically from 2014 to 2015, 238 patients with aneurysms were diagnosed in Angiography of the HCvB. In the prospective period of 2.5 years, we are expecting the additional inclusion of 250 patients.

Data to be collected are

- Angiographic images (already in DICOM format)

- Informs: radiologist inform to establish diagnostic; radiologist inform of intervention (already in digital format)

- Health records: these data are already accessible in a digital home-made database in the Angiography Deparment of HCvB, based on FileMaker, developed and administrated by RT Maximiliano Godoy
  - Patient demographic information. Age, gender, weight, height, BMI, city of residence (to be related to epidemic data and weather data)
  - Diagnostic (ICD10) and comorbidity
  - Clinical and treatment information: Glasgow score, drugs used (which ones in which concentrations, or which suspended), allergies, number of punctures, etc.
  - Laboratory analysis, in particular PCR, among others

- Epidemic, from the Ministry of Health (Departamento de Estadísticas e Información de Salud DEIS http://www.deis.cl) : in particular, registry of seasonal variation (syncytial virus, and others).

- Weather data, in combination with the epidemic information. The “Centro de Ciencia del Clima y la Resiliencia” (http://www.cr2.cl) has released in 2016 a tool to access the Chilean historical weather data, including variables, such as mean, maximum and minimum temperatures and precipitations across the country, including at least 229 weather stations. In this step it is necessary to obtain all the information available since year 2014, so it can be later used jointly with the aneurysms rupture dates.

The inclusion of epidemic and weather data is motivated by the recent observations of neuroradiologist that there seems to be a peak of aneurysm ruptures observed in relation with seasonal fluctuations (syncytial virus for instance). The underlying hypothesis is that rupture might be influenced by mechanisms of inflammation, in combination with hemodynamic and biomechanical stresses exerted over the arterial wall.

#### Data storage (May 2017 – July 2017)

The *Proyecto de Mejoramiento Institucional* UVA1402 for the *Development of an Interdisciplinary Platform for Healthcare Innovation* being executed by the institution will provide a secure database to store the information. The objective of this task is to centralize the access of all the data in a unique database and to anonymize the data, so only the relevant clinical professionals may access the identity of the person behind specific data.

The initial computational framework implementation (client-side) will also be considered for the retrieval and the processing of the data.

#### Technical report (May 2017 – August 2017)

Write a report to summarize the aneurysm rupture information related to each resource and a detailed data description from each source for future reference.

### Phase II

#### Medical images feature extraction (May 2017 – April 2019)

The initial problems detected in the feature extraction stage of the image characterization problem will be further explored, such as robust aneurysm neck detection, fast and robust three-dimensional mesh computation and new feature engineering to describe the aneurysm, since features like the non-sphericity index have been shown to have a significant correlation with the aneurysm rupture (Villa-Uriol et al. 2011). A new promising feature that will be pursued is the automatic estimation of the vascular age of the patient, as the two experienced interventional neuroradiologists members of this project are able to qualify the patient’s vascular age as a function of the artery tree, visible on the angiography.

The first step, after briefly exploring the existing problems and their solutions, will be the initial build of a flexible and modular computational framework for image processing, capable of easily integrating external libraries to use whenever is possible existing software solutions, such as ITK (Insight Segmentation and Registration Toolkit) and VTK (The Visualization Toolkit), to avoid re-implementing algorithms, since it is a time demanding task. Naturally, the integration of different external solutions will be done as needed, but it is important to lay a robust foundation to allow this to happen seamlessly.

Considering that, the methodology steps will be applied to each of the following tasks:

- Initial computational framework implementation for image processing

- Robust aneurysm neck detection

- Vascular tree description

- Fast and robust three-dimensional mesh computation

- Morphological aneurysm description

- Additional feature consideration

Additionally, a first paper will be written to be published in a conference of level A or A/B in the CORE system or in a journal (April 2019).

#### Other data feature extraction (July 2018 – April 2019)

The rest of the information is composed of a plethora of different features, such as time series (weather and epidemic data), categorical (smoking habit) and numerical information (age, height). To take advantage of this diversity, it is important to carefully extract relevant features, so they provide additional information.

The following tasks are identified for which the proposed methodology will be applied:

- Relevant features for weather data extraction, such as humidity, temperature and their changes in short time intervals in specific locations

- Epidemic data feature extraction

- Health records information extraction

- Dimension reduction by finding correlated variables

### Phase III

#### Feature combination for aneurysm description (May 2019 - October 2019)

Using all the extracted features, the aneurysm rupture risk will be modeled using a data-driven approach. It will be very important to take into account the different kind of features and missing values, as it has been shown that in the classifying process this can have a very significant impact (Bisbal et al. 2011).

Specifically, the following task have been identified:

- Missing value estimation (November 2018 – January 2018)

- Different feature space combination (February 2018 – April 2018)

#### Aneurysm rupture risk estimation according to combined features (May 2019 – October 2019)

To make a good estimation, it is important to use or modify a classifier that is able to take into account the risks of each decision and give a confidence on its estimation.

- Imbalanced classes impact quantification and consideration (May 2019 – June 2019)

- Error cost inclusion (June 2019 – July 2019)

- Classifier confidence estimation (July 2019 – August 2019)

- Rupture risk prediction (August 2019 – September 2019)

The publication of the experiments results and insights acquired will be published in an ISI indexed Journal of the area article (April 2019 – September 2019).

### Phase IV

#### Feature filtering and selection to identify the quantitative role of the individual features (September 2019 – February 2020)

After obtaining a good classification accuracy compared to the existing literature, the objective is to identify the subset of the most relevant features and their correlations that could explain the rupture of cerebral aneurysms. The tasks to achieve this objective are:

- Find lineal and non-lineal correlation among different variables sets and the predicted aneurysm rupture risk. This should take into account variables of the same source and multiple sources (September 2019 – November 2019)

- Decrease the number of used features to a minimum maintaining the classifier’s predictive precision (December 2019 – January 2020)

The publication of the experiments results and insights acquired will be published in an ISI indexed Journal of the area article (October 2019 – February 2020)

### Available Resources

The sponsoring institution is executing the PMI (*Plan de Mejoramiento Institucional*) UVA1402 for the *Development of an Interdisciplinary Platform for Healthcare Innovation* . The actual available equipment includes two multi-processor servers with more than sufficient storage for all the required data of the study and services to store sensible data. Additionally, personal powerful workstations are available for heavy processing tasks. In this context, the data are stored within the custody of *Universidad de Valparaiso*’s Informatics Division (DISICO), with physical and digital safeguard.

Physical space, access to the university library, internet connection and relevant journals subscriptions are also available.

## Funding program

2017 Postdoctoral Grant

## Grant title

Applying machine learning and image feature extraction techniques to the problem of cerebral aneurysm rupture

## Hosting institution

Universidad de Valparaiso, Valparaiso, Chile

Hospital Carlos van Buren, Valparaiso, Chile

## Ethics and security

The proposal is to undertake a retrospective and prospective study, to include patients from 2014 to 2016 retrospectively and from June 2017 up to December 2019 prospectively, counting on the approval by the local Ethical Committee.

## Conflicts of interest

The authors do not present any conflicts of interest to report.

## References

Bisbal Jesus, Engelbrecht Gerhard, Villa-Uriol Mari-Cruz, Frangi Alejandro F. 2011. Prediction of Cerebral Aneurysm Rupture Using Hemodynamic, Morphologic and Clinical Features: A Data Mining Approach. Lecture Notes in Computer Science. http://dx.doi.org/10.1007/978-3-642-23091-2_6. https://doi.org/10.1007/978-3-642-23091-2_6

Bishop C. M. 2007. Pattern Recognition and Machine Learning. Heidelberg, Germany: Springer 2006. i‐xx, 740 pp., ISBN: 0‐387‐31073‐8 $74.95 Hardcover. Kybernetes. 36. 2. 275. 275. http://dx.doi.org/10.1108/03684920710743466. https://doi.org/10.1108/03684920710743466

Chen Xue-Wen, Lin Xiaotong. 2014. Big Data Deep Learning: Challenges and Perspectives. IEEE Access. 2. 514. 525. http://dx.doi.org/10.1109/access.2014.2325029. https://doi.org/10.1109/access.2014.2325029

Hernandez Monica, Frangi Alejandro F. 2007. Non-parametric geodesic active regions: method and evaluation for cerebral aneurysms segmentation in 3DRA and CTA. Medical image analysis. 11. 3. 224. 41. http://dx.doi.org/10.1016/j.media.2007.01.002. https://doi.org/10.1016/j.media.2007.01.002

Huang Shuai, Chaovalitwongse W. Art. 2015. Computational Optimization and Statistical Methods for Big Data Analytics: Applications in Neuroimaging. The Operations Research Revolution. http://dx.doi.org/10.1287/educ.2015.0135. https://doi.org/10.1287/educ.2015.0135

Hu Xinhai, Cammann Henning, Meyer Hellmuth-A, Miller Kurt, Jung Klaus, Stephan Carsten. 2013. Artificial neural networks and prostate cancer--tools for diagnosis and management. Nature reviews. Urology. 10. 3. 174. 82. http://dx.doi.org/10.1038/nrurol.2013.9. https://doi.org/10.1038/nrurol.2013.9

Izbicki R., Lee A. B., Finol E. A. 2011. Assessment of Aortic Aneurysm Rupture Risk. Carnegie Mellon University. Research Showcase @ CMU. http://repository.cmu.edu/cgi/viewcontent.cgi?article=1068&context=statistics

Kelleher J. D., Mac Namee B., D'Arcy A. 2015. Fundamentals of Machine Learning for Predictive Data Analytics. Algorithms, Worked Examples, and Case Studies. MIT Press. 624. 9780262029445

Ma Baoshun, Lu Jia, Harbaugh Robert E, Raghavan Madhavan L. 2007. Nonlinear anisotropic stress analysis of anatomically realistic cerebral aneurysms. Journal of biomechanical engineering. 129. 1. 88. 96. http://dx.doi.org/10.1115/1.2401187. https://doi.org/10.1115/1.2401187

Millán R D, Dempere-Marco L, Pozo J M, Cebral J R, Frangi A F. 2007. Morphological characterization of intracranial aneurysms using 3-D moment invariants. IEEE transactions on medical imaging. 26. 9. 1270. 82. http://dx.doi.org/10.1109/TMI.2007.901008. https://doi.org/10.1109/TMI.2007.901008

Salud Ministerio de, Chile República de. 2007. Guía clínica hemorragia subaracnoidea secundaria a rotura de aneurismas cerebrales. Guía clínica

Raghavan Madhavan L, Ma Baoshun, Harbaugh Robert E. 2005. Quantified aneurysm shape and rupture risk. Journal of neurosurgery. 102. 2. 355. 62. http://dx.doi.org/10.3171/jns.2005.102.2.0355. https://doi.org/10.3171/jns.2005.102.2.0355

Sadasivan Chander, Fiorella David J., Woo Henry H., Lieber Baruch B. 2013. Physical Factors Effecting Cerebral Aneurysm Pathophysiology. Annals of Biomedical Engineering. 41. 7. 1347. 1365. http://dx.doi.org/10.1007/s10439-013-0800-z. https://doi.org/10.1007/s10439-013-0800-z

Schölkopf B., Smola A. J. 2001. Learning with Kernels. Support Vector Machines, Regularization, Optimization and Beyond. MIT Press. 648. 9780262194754

Suniaga Santiago, Werner Rene, Kemmling Andre, Groth Michael, Fiehler Jens, Forkert Nils Daniel. 2012. Computer-Aided Detection of Aneurysms in 3D Time-of-Flight MRA Datasets. Lecture Notes in Computer Science. http://dx.doi.org/10.1007/978-3-642-35428-1_8. https://doi.org/10.1007/978-3-642-35428-1_8

Vapnik V. N. 1998. Statistical Learning Theory. Wiley. 768. 978-0-471-03003-4

Villa-Uriol M. C., Berti G., Hose D. R., Marzo A., Chiarini A., Penrose J., Pozo J., Schmidt J. G., Singh P., Lycett R., Larrabide I., Frangi A. F. 2011. @neurIST complex information processing toolchain for the integrated management of cerebral aneurysms. Interface Focus. 1. 3. 308. 319. http://dx.doi.org/10.1098/rsfs.2010.0033. https://doi.org/10.1098/rsfs.2010.0033

Wernick M. N., Yang Y, Brankov J. G., Yourganov G., Stretcher S. C. 2010. Machine Learning in Medical Imaging. IEEE Signal Processing Magazine. 27. 4. 25. 38. https://doi.org/10.1109/MSP.2010.936730
