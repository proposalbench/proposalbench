# eEcoLiDAR, eScience infrastructure for ecological applications of LiDAR point clouds: reconstructing the 3D ecosystem structure for animals at regional to continental scales

## Abstract

The lack of high-resolution measurements of 3D ecosystem structure across broad spatial extents impedes major advancements in animal ecology and biodiversity science. We aim to fill this gap by using Light Detection and Ranging (LiDAR) technology to characterize the vertical and horizontal complexity of vegetation and landscapes at high resolution across regional to continental scales. The newly LiDAR-derived 3D ecosystem structures will be applied in species distribution models for breeding birds in forests and marshlands, for insect pollinators in agricultural landscapes, and songbirds at stopover sites during migration. This will allow novel insights into the hierarchical structure of animal-habitat associations, into why animal populations decline, and how they respond to habitat fragmentation and ongoing land use change. The processing of these massive amounts of LiDAR point cloud data will be achieved by developing a generic interactive eScience environment with multi-scale object-based image analysis (OBIA) and interpretation of LiDAR point clouds, including data storage, scalable computing, tools for machine learning and visualisation (feature selection, annotation/segmentation, object classification, and evaluation), and a PostGIS spatial database. The classified objects will include trees, forests, vegetation strata, edges, bushes, hedges, reedbeds etc. with their related metrics, attributes and summary statistics (e.g. vegetation openness, height, density, vertical biomass distribution etc.). The newly developed eScience tools and data will be available to other disciplines and applications in ecology and the Earth sciences, thereby achieving high impact. The project will foster new multi-disciplinary collaborations between ecologists and eScientists and contribute to training a new generation of geo-ecologists.

## List of participants

Core research team

- Zsófia Koma (PhD student, University of Amsterdam, Amsterdam, The Netherlands)

- Christiaan Meijer (eScience Research Engineer, Netherlands eScience Center, Amsterdam, The Netherlands)

- W. Daniel Kissling (Associate Professor, University of Amsterdam, Amsterdam The Netherlands)

- Arie C. Seijmonsbergen (Assistant Professor, University of Amsterdam, Amsterdam, The Netherlands)

- Willem Bouten (Professor, University of Amsterdam, Amsterdam, The Netherlands)

- Ruud P. B. Foppen (Professor, Radboud University, Nijmegen, The Netherlands)

Management support

- Elena Ranguelova (eScience coordinator, Netherlands eScience Center, Amsterdam, The Netherlands)

Associated Master students

- Tristan Bakx (MSc student, University of Amsterdam, Amsterdam, The Netherlands)

- Jim Groot (MSc student, University of Amsterdam, Amsterdam, The Netherlands)

- Berend Wijers (MSc student, University of Amsterdam, Amsterdam, The Netherlands)

- Peter Haacke (MSc student, University of Amsterdam, Amsterdam, The Netherlands)

- Chris Lucas (MSc student, University of Amsterdam, Amsterdam, The Netherlands)

Associated researchers

- Adriaan M. Dokter (Postdoc, Cornell Lab of Ornithology, Cornell University, USA)

- Jesus Aguirre-Gutiérrez (Postdoc, Environmental Change Institute, University of Oxford, UK)

- Henk Sierdsema (Researcher, Sovon Vogelonderzoek Nederland, Nijmegen, The Netherlands)

- Marco Heurich (Deputy head, Department of Conservation and Research, Bavarian Forest National Park, Grafenau, Germany)

Advisory board

- Jacobus C. Biesmeijer (Professor, Naturalis Biodiversity Center, Leiden, The Netherlands)

- Peter J.M. van Oosterom (Professor, Delft University of Technology, Delft, The Netherlands)

- Andrew K. Skidmore (Professor, University of Twente, Enschede, The Netherlands)

- Maurice Bouwhuis (Computational scientist, SURFsara, Amsterdam, The Netherlands)

- Hans van Gasteren (Head of Nature Bureau, Royal Netherlands Air Force, Gouda, The Netherlands)

- Niels S. Anders (Researcher, Geodan, Amsterdam, The Netherlands)

## Science: background, research questions, approach, and innovation

Humans have a tremendous impact on the natural environment. For instance, human-modified landscapes are now dominating our planet and the conversion, degradation and loss of habitat leads to species extinctions and severely affects the distribution of species and ecosystems and the services they provide to humanity Hoekstra et al. 2005, Cardinale et al. 2012, Ceballos et al. 2015, Newbold et al. 2015. Hence, national and international programmes —such as those related to the Group on Earth Observations Biodiversity Observation Network (GEO BON), the United Nations (UN) Convention on Biological Diversity (CBD), or the Intergovernmental Science-Policy Platform on Biodiversity and Ecosystem Services (IPBES)— demand to quantify ecosystem structure and changes in land use and their effects and impacts on biodiversity to better assess progress towards achieving policy targets, such as the Aichi Biodiversity Targets for 2020 set by the CBD (Pereira et al. 2013, Kissling et al. 2015, Skidmore et al. 2015).

