from math import exp, floor, log
import numpy

from soil3ds.test.test_init_soil import init_sol_test
from soil3ds import soil_wrapper as soil_interface

def expansion(t, a, delai):
    "croissance sigmoidale"
    return 1/(1+exp(-a*(t-delai)))

def CarbonAssimilation(RelativeLightAbs, IncomingLight, RUE, FTSW, Soilsurf=1.):
    """Modélise une assimilation du carbone en fonction du par

    Parameters
    ----------
    RelativeLightAbs : float
        _description_
    IncomingLight : float
        entrée météo du rayonnement
    RUE : float
        _description_
    FTSW : float
        _description_
    Soilsurf : float, optional
        surface du sol en m^2, by default 1.

    Returns
    -------
    float
        dMS
    """    
    epsi = RelativeLightAbs/Soilsurf
    water_stress = FTSW #effet stress hydrique proportionnel a FTSW
    carbon = epsi * IncomingLight * RUE * water_stress
    return carbon

def update_light_lstring(lstring, aggregated_out):
    """_summary_

    Parameters
    ----------
    lstring : lstring
        _description_
    aggregated_out : dict
        résultats ensoleillement intégrés par organe

    Returns
    -------
    list
        lstring : mise à jour de la lstring
        cumlight : cumul du par sur le couvert
        ls_par : par pondérée par surface des organe
    """    
    Dico_Par = aggregated_out['default_band']['Ei']
    cumlight = 0.
    ls_par = []
    for mod in range(len(lstring)):
        if lstring[mod].name == 'A' or lstring[mod].name == 'B':
            calcpar = Dico_Par[mod]
            lstring[mod][1] = calcpar
        elif lstring[mod].name == 'Leaf':
            par_i = Dico_Par[mod] * aggregated_out['default_band']['area'][ mod]  # a ponderer par surface, eventuellement selon id plante
            cumlight += par_i
            ls_par.append(par_i)
    
    return lstring, cumlight, ls_par

def growth_roots(roots_length, uptakeN, carbon):
    """Modélise une croissance des racines (expérimental)

    Parameters
    ----------
    roots_length : float
        longueur des racines sur une plantes (en m)
    uptakeN : float
        uptake d'azote en kg
    carbon : float
        dMS

    Returns
    -------
    float
        Nouvelle longueur de racines
    """    
    if carbon > 0 :
        growth = max(0.1, uptakeN ** carbon)
        growth = -log(growth) * 100.
    else:
        growth = 1e-5
    if carbon > 2.5*1e-5:
        growth = 1e-5
    return roots_length + roots_length * growth

def roots_length_repartition(roots_length, carto, soil_dx, soil_origin, soil_dimensions):
    """Répartition des racines dans la grille de voxels du sol
    répartition homogène en profondeur

    Parameters
    ----------
    roots_length : float
        longueur des racines en m
    carto : list
        position de la plante [[x, y, z]]
    soil_dx : float
        taille en x d'un voxel du sol (on considère les voxels carré en xy)
    soil_origin : list
        [x0, y0, z0]
    soil_dimensions : list
        nombre de voxels sur chaque axe [nz, nx, ny]

    Returns
    -------
    list
        tableau de 4 dimensions [id_plante, ix, iy, iz] des longueurs de racines
    """    
    roots_length_per_voxel = numpy.zeros(soil_dimensions)
    roots_length_per_voxel_per_plant = []
    for p in carto:
        ix = floor((p[0] - soil_origin[0]) / soil_dx)
        iy = floor((p[1] - soil_origin[1]) / soil_dx)
        roots_length_per_voxel[:, ix, iy] = roots_length / soil_dimensions[0]
        roots_length_per_voxel_per_plant.append(roots_length_per_voxel)
    return roots_length_per_voxel_per_plant

def initiatisation_soil_default(pattern8, dz, size, stateEV, properties_3ds):
    #properties_3ds = ['asw_t', 'tsw_t', 'Corg', 'Norg', 'm_NO3', 'm_NH4', 'm_soil_vol', 'm_Tsol', 'm_DA', 'ftsw_t']
    # signification des properties:
    # asw_t : quantite d'eau libre pour plante dans le voxel au temps t (mm)
    # tsw_t : quantite d'eau totale dans le voxel au temps t (mm)
    # ftsw_t : fraction d'eau ranspirable = asw_t/tsw_t
    # m_soil_vol : volume des voxels (m3)
    # m_DA : densite apparente du sol par voxel (g.cm-3)
    # m_Tsol: Temperature sol (degreC - entree actuellement forcee par meteo)
    # Corg: (kg C dans le voxel)
    # Norg: (kg N dans le voxel)
    # m_NH4: (kg N NH4 dans le voxel)
    # m_NO3: (kg N NO3 dans le voxel)

    ## creation d'un objet sol 3ds par defaut (S)
    S = init_sol_test(pattern8, dz, size)
    #print('surfsol',S.surfsolref) #-> c'est bien un objet sol de la bonne surface qui est cree 

    #instancie un odjet sol 3D d'interface vide (intsoil) a partir de l'objet sol 3ds (S)
    size_ = S.size[1:]+S.size[0:1] #passe z,x,y en xyz
    dxyz_ = [S.dxyz[0][0], S.dxyz[1][0], S.dxyz[2][0]]
    origin = S.origin
    # Par default, les dimensions sont exprimes en m. Il faut les convertir en cm pour le wrapper Soil3D
    dxyz_ = [v*100 for v in dxyz_] # conversion cm
    origin = [v*100 for v in origin] # conversion cm


    # creation wrapper sol
    intsoil = soil_interface.Soil3D_wrapper(origin, size_, dxyz_)
    intsoil.add_property('root_length',0)

    #mise a jour de ttes les proprietes de sol dans l'interface sol
    intsoil.set_3ds_properties(S, properties_3ds)
    #print origin, size_, dxyz_

    return S, stateEV, intsoil
    