A major bottleneck for predictive biodiversity modelling is the current lack of high-resolution (i.e. fine-scale) measurements of habitat structures and 3D characteristics of vegetation across regions and continents (Davies and Asner 2014, Dantas de Paula et al. 2016, Lausch et al. 2016). Animals depend on the vertical and horizontal distribution of plants at different spatial scales (Fig. 1), ranging from regional habitat distributions to 3D vegetation structure within local habitats (Cody 1985, Wiens 1989, Buler et al. 2007, Kissling et al. 2008, Fuller 2012). However, current studies usually do not account for this hierarchical nature of animal-habitat associations (Kristan III 2006) because they either use only coarse habitat information (e.g. CORINE land cover types) over large spatial extents or very local information with a fine grain but a small spatial extent. For instance, the CORINE Land Cover database (http://land.copernicus.eu/pan-european/corine-land-cover), a widely used data source, provides consistent geographical information on land cover across Europe, but only distinguishes 44 coarse land cover classes (e.g. only three forest and five wetland types). Small and scattered habitats such as reedbed and linear elements (e.g. hedges) in agricultural landscapes are generally not well represented, and the 3D structural and compositional characteristics of land cover types are not captured at all. This is insufficient for modelling species distributions of animals because their abundances as well as nesting and foraging requirements depend on the fine-scale structure of the landscape (e.g. density, cover and openness of vegetation, edges) (Cody 1985) and on the specific 3D characteristics of the habitats (e.g. vertical and horizontal distribution of biomass) (MacArthur and MacArthur 1961, Goetz et al. 2010, Lesak et al. 2011, Zellweger et al. 2013) (Fig. 1). Hence, high-resolution measurements of 2D and 3D ecosystem structures at fine grain sizes are needed across broad spatial extents (regional to continental) to make major advancements in animal ecology and biodiversity science (Wulder et al. 2004, Kissling et al. 2008, Vierling et al. 2008, Zhang et al. 2013, Dantas de Paula et al. 2016, Zellweger et al. 2016).

An exciting opportunity to improve predictive biodiversity modelling is the increasing availability of high-resolution remote sensing (RS) data on ecosystem structures derived from Light Detection and Ranging (LiDAR). LiDAR data enable us to fill the existing data gap by providing fine-scale habitat information across large spatial extents (Lim et al. 2003, Wulder et al. 2012, Davies and Asner 2014). To date, LiDAR-derived 3D ecosystem structures have mainly been applied in local-scale ecological studies at small spatial extents (Davies and Asner 2014). Quantified across regions and continents, the vertical and horizontal complexity of forests (e.g. tree heights, densities, canopy cover and gaps etc.) and the extent and structure of open habitats (e.g. hedges in agricultural landscapes, shrub density and coverage, height and density of reedbeds etc.) can be used for predictive biodiversity modelling. For instance, LiDAR-derived habitat data can be used together with other abiotic variables (e.g. climate, topography, soil and land cover types) (Kissling et al. 2012, Eskildsen et al. 2013, Aguirre-Gutiérrez et al. 2016) in species distribution models (SDMs) (Elith and Leathwick 2009) to predict the abundance and distribution of animals with unprecedented detail and accuracy. This is particular relevant for animal species that depend on complex vegetation structures (e.g. 3D structure of forests) as well as those that rely on linear habitats in agricultural landscapes (e.g. hedges) or on small and scattered habitat types (e.g. marshlands) that are underrepresented in current land cover maps.

The aim of this project is to use LiDAR technology to quantify fine-scale 3D ecosystem structures across broad spatial extents. Across Europe, we will focus on (1) ground-nesting breeding birds in forests (e.g. Wren, Wood Warbler, Common Nightingale etc.) for which the 3D forest structure (e.g. forest height, stem density, canopy openness, density of understory etc.) is of key relevance (Fig. 1a), and (2) breeding birds in reedbeds and marshlands (e.g. Great Bittern, Purple Heron, Great Reed Warbler, Savi’s Warbler and Bearded Reedling) which are a prime target of conservation and for which high-resolution data on 3D habitat features of reedbeds (e.g. reed height, reed and shrub density, ground dryness etc.) have been lacking to quantify the effects of reedbed management (e.g. desiccation, mowing and reed harvesting) on population declines (Fig. 1c). We have access to the largest amount of bird data available across Europe ([www.ebcc.info](http://www.ebcc.info/)), representing presence-absence information as well as (relative) abundances of breeding birds derived from standardized observation methods. Covering most parts of Europe, the data represent bird census and monitoring data (at fixed locations), national distribution atlases (with 5×5, 10×10 or 50×50 km grid cell size resolution), and site level data (i.e. the number and breeding locations of bird species in specific areas such as nature reserves and Natura2000 sites). We will use these high-quality bird census data together with the newly quantified LiDAR-derived 3D ecosystem structures to model the distribution and abundance of these bird species with unprecedented reality. This will be achieved by developing an interactive eScience environment for object-based image analysis (OBIA) and interpretation of LiDAR point clouds (see below).

We will expose the developed eScience infrastructure to two other ongoing research projects, thus increasing the impact, generating user feed-back, and identifying bottlenecks for wider applicability. Postdoc J. Aguirre-Gutiérrez focuses on the impact of land-use change on the distribution and loss of NW-European pollinators. This includes insects such as bees, butterflies, and hoverflies. Predictive modelling is currently restricted to coarse-scale 2D habitat characterization (Aguirre-Gutiérrez et al. 2015, Aguirre-Gutiérrez et al. 2016) and new 3D-vegetation characterization (e.g. amount of hedges, habitat edges, flower strips etc.) has high potential to improve pollinator models as well as prediction of pollination services to European fruits and vegetables (Steffan-Dewenter et al. 2002, Tscharntke et al. 2012, Jha and Kremen 2013). Postdoc A. M. Dokter focuses on the locations of stop-over sites of European migratory song birds (e.g. warblers, thrushes, starlings etc.) as identified from weather radar data (Dokter et al. 2011). A major challenge is to assess the habitat preferences of these migratory birds at stopover sites because multi-scale habitat data (at patch and landscape scale) are usually lacking (Buler et al. 2007). This requires to quantify the density of trees/thickets/shrubs, forest understory structure, vertical structure of open habitats, marshland habitats etc. to assess en route requirements for these migrating land birds.

The proposed project will enable scientific breakthroughs in predicting animal populations and species distributions at much finer resolution and higher accuracy than ever has been previously possible. This will strongly push the frontiers of ecology, biogeography and conservation by providing new data and novel insights into the distribution of biodiversity and ecosystems. The availability of LiDAR-derived 3D ecosystem structures across broad spatial extents will have a major impact, maybe comparable to the influence of the WorldClim dataset (Hijmans et al. 2005) on biological and geo-ecological research (>8500 Google Scholar citations in 10+ years). Our developed methodology will be broadly applicable to other animal species and regions, and of major relevance to other fields dealing with massive amounts of LiDAR point cloud data. We are therefore convinced that this project will contribute to transform and rapidly advance current basic and applied research.

## eScience: technologies, methods, and expected impact on the research

We are witnessing changes in remote sensing (RS) from grid cell-based approaches to object-based approaches (Blaschke and Strobl 2001, Heumann 2011, Aguirre-Gutiérrez et al. 2012). Because grid-cells merge information of various objects, the object-based approach provides more accurate information and enhances quantitative analysis of traditional pixel-based approaches (Blaschke 2010, Blaschke and Strobl 2001). With the increasing density of point clouds, ever smaller objects can accurately be identified using the characteristic features of the point data that make up the object. Consequently, LiDAR point clouds and high-resolution RS imagery now allow to accurately characterize geo-vegetation objects (Aguirre-Gutiérrez et al. 2012), a key for animal biodiversity science (Davies and Asner 2014). However, handling of these massive amounts of data creates immense challenges related to data storage, management, analysis, processing, and visualization (van Oosterom et al. 2015).

The methodological and technological aim of the proposed project is to develop a workbench that supports the workflow for handling, storage, and interactive object-based image analysis (OBIA) of massive amounts of LiDAR point cloud data (Fig. 2). This includes preprocessing of data (data exploration, projecting, tiling, mosaicking), storage of LiDAR files, interactive machine learning and visualization of point data (e.g. feature selection, annotation/segmentation, classification and evaluation), scalable computing, and a PostGIS spatial database (Fig. 2). Together with other data (e.g. bird data, climate data, other remote sensing layers etc.), the LiDAR data can then be used for ecological applications, including species distribution modelling of birds and insect pollinators (Fig. 2). The handling and analysis of the LiDAR data to obtain 3D-vegetation and landscape structures at high resolution over an unprecedented spatial extent (regions, continents) requires a multi-disciplinary collaboration of ecologists and eScientists.

We already have many TeraBytes of LiDAR-data (NL, BE, AUT), we are in contact with some other countries (GB, DE), and many European countries have LiDAR data that are available for scientific research (e.g. ES, FIN, DK, SI). We will take care of the differences between data sets in terms of point cloud density and information type (e.g. full wave form, intensity, only first return, additional parallel sensors). Uniform global LiDAR data will become accessible when the GEDI sensor is installed on the International Space Station in 2018 (https://www.nasa.gov/content/goddard/new-nasa-probe-will-study-earth-s-forests-in-3-d/#.VzWjAr4T5fA). Besides LiDAR, we have access to bird distribution and abundance data, climate data, and other remote sensing layers such as Sentinel imagery (https://scihub.copernicus.eu), Landsat imagery (http://landsat.gsfc.nasa.gov), and SPOT vegetation products such as NDVI (http://www.vgt.vito.be/index.html). These will be needed for species distribution modelling. For ground truthing of LiDAR data and derived objects, we will use specific test areas in flat as well as mountainous regions (e.g. cultural landscapes in the Netherlands vs. steep slopes in the Alps) to assess the accuracy of the identification of trees, understory density, shrubs, hedges, marshland habitats etc. in different environments. We will then develop and test the workflow for supervised OBIA to capture the full variation of vegetation across Europe.

LAStools (https://rapidlasso.com/lastools/) are indispensable for efficient LiDAR processing (i.e. converting, tiling, filtering, and clipping the many TeraBytes of data). However, additional tools are needed for efficient and transparent object-based classification. We aim to combine OBIA with scalable computing in an interactive environment for data exploration, segmentation, classification and interpretation of LiDAR data. The following elements for developing the workflow are essential:

1. **Scalable storage**. We will use existing file-based LAStools for storing LiDAR data. In addition, we will develop a PostgreSQL/GIS database for storing the metadata of the LiDAR and other RS data, and for storing classified objects with their attributes and summary statistics. It should be easy for a user to add new schemas and new objects to the data base. Objects may have different spatial scales (e.g. single trees in a forest, the forest as a whole, hedges or other linear structures, reedbeds etc.). Attributes of e.g. a tree may be tree metrics such as height, crown diameter, biomass, species identity etc.. The data base with objects will be made available to scientists (ecologists, environmental scientists, meteorologists) which we expect will increase the impact of our work enormously (see deliverables below).

2. **Tools for machine learning**. Traditional tools for geospatial analyses are not yet ready for point clouds. eCognition (http://www.ecognition.com/) is a suite of commercial software for interactive OBIA (including point clouds), but capabilities are still very limited and classification algorithms are (partly) hidden and thus inappropriate for scientific innovation. The challenge in the proposed project is to make use of existing open source software such as the Point Cloud Library (Aldoma et al. 2012, http://pointclouds.org/), CloudCompare (http://www.danielgm.net/cc/), and Orfeo (https://www.orfeo-toolbox.org/) and to include machine learning; to closely monitor and make use of new developments; and to complement this by developing new software. From our previous research we have good experience with the WEKA software (Jakubowski et al. 2013, Frank et al. 2010) which covers various machine learning algorithms and data preprocessing tools. We therefore know that several existing machine learning algorithms can provide good results for pattern recognition as long as annotation, segmentation (see Box 1 for an example) and data features are optimally taken care of. The development of algorithms to calculate new features as well as feature selection have emerged as key steps. We will therefore mainly invest in tools for interactive feature selection and annotation/segmentation relevant for object classification (Anders et al. 2011).

3. **Visualization**. In the iterative process of feature selection, annotation/segmentation, and object classification and evaluation, the visualization is of utmost importance, especially when working on the improvement of methodologies. To be able to visually judge the quality of methodologies and to understand mismatches, we will adapt existing software such as Point Cloud Library (Aldoma et al. 2012, http://pointclouds.org/) and Potree (http://potree.org/wp/) for the visualization of merged objects and point clouds.

4. **Computation**. Once the models and methods for classification of objects (e.g. trees, bushes, hedges, reedbeds etc.; Fig. 2) have been developed, we aim to apply them to large areas (regions to continents). This will require to develop scalable computing solutions.

The eScience engineers will develop the proposed workbench (we envisage a combination of LAStools, Point Cloud Library, CloudCompare, Orfeo, QGIS, Potree, as well as newly developed tools) in close collaboration with the PhD student who will characterize the 3D ecosystem structures for breeding birds (see above), while the postdocs working on pollinators (Aguirre-Gutiérrez et al. 2015, Aguirre-Gutiérrez et al. 2016) and bird migration (Dokter et al. 2011, Shamoun-Baranes et al. 2014) will provide feed-back. The combination of this eScience infrastructure and expertise on LiDAR, OBIA, ecology and modelling will further strengthen our position at the cutting edge of eEcology (technology enhanced Ecology).

## Box 1: Identifying trees in a forest

LiDAR data can be used to delineate individual trees in forests (Jakubowski et al. 2013, Hu et al. 2014, Duncanson et al. 2014). In a preparatory study (BSc project), we tested an efficient methodology to segment single trees in a dense forest from LiDAR point clouds.

LiDAR returns were filtered from the point cloud, smoothed and rasterized to a 1m resolution Canopy Height Model (CHM). Locations of tree tops were determined using a local maximum filter and the minimum distance between trees. The CHM was then flipped with tree tops becoming sinks. An existing algorithm (Duncanson et al. 2014) was used (originally developed to calculate flow direction and delineation of hydrological catchments) to select cells that contribute to a particular sink. This allowed to assign cells to the tree top and thus to segment the tree crowns within the canopy. The resulting tree crown objects were stored in a data base.

Our example shows how tree crowns and tree tops can be calculated from LiDAR data (Fig. 3). Additional tree metrics could be calculated, including tree height, tree biomass and crown diameter. This example illustrates how existing methodologies can be improved (Jakubowski et al. 2013) by adapting an algorithm and taking into account the information of the LiDAR point cloud. A further improvement of the algorithm would be needed for the proposed applications (Fig. 2) to reliably identify different types of trees in a mixed forest, canopy openness etc..

## Re-use, sustainability, dissemination, and collaborations

The use of LiDAR point clouds is dramatically increasing. A generic challenge across many disciplines and applications is the storage and handling of massive amounts of data, the visualization, and the automated identification of objects (models) prior to the actual interpretation or analysis (van Oosterom et al. 2015). This approach (LiDAR/RS data - object modelling - application) is generic, whether it is about the identification of 3D-vegetation structures (Heumann 2011, Vierling et al. 2008, Jakubowski et al. 2013, Hu et al. 2014) or 3D subsurface structures from geophysical data (Fadel et al. 2015); operational flood mapping (Brown et al. 2016); detection of snow avalanches (Eckerstorfer et al. 2016) or landslides (Stumpf and Kerle 2011, Li et al. 2015); identification of illegal forest clearings or land use change (Collins and Mitchard 2015); city planning (Pang et al. 2014), or identifying buildings and their distinct sub-elements such as roofs and facades (Le et al. 2016, Vetrivel et al. 2015). Our new eScience tools will be available to other disciplines and applications and thus achieve broad impact. We will re-use the database knowledge and visualization tools developed in the past NLeSC PointCloud project (van Oosterom et al. 2015) and the gateway that we developed in EUBrazilCloudConnect (Elia et al. 2016). We also build upon existing open source software for RS, OBIA, and visualization.

Our research group is active in both the Geo- and Bio-world. We will promote the eScience approach and disseminate the results through publications in both disciplines. Since 2008 we organize one or two international PhD summer schools every year. We envisage to organize a future summer school on 'OBIA of LiDAR point clouds for ecological applications'. LiDAR and OBIA also play an important role in education at the University of Amsterdam where we contribute to the eScience training of the next generation of geo-ecologists. Macroecology and RS are important and promising research directions of our permanent staff members. A follow-up with new (international) projects is thus guaranteed and as the developed infrastructure is crucial it will be maintained after the project.

## Use of the national e-infrastructure

We have agreed with SurfSara (https://www.surf.nl/en/about-surf/subsidiaries/surfsara/) to use the National e-Infrastructure of the Netherlands (e-Infra). The project will require a substantial storage for all raw data and LiDAR files (max 0.5 PB). Since we have a very good experience with the central hosting of data at SurfSara, the PostgreSQL/GIS database of the proposed research will be hosted by e-Infra. In the beginning, we will collect LiDAR data and store these in a file-based archive. During the development phase, we will then use subsets of the LiDAR data from different countries. The vast majority of the LiDAR data will only be used when upscaling the analysis to Europe for relevant ecological applications (Fig. 2). In addition to data storage, we will need Virtual Machines in the SURFCloud for various components of the workbench. For the large-scale classification of objects, we will use the e-Infra Research Capacity Compute Service ([www.surf.nl/rccs](http://www.surf.nl/rccs)). This combines Cloud, Cluster, Grid and Hadoop computing. The best scalable computing for the classification of high resolution objects at large spatial extents has to be identified during the project.

## Workplan and time table

The suggested workplan and time table is illustrated in Fig. 4. eScience engineers will work closely together (over the first ~3 years) with the PhD student who will do the 3D ecosystem characterization for breeding birds. The role of the eScience engineers is to develop and implement the four elements mentioned above and to integrate these with existing software in an interactive workbench. The PhD will contribute to the workbench developments and generate feed-back from a user perspective. The PhD will then use the workbench to analyze the data of test areas in flat and mountainous regions and to produce the objects that are needed for the species distribution modelling in the 4th year. The associated researchers can make use of the workbench and generate feed-back.

We envisage that we need various expertise of eScience engineers. We will take advantage of the existing knowledge in the Netherlands eScience Center (NLeSC) regarding handling, storing and visualizing of LiDAR data. NLeSC knowledge and skills on machine learning and scientific visualization are essential as eScience engineers will take the lead in developing the workbench. This will be in close collaboration with the PhD student and the supervisors who will be involved in the design and will generate feed-back during the various phases in the development process. At the end of the 3rd year when OBIA is applied to large areas the PhD student will probably need some help with scalable computing. We also envisage several brainstorms with the involved eScience engineers, the PhD student, supervisors and associated researchers to design the workbench as a whole and to discuss the requirements. After three years with contributing to the methodological and technological challenges, the involvement of eScience engineers will be limited to their input to scientific publications and outreach. The PhD will then finish his/her research by using the classified objects for species distribution models. We foresee that the eScience engineers will be mainly working at NLeSC with frequent meetings (at least one per week as our institute is just across the street) with the PhD student and one of the supervisors.

## Deliverables

1. A SWOT (Strengths, Weaknesses, Opportunities, and Threats) analysis (provided as report), with evaluation of existing open source software that can be used for the workbench, both from the developer and user point of view.

2. A file-based archive with LiDAR point cloud data

3. Data base for LiDAR meta data, object models, and classified objects with their metrics, attributes and summary statistics. The data base will also include climate data, other remote sensing layers and bird data that are needed for developing species distribution models. The LiDAR objects information in the data base will be made available to the scientific community.

4. Workbench focusing on Object Based Point Cloud Analysis, tested by user(s)

5. PhD-thesis with 4-5 scientific publications focusing on 1) methodology of Object-Based Point Cloud Analysis (incl. case applications); 2) workbench design for Object-Based Point Cloud Analysis; 3) data publication(s) providing the classified objects from different LiDAR datasets, 4) the added value of 3D vegetation information for distribution modelling of ground nesting forest birds; and 5) identification of reedbeds from LiDAR data and its application to the distribution and abundance of birds in reedbeds and marshlands.

6. PhD summer school on 'OBIA of LiDAR point clouds for ecological applications'

7. Presentations at conferences and workshops and general outreach.

## Acknowledgements

We thank two anonymous referees and the assessment committee of the Netherlands eScience Center for the positive evaluation of this grant proposal.

## Funding program

Accelerating Scientific Discovery (ASDI) grant (ASDI.2016.014) from the Netherlands eScience Center (NLeSC)

Figure 1.

The vertical and horizontal distribution of plants influences habitat structure and 3D characteristics of vegetation for animals. Illustrated are examples for (a) forests, (b) agricultural and open landscapes, and (c) reedbeds and marshlands. The height, openness and density of vegetation as well as specific habitat features (e.g. tree species, hedges etc.) are key aspects of animal habitat and space use.

Figure 2.

Generic workflow for object-based image analysis (OBIA) of LiDAR point clouds and proposed ecological applications. A workbench (blue) will be developed to handle the data storage, data exploration, and interactive OBIA of the massive LiDAR point clouds. Combined with datasets of bird distributions, climate, and other remote sensing layers (orange), the LiDAR data will be applied to several ecological case studies, e.g. by using species distribution modelling of birds and insect pollinators (green).

Figure 3.

Example of identifying trees in a forest from LiDAR data. Illustrated is a small plot of poplar trees in Flevoland, The Netherlands, for which tree crowns and tree tops have been calculated.

Figure 4.

Time table for the eEcoLiDAR project (assuming a start in March 2017). The work plan covers tasks for the NLeSC engineers, the proposed PhD student, and two associated Postdoc projects.

## References

Aguirre-Gutiérrez Jesus, Seijmonsbergen Arie C., Duivenvoorden Joost F. 2012. Optimizing land cover classification accuracy for change detection, a combined pixel-based and object-based approach in a mountainous area in Mexico. Applied Geography. 34. 29. 37. http://www.sciencedirect.com/science/article/pii/S0143622811001871. https://doi.org/10.1016/j.apgeog.2011.10.010

Aguirre-Gutiérrez Jesús, Biesmeijer Jacobus C., van Loon E. Emiel, Reemer Menno, WallisDeVries Michiel F., Carvalheiro Luísa G. 2015. Susceptibility of pollinators to ongoing landscape changes depends on landscape history. Diversity and Distributions. 21. 10. 1129. 1140. http://dx.doi.org/10.1111/ddi.12350. https://doi.org/10.1111/ddi.12350

Aguirre-Gutiérrez Jesús, Kissling W. Daniel, Carvalheiro Luísa G., WallisDeVries Michiel F., Franzén Markus, Biesmeijer Jacobus C. 2016. Functional traits help to explain half-century long shifts in pollinator distributions. Scientific Reports. 6. http://dx.doi.org/10.1038/srep24451. https://doi.org/10.1038/srep24451

Aldoma A., Marton Z. C., Tombari F., Wohlkinger W., Potthast C., Zeisl B., Rusu R. B., Gedikli S., Vincze M. 2012. Tutorial: Point Cloud Library: three-dimensional object recognition and 6 DOF pose estimation. IEEE Robotics & Automation Magazine. 19. 3. 80. 91. https://doi.org/10.1109/MRA.2012.2206675

Anders Niels S., Seijmonsbergen Arie C., Bouten Willem. 2011. Segmentation optimization and stratified object-based analysis for semi-automated geomorphological mapping. Remote Sensing of Environment. 115. 12. 2976. 2985. http://www.sciencedirect.com/science/article/pii/S0034425711001799. https://doi.org/10.1016/j.rse.2011.05.007

Blaschke T. 2010. Object based image analysis for remote sensing. ISPRS Journal of Photogrammetry and Remote Sensing. 65. 1. 2. 16. http://www.sciencedirect.com/science/article/pii/S0924271609000884. https://doi.org/10.1016/j.isprsjprs.2009.06.004

Blaschke T., Strobl J. 2001. What's wrong with pixels? Some recent developments interfacing remote sensing and GIS. GIS | Zeitschrift für Geoinformationssysteme. 14. 12. 17

Brown Kyle M., Hambidge Crispin H., Brownett Jonathan M. 2016. Progress in operational flood mapping using satellite synthetic aperture radar (SAR) and airborne light detection and ranging (LiDAR) data. Progress in Physical Geography. 40. 2. 196. 214. http://search.ebscohost.com/login.aspx?direct=true&db=aph&AN=114452088&site=ehost-live. https://doi.org/10.1177/0309133316633570

Buler Jeffrey J., Moore Frank R., Woltmann Stefan. 2007. A multi-scale examination of stopover habitat use by birds. Ecology. 88. 7. 1789. 1802. http://dx.doi.org/10.1890/06-1871.1. https://doi.org/10.1890/06-1871.1

Cardinale Bradley J., Duffy J. Emmett, Gonzalez Andrew, Hooper David U., Perrings Charles, Venail Patrick, Narwani Anita, Mace Georgina M., Tilman David, Wardle David A., Kinzig Ann P., Daily Gretchen C., Loreau Michel, Grace James B., Larigauderie Anne, Srivastava Diane S., Naeem Shahid. 2012. Biodiversity loss and its impact on humanity. Nature. 486. 7401. 59. 67. http://dx.doi.org/10.1038/nature11148

Ceballos Gerardo, Ehrlich Paul R., Barnosky Anthony D., García Andrés, Pringle Robert M., Palmer Todd M. 2015. Accelerated modern human–induced species losses: Entering the sixth mass extinction. Science Advances. 1. 5. http://advances.sciencemag.org/advances/1/5/e1400253.full.pdf. https://doi.org/10.1126/sciadv.1400253

Cody M. L. 1985. Habitat selection in birds. Academic Press. Orlando

Collins M. B., Mitchard E. T. A. 2015. Integrated radar and lidar analysis reveals extensive loss of remaining intact forest on Sumatra 2007–2010. Biogeosciences. 12. 22. 6637. 6653. http://www.biogeosciences.net/12/6637/2015/. https://doi.org/10.5194/bg-12-6637-2015

Dantas de Paula Mateus, Groeneveld Jürgen, Huth Andreas. 2016. The extent of edge effects in fragmented landscapes: Insights from satellite measurements of tree cover. Ecological Indicators. 69. 196. 204. http://www.sciencedirect.com/science/article/pii/S1470160X16301923. https://doi.org/10.1016/j.ecolind.2016.04.018

Davies Andrew B., Asner Gregory P. 2014. Advances in animal ecology from 3D-LiDAR ecosystem mapping. Trends in Ecology & Evolution. 29. 12. 681. 691. http://dx.doi.org/10.1016/j.tree.2014.10.005. https://doi.org/10.1016/j.tree.2014.10.005

Dokter Adriaan M., Liechti Felix, Stark Herbert, Delobbe Laurent, Tabary Pierre, Holleman Iwan. 2011. Bird migration flight altitudes studied by a network of operational weather radars. Journal of The Royal Society Interface. 8. 54. 30. 43. http://rsif.royalsocietypublishing.org/content/royinterface/8/54/30.full.pdf. https://doi.org/10.1098/rsif.2010.0116

Duncanson L. I., Cook B. D., Hurtt G. C., Dubayah R. O. 2014. An efficient, multi-layered crown delineation algorithm for mapping individual tree structure across multiple ecosystems. Remote Sensing of Environment. 154. 378. 386. http://www.sciencedirect.com/science/article/pii/S0034425714000984. https://doi.org/10.1016/j.rse.2013.07.044

Eckerstorfer Markus, Bühler Yves, Frauenfelder Regula, Malnes Eirik. 2016. Remote sensing of snow avalanches: Recent advances, potential, and limitations. Cold Regions Science and Technology. 121. 126. 140. http://www.sciencedirect.com/science/article/pii/S0165232X15002591. https://doi.org/10.1016/j.coldregions.2015.11.001

Elia D., Nuzzo A., Nassise P., Fiore S., Blanquer I., Brasiliero F. V., Rufino I. A.A., Seijmonsbergen A. C., Anders N. S., Galvao C. O., Cunha J. E. de B.L., Sousa-Baena M. S., Canhos V. P., Aloiso G. 2016. A science gateway for biodiversity and climate change research. 8th International Workshop on Science Gateways (IWSG 2016)

Elith J., Leathwick J. R. 2009. Species distribution models: ecological explanation and prediction across space and time. Annual Review of Ecology Evolution and Systematics. 40. 677. 697. <Go to ISI>://000272455700032. https://doi.org/10.1146/annurev.ecolsys.110308.120159

Eskildsen Anne, le Roux Peter C., Heikkinen Risto K., Høye Toke T., Kissling W. Daniel, Pöyry Juha, Wisz Mary S., Luoto Miska. 2013. Testing species distribution models across space and time: high latitude butterflies and recent warming. Global Ecology and Biogeography. 22. 12. 1293. 1303. http://dx.doi.org/10.1111/geb.12078. https://doi.org/10.1111/geb.12078

Fadel I., van der Meijde M., Kerle N., Lauritsen N. 2015. 3D object-oriented image analysis in 3D geophysical modelling: Analysing the central part of the East African Rift System. International Journal of Applied Earth Observation and Geoinformation. 35, Part A. 44. 53. http://www.sciencedirect.com/science/article/pii/S0303243413001517. https://doi.org/10.1016/j.jag.2013.11.004

Frank E., Hall M., Holmes G., Kirkby R., Pfahringer B., Witten I. H., Trigg L. 2010. Weka — A machine learning workbench for data mining. Maimon O., Rokach L. Data mining and knowledge discovery handbook. Springer. New York, NY, USA

Fuller R. J. 2012. Birds and habitat. Cambridge University Press. Cambridge

Goetz Scott J., Steinberg Daniel, Betts Matthew G., Holmes Richard T., Doran Patrick J., Dubayah Ralph, Hofton Michelle. 2010. Lidar remote sensing variables predict breeding habitat of a Neotropical migrant bird. Ecology. 91. 6. 1569. 1576. http://dx.doi.org/10.1890/09-1670.1. https://doi.org/10.1890/09-1670.1

Heumann Benjamin W. 2011. Satellite remote sensing of mangrove forests: Recent advances and future opportunities. Progress in Physical Geography. 35. 1. 87. 108. http://ppg.sagepub.com/content/35/1/87.abstract. https://doi.org/10.1177/0309133310385371

Hijmans R. J., Cameron S. E., Parra J. L., Jones P. G., Jarvis A. 2005. Very high resolution interpolated climate surfaces for global land areas. International Journal of Climatology. 25. 15. 1965. 1978. <Go to ISI>://000234519700002. https://doi.org/10.1002/joc.1276

Hoekstra Jonathan M., Boucher Timothy M., Ricketts Taylor H., Roberts Carter. 2005. Confronting a biome crisis: global disparities of habitat loss and protection. Ecology Letters. 8. 1. 23. 29. http://dx.doi.org/10.1111/j.1461-0248.2004.00686.x. https://doi.org/10.1111/j.1461-0248.2004.00686.x

Hu Baoxin, Li Jili, Jing Linhai, Judah Aaron. 2014. Improving the efficiency and accuracy of individual tree crown delineation from high-density LiDAR data. International Journal of Applied Earth Observation and Geoinformation. 26. 145. 155. http://www.sciencedirect.com/science/article/pii/S0303243413000755. https://doi.org/10.1016/j.jag.2013.06.003

Jakubowski Marek, Li Wenkai, Guo Qinghua, Kelly Maggi. 2013. Delineating individual trees from Lidar data: A comparison of vector- and raster-based segmentation approaches. Remote Sensing. 5. 9. http://www.mdpi.com/2072-4292/5/9/4163

Jha Shalene, Kremen Claire. 2013. Resource diversity and landscape-level homogeneity drive native bee foraging. Proceedings of the National Academy of Sciences. 110. 2. 555. 558. http://www.pnas.org/content/110/2/555.abstract. https://doi.org/10.1073/pnas.1208682110

Kissling W. D., Field R., Böhning-Gaese K. 2008. Spatial patterns of woody plant and bird diversity: functional relationships or environmental effects?. Global Ecology and Biogeography. 17. 3. 327. 339. <Go to ISI>://000254948700003. https://doi.org/10.1111/j.1466-8238.2007.00379.x

Kissling W. D., Sekercioglu Cagan H., Jetz Walter. 2012. Bird dietary guild richness across latitudes, environments and biogeographic regions. Global Ecology and Biogeography. 21. 3. 328. 340. http://dx.doi.org/10.1111/j.1466-8238.2011.00679.x. https://doi.org/10.1111/j.1466-8238.2011.00679.x

Kissling W. Daniel, Hardisty Alex, García Enrique Alonso, Santamaria Monica, De Leo Francesca, Pesole Graziano, Freyhof Jörg, Manset David, Wissel Silvia, Konijn Jacco, Los Wouter. 2015. Towards global interoperability for supporting biodiversity research on essential biodiversity variables (EBVs). Biodiversity. 16. http://www.tandfonline.com/doi/abs/10.1080/14888386.2015.1068709. https://doi.org/10.1080/14888386.2015.1068709

Kristan III William B. 2006. Sources and expectations for hierarchical structure in bird-habitat associations. The Condor. 108. 1. 5. 12. http://www.aoucospubs.org/doi/abs/10.1650/0010-5422%282006%29108%5B0005%3ASAEFHS%5D2.0.CO%3B2. https://doi.org/10.1650/0010-5422(2006)108[0005:SAEFHS]2.0.CO;2

Lausch A., Bannehr L., Beckmann M., Boehm C., Feilhauer H., Hacker J. M., Heurich M., Jung A., Klenke R., Neumann C., Pause M., Rocchini D., Schaepman M. E., Schmidtlein S., Schulz K., Selsam P., Settele J., Skidmore A. K., Cord A. F. 2016. Linking Earth Observation and taxonomic, structural and functional biodiversity: Local to ecosystem perspectives. Ecological Indicators. 70. 317. 339. http://www.sciencedirect.com/science/article/pii/S1470160X16303223. https://doi.org/10.1016/j.ecolind.2016.06.022

Lesak Adrian A., Radeloff Volker C., Hawbaker Todd J., Pidgeon Anna M., Gobakken Terje, Contrucci Kirk. 2011. Modeling forest songbird species richness using LiDAR-derived measures of forest structure. Remote Sensing of Environment. 115. 11. 2823. 2835. http://www.sciencedirect.com/science/article/pii/S0034425711001271. https://doi.org/10.1016/j.rse.2011.01.025

Le Tuan, Kholdi Danial, Xie Hongjie, Dong Bing, Vega Rolando. 2016. LiDAR-based solar mapping for distributed solar plant design and grid integration in San Antonio, Texas. Remote Sensing. 8. 3. http://www.mdpi.com/2072-4292/8/3/247. https://doi.org/10.3390/rs8030247

Lim Kevin, Treitz Paul, Wulder Michael, St-Onge Benoît, Flood Martin. 2003. LiDAR remote sensing of forest structure. Progress in Physical Geography. 27. 1. 88. 106. http://ppg.sagepub.com/content/27/1/88.abstract. https://doi.org/10.1191/0309133303pp360ra

Li Xianju, Cheng Xinwen, Chen Weitao, Chen Gang, Liu Shengwei. 2015. Identification of forested landslides using LiDar data, object-based image analysis, and machine learning algorithms. Remote Sensing. 7. 8. 9705. 9726. http://www.mdpi.com/2072-4292/7/8/9705. https://doi.org/10.3390/rs70809705

MacArthur R., MacArthur J. W. 1961. On bird species diversity. Ecology. 42. 3. 594. 598. <Go to ISI>://A19610906900021

Newbold Tim, Hudson Lawrence N., Hill Samantha L. L., Contu Sara, Lysenko Igor, Senior Rebecca A., Borger Luca, Bennett Dominic J., Choimes Argyrios, Collen Ben, Day Julie, De Palma Adriana, Diaz Sandra, Echeverria-Londono Susy, Edgar Melanie J., Feldman Anat, Garon Morgan, Harrison Michelle L. K., Alhusseini Tamera, Ingram Daniel J., Itescu Yuval, Kattge Jens, Kemp Victoria, Kirkpatrick Lucinda, Kleyer Michael, Correia David Laginha Pinto, Martin Callum D., Meiri Shai, Novosolov Maria, Pan Yuan, Phillips Helen R. P., Purves Drew W., Robinson Alexandra, Simpson Jake, Tuck Sean L., Weiher Evan, White Hannah J., Ewers Robert M., Mace Georgina M., Scharlemann Jorn P. W., Purvis Andy. 2015. Global effects of land use on local terrestrial biodiversity. Nature. 520. 7545. 45. 50. http://dx.doi.org/10.1038/nature14324. https://doi.org/10.1038/nature14324

Pang Shiyan, Hu Xiangyun, Wang Zizheng, Lu Yihui. 2014. Object-based analysis of airborne LiDAR data for building change detection. Remote Sensing. 6. 11. 10733. 10749. http://www.mdpi.com/2072-4292/6/11/10733. https://doi.org/10.3390/rs61110733

Pereira H. M., Ferrier S., Walters M., Geller G. N., Jongman R. H. G., Scholes R. J., Bruford M. W., Brummitt N., Butchart S. H. M., Cardoso A. C., Coops N. C., Dulloo E., Faith D. P., Freyhof J., Gregory R. D., Heip C., Höft R., Hurtt G., Jetz W., Karp D. S., McGeoch M. A., Obura D., Onoda Y., Pettorelli N., Reyers B., Sayre R., Scharlemann J. P. W., Stuart S. N., Turak E., Walpole M., Wegmann M. 2013. Essential Biodiversity Variables. Science. 339. 6117. 277. 278. http://www.sciencemag.org/content/339/6117/277.short. https://doi.org/10.1126/science.1229931

Shamoun-Baranes Judy, Alves Jose, Bauer Silke, Dokter Adriaan, Huppop Ommo, Koistinen Jarmo, Leijnse Hidde, Liechti Felix, van Gasteren Hans, Chapman Jason. 2014. Continental-scale radar monitoring of the aerial movements of animals. Movement Ecology. 2. 1. http://www.movementecologyjournal.com/content/2/1/9. https://doi.org/10.1186/2051-3933-2-9

Skidmore Andrew K., Pettorelli Nathalie, Coops Nicholas C., Geller Gary N., Hansen Matthew, Lucas Richard, Mücher Caspar A., O'Connor Brian, Paganini Marc, Pereira Henrique Miguel, Schaepman Michael E., Turner Woody, Wang Tiejun, Wegmann Martin. 2015. Agree on biodiversity metrics to track from space. Nature. 523. 403. 405

Steffan-Dewenter I., Munzenberg U., Burger C., Thies C., Tscharntke T. 2002. Scale-dependent effects of landscape context on three pollinator guilds. Ecology. 83. 5. 1421. 1432. <Go to ISI>://WOS:000175131300023. https://doi.org/10.2307/3071954

Stumpf André, Kerle Norman. 2011. Object-oriented mapping of landslides using Random Forests. Remote Sensing of Environment. 115. 10. 2564. 2577. http://www.sciencedirect.com/science/article/pii/S0034425711001969. https://doi.org/10.1016/j.rse.2011.05.013

Tscharntke Teja, Tylianakis Jason M., Rand Tatyana A., Didham Raphael K., Fahrig Lenore, Batáry Péter, Bengtsson Janne, Clough Yann, Crist Thomas O., Dormann Carsten F., Ewers Robert M., Fründ Jochen, Holt Robert D., Holzschuh Andrea, Klein Alexandra M., Kleijn David, Kremen Claire, Landis Doug A., Laurance William, Lindenmayer David, Scherber Christoph, Sodhi Navjot, Steffan-Dewenter Ingolf, Thies Carsten, van der Putten Wim H., Westphal Catrin. 2012. Landscape moderation of biodiversity patterns and processes - eight hypotheses. Biological Reviews. 87. 3. 661. 685. http://dx.doi.org/10.1111/j.1469-185X.2011.00216.x. https://doi.org/10.1111/j.1469-185X.2011.00216.x

van Oosterom Peter, Martinez-Rubi Oscar, Ivanova Milena, Horhammer Mike, Geringer Daniel, Ravada Siva, Tijssen Theo, Kodde Martin, Gonçalves Romulo. 2015. Massive point cloud data management: design, implementation and execution of a point cloud benchmark. Computers & Graphics. 49. 92. 125. http://www.sciencedirect.com/science/article/pii/S0097849315000084. https://doi.org/10.1016/j.cag.2015.01.007

Vetrivel A., Gerke M., Kerle N., Vosselman G. 2015. Segmentation of UAV-based images incorporating 3D point cloud information. Int. Arch. Photogramm. Remote Sens. Spatial Inf. Sci. XL-3/W2. 261. 268. http://www.int-arch-photogramm-remote-sens-spatial-inf-sci.net/XL-3-W2/261/2015/. https://doi.org/10.5194/isprsarchives-XL-3-W2-261-2015

Vierling Kerri T., Vierling Lee A., Gould William A., Martinuzzi Sebastian, Clawges Rick M. 2008. Lidar: shedding new light on habitat characterization and modeling. Frontiers in Ecology and the Environment. 6. 2. 90. 98. http://dx.doi.org/10.1890/070001. https://doi.org/10.1890/070001

Wiens J. A. 1989. The ecology of bird communities. Part 1. Cambridge University Press. Cambridge

Wulder Michael A., Hall Ronald J., Coops Nicholas C., Franklin Steven E. 2004. High spatial resolution remotely sensed data for ecosystem characterization. Bioscience. 54. 6. 511. 521. http://bioscience.oxfordjournals.org/content/54/6/511.abstract. https://doi.org/10.1641/0006-3568(2004)054[0511:hsrrsd]2.0.co;2

Wulder Michael A., White Joanne C., Nelson Ross F., Næsset Erik, Ørka Hans Ole, Coops Nicholas C., Hilker Thomas, Bater Christopher W., Gobakken Terje. 2012. Lidar sampling for large-area forest characterization: A review. Remote Sensing of Environment. 121. 196. 209. http://www.sciencedirect.com/science/article/pii/S0034425712000855. https://doi.org/10.1016/j.rse.2012.02.001

Zellweger Florian, Braunisch Veronika, Baltensweiler Andri, Bollmann Kurt. 2013. Remotely sensed forest structural complexity predicts multi species occurrence at the landscape scale. Forest Ecology and Management. 307. 303. 312. http://www.sciencedirect.com/science/article/pii/S0378112713004659. https://doi.org/10.1016/j.foreco.2013.07.023

Zellweger Florian, Baltensweiler Andri, Ginzler Christian, Roth Tobias, Braunisch Veronika, Bugmann Harald, Bollmann Kurt. 2016. Environmental predictors of species richness in forest landscapes: abiotic factors versus vegetation structure. Journal of Biogeography. http://dx.doi.org/10.1111/jbi.12696. https://doi.org/10.1111/jbi.12696

Zhang Jian, Kissling W. Daniel, He Fangliang. 2013. Local forest structure, climate and human disturbance determine regional distribution of boreal bird species richness in Alberta, Canada. Journal of Biogeography. 40. 6. 1131. 1142. http://dx.doi.org/10.1111/jbi.12063. https://doi.org/10.1111/jbi.12063
