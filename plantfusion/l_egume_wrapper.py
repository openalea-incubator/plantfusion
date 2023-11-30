import os
from copy import deepcopy

import numpy
import pandas
import scipy

from openalea.lpy import *

import legume.IOxls as IOxls
import legume.IOtable as IOtable
import legume.run_legume_usm as runl
import legume.ShootMorpho as sh
import legume.daily_loop as loop
from legume.initialisation import init_plant_residues_fromParamP

import riri5.RIRI5 as riri

from plantfusion.utils import create_child_folder
from plantfusion.light_facade import Light
from plantfusion.environment_tool import Environment


class L_egume_facade(object):
    """Wrapper for l-egume model

    construction creates the lsystems



    """

    def __init__(
        self,
        name="legume",
        in_folder="",
        out_folder=None,
        nameconfigfile="liste_usms_exemple.xls",
        ongletconfigfile="exemple",
        IDusm=None,
        planter=None,
    ) -> None:
        if out_folder is not None:
            try:
                os.mkdir(os.path.normpath(out_folder))
                print("Directory ", out_folder, " Created ")
            except FileExistsError:
                pass

            # output folder for l-egume
            out_folder = os.path.normpath(out_folder)
            self.out_folder = os.path.join(out_folder, "legume")
            try:
                os.mkdir(os.path.normpath(self.out_folder))
                print("Directory ", self.out_folder, " Created ")
            except FileExistsError:
                pass
            create_child_folder(self.out_folder, "brut")
            create_child_folder(self.out_folder, "graphs")

        else:
            self.out_folder = ""
        
        # read l-egume configuration files
        mn_path = os.path.join(in_folder, nameconfigfile)
        usms = IOxls.xlrd.open_workbook(mn_path)
        ls_usms = IOtable.conv_dataframe(IOxls.get_xls_col(usms.sheet_by_name(ongletconfigfile)))

        # create list of lsystems from config file
        self.lsystems = {}
        self.idsimu = []
        if IDusm is None:
            for i in range(len(ls_usms["ID_usm"])):
                    if int(ls_usms["torun"][i]) == 1:
                        self.__load_lsystem(nameconfigfile, in_folder, ongletconfigfile, i, os.path.join(self.out_folder, "brut"), planter, planter_index)
        else:
            if isinstance(IDusm, list):
                for i in IDusm:
                    self.__load_lsystem(nameconfigfile, in_folder, ongletconfigfile, ls_usms["ID_usm"].index(i), os.path.join(self.out_folder, "brut"), planter, planter_index)
            else:
                self.__load_lsystem(nameconfigfile, in_folder, ongletconfigfile, ls_usms["ID_usm"].index(IDusm), os.path.join(self.out_folder, "brut"), planter, planter_index)

        option_externalcoupling = 1
        option_Nuptake = 0

        self.lstrings = []
        for n in self.idsimu:
            self.lstrings.append(self.lsystems[n].axiom)
            self.lsystems[n].opt_external_coupling = option_externalcoupling
            self.lsystems[n].opt_Nuptake = option_Nuptake

        # in order to compute tag_inputs_loop
        for i, n in enumerate(self.idsimu):
            lstrings_temp = self.lsystems[n].derive(self.lstrings[i], 0, 1)

        self.number_of_species_per_usm = [len(self.lsystems[n].tag_loop_inputs[17]) for n in self.idsimu]

        if sum(self.number_of_species_per_usm) > len(self.idsimu):
            print("--> Please use one plant specy per usm.")
            raise

        self.res_trans = None
        self.res_abs_i = None
        self.invar = None
        self.domain = None

    def __load_lsystem(self, nameconfigfile, in_folder, ongletconfigfile, i, path_OUT, planter=None, planter_index=None):
        if planter is not None:
            mylsys = lsystemInputOutput_usm_with_planter(
                        nameconfigfile,
                        foldin=in_folder,
                        ongletBatch=ongletconfigfile,
                        i=i,
                        path_OUT=path_OUT,
                        planter=planter,
                        planter_index=planter_index
                    )
        else:
            mylsys = runl.lsystemInputOutput_usm(
                nameconfigfile,
                foldin=in_folder,
                ongletBatch=ongletconfigfile,
                i=i,
                path_OUT=path_OUT,
            )
        name = list(mylsys)[0]
        self.idsimu.append(name)
        self.lsystems[name] = mylsys[name]

    def derive(self, t):
        for i, n in enumerate(self.idsimu):
            self.lstrings[i] = self.lsystems[n].derive(self.lstrings[i], t, 1)
        self.invar = [self.lsystems[n].tag_loop_inputs[0] for n in self.idsimu]

    def light_inputs(self, lightmodel) -> list:
        if lightmodel == "caribu":
            return [self.lsystems[n].sceneInterpretation(self.lstrings[i]) for i, n in enumerate(self.idsimu)]
        elif lightmodel == "ratp" or lightmodel == "riri5":
            leaf_area = self.concatene_leaf_area()
            angle_distrib = self.concatene_angle_distributions()
            legume_grid = {"LA": leaf_area, "distrib": angle_distrib}
            return [legume_grid]
        else:
            print("Unknown light model")
            raise

    def light_results(self, energy, lighting: Light) -> None:
        if lighting.lightmodel == "caribu":
            self.res_trans = self.transfer_caribu_legume(
                energy=energy,
                id=lighting.l_egume_index,
                nb0=lighting.nb_empty_z_layers(),
                elements_outputs=lighting.results_organs(),
                sensors_outputs=lighting.results_sensors(),
            )

        elif lighting.lightmodel == "ratp":
            self.res_abs_i, self.res_trans = self.transfer_ratp_legume(
                energy, lighting.results_voxels(), lighting.nb_empty_z_layers()
            )

        elif lighting.lightmodel == "riri5":
            self.res_trans = lighting.res_trans()
            self.res_abs_i = lighting.res_abs_i()

        self.compute_plants_interception(
            lighting.results_organs(), energy, lighting.soil_energy(), lighting.l_egume_index
        )
        self.compute_potential_plant_growth()

    def soil_inputs(self) -> list:
        list_ls_roots = [self.lsystems[n].tag_loop_inputs[21] for n in self.idsimu]
        list_ParamP = [self.lsystems[n].tag_loop_inputs[3] for n in self.idsimu]
        par_SN = self.lsystems[self.idsimu[0]].tag_loop_inputs[19]
        meteo_j = self.lsystems[self.idsimu[0]].tag_loop_inputs[6]
        mng_j = self.lsystems[self.idsimu[0]].tag_loop_inputs[7]
        opt_residu = self.lsystems[self.idsimu[0]].tag_loop_inputs[-2]
        opt_Nuptake = max([self.lsystems[n].opt_Nuptake for n in self.idsimu])
        soil = self.lsystems[self.idsimu[0]].tag_loop_inputs[18]

        list_ls_N = []
        for k in range(len(self.idsimu)):
            if opt_Nuptake == 0 or opt_Nuptake == 2:  # 'STICS' or 'old':
                list_ls_N.append(self.demandeN[k])

            elif opt_Nuptake == 1:  # 'LocalTransporter':
                list_ls_N.append(numpy.array(self.invar[k]["NNI"]))  # ls_NNIStress['NTreshExpSurf']

        # gere l'aggregation des entrees par plante
        self.nb_plant_per_specy = [len(self.epsi[0].tolist())]
        ls_epsi = self.epsi[0].tolist()
        ls_N = list_ls_N[0].tolist()
        ls_roots = list_ls_roots[0]
        ParamP = list_ParamP[0]
        for k in range(1, len(self.idsimu)):
            self.nb_plant_per_specy.append(len(self.epsi[k].tolist()))
            ls_epsi = ls_epsi + self.epsi[k].tolist()
            ls_N = ls_N + list_ls_N[k].tolist()
            ls_roots = ls_roots + list_ls_roots[k]
            ParamP = ParamP + list_ParamP[k]

        # step soil en commun
        inputs_soil = [
            soil,
            par_SN,
            meteo_j,
            mng_j,
            ParamP,
            ls_epsi,
            ls_roots,
            ls_N,
            opt_residu,
            opt_Nuptake,
        ]

        return inputs_soil

    def soil_results(self, inputs_soil, results_soil) -> None:
        nb_plants = int(sum(self.nb_plant_per_specy[:]))

        (
            soil,
            par_SN,
            meteo_j,
            mng_j,
            ParamP,
            ls_epsi,
            ls_roots,
            ls_N,
            opt_residu,
            opt_Nuptake,
        ) = inputs_soil
        soil, stateEV, ls_ftsw, ls_transp, ls_Act_Nuptake_plt, temps_sol = results_soil

        ParamP = ParamP[:nb_plants]
        ls_epsi = ls_epsi[:nb_plants]
        ls_roots = ls_roots[:nb_plants]
        ls_N = ls_N[:nb_plants]
        ls_ftsw = ls_ftsw[:nb_plants]
        ls_transp = ls_transp[:nb_plants]
        ls_Act_Nuptake_plt_leg = ls_Act_Nuptake_plt[:nb_plants]

        self.inputs_soil_legume = [
            soil,
            par_SN,
            meteo_j,
            mng_j,
            ParamP,
            ls_epsi,
            ls_roots,
            ls_N,
            opt_residu,
            opt_Nuptake,
        ]
        self.results_soil_legume = [soil, stateEV, ls_ftsw, ls_transp, ls_Act_Nuptake_plt_leg, temps_sol]

    def compute_plants_interception(self, organs_results=[], energy=1, pari_soil_in=-1, id=None):
        surf_refVOX = self.lsystems[self.idsimu[0]].tag_loop_inputs[15]
        list_dicFeuilBilanR = [self.lsystems[n].tag_loop_inputs[14] for n in self.idsimu]

        if self.domain is None:
            surfsolref = self.lsystems[self.idsimu[0]].tag_loop_inputs[12]
        else:
            surfsolref = (self.domain[1][0] - self.domain[0][0]) * (self.domain[1][1] - self.domain[0][1])

        leaf_area = self.concatene_leaf_area()

        # R_FR voxel (calcul de zeta)
        tag_light_inputs2 = [self.res_trans / (energy * surf_refVOX)]  # input tag
        self.rfr = riri.rfr_calc_relatif(*tag_light_inputs2)

        # interception au sol
        if pari_soil_in < 0:
            transmi_sol = numpy.sum(self.res_trans[-1][:][:]) / (energy * surfsolref)
            pari_soil = max(1.0 - transmi_sol, 1e-15)
        else:
            pari_soil = 1 - pari_soil_in

        # calul des interception feuille et ls_epsi plante
        # res_abs_i existe donc on est passé soit par ratp soit riri
        if self.res_abs_i is not None:
            pari_canopy = 0
            for k in range(len(self.idsimu)):
                # si on a pas calculé l'interception par plante dans invar
                if numpy.sum(self.invar[k]["parip"]) == 0.0:
                    # filtered_data = organs_results[(organs_results.VegetationType.isin(id))]
                    list_dicFeuilBilanR[k] = sh.calc_paraF(
                        list_dicFeuilBilanR[k], leaf_area, self.res_abs_i, force_id_grid=k
                    )
                    sh.calc_para_Plt(self.invar[k], list_dicFeuilBilanR[k])
                pari_canopy += numpy.sum(self.invar[k]["parip"])

        # res_abs_i n'existe pas donc on est passé par caribu
        else:
            species_not_legume = [i for i in organs_results["VegetationType"].unique() if i not in id]
            filtered_data = organs_results[(organs_results.VegetationType.isin(species_not_legume))]
            pari_canopy = numpy.sum([numpy.sum(self.invar[k]["parip"]) for k in range(len(self.idsimu))])
            if not filtered_data.empty:
                pari_canopy += numpy.sum(filtered_data["par Ei"]) * energy

        self.epsi = []
        for k in range(len(self.idsimu)):
            ratio_pari_plante = self.invar[k]["parip"] / (pari_canopy + 10e-15)
            epsi_per_plant = pari_soil * ratio_pari_plante
            self.epsi.append(epsi_per_plant)
            # if numpy.sum(epsi_per_plant) > 1e-17 :
            #     self.epsi.append(epsi_per_plant)
            # else:
            #     self.epsi.append(numpy.array([1e-16] * len(self.invar[k]["parip"])))

            print(self.idsimu[k], "epsi = ", sum(self.epsi[-1]))

    def compute_potential_plant_growth(self):
        list_outvar = [self.lsystems[n].tag_loop_inputs[1] for n in self.idsimu]
        list_ParamP = [self.lsystems[n].tag_loop_inputs[3] for n in self.idsimu]
        meteo_j = self.lsystems[self.idsimu[0]].tag_loop_inputs[6]
        mng_j = self.lsystems[self.idsimu[0]].tag_loop_inputs[7]
        list_nbplantes = [self.lsystems[n].tag_loop_inputs[11] for n in self.idsimu]
        list_ls_ftswStress = [self.lsystems[n].tag_loop_inputs[24] for n in self.idsimu]
        list_ls_NNIStress = [self.lsystems[n].tag_loop_inputs[25] for n in self.idsimu]
        list_ls_TStress = [self.lsystems[n].tag_loop_inputs[26] for n in self.idsimu]
        list_lsApex = [self.lsystems[n].tag_loop_inputs[27] for n in self.idsimu]
        list_lsApexAll = [self.lsystems[n].tag_loop_inputs[28] for n in self.idsimu]
        list_opt_stressW = [self.lsystems[n].tag_loop_inputs[38] for n in self.idsimu]
        list_opt_stressN = [self.lsystems[n].tag_loop_inputs[39] for n in self.idsimu]
        opt_stressGel = self.lsystems[self.idsimu[0]].tag_loop_inputs[40]

        if self.domain is None:
            surfsolref = self.lsystems[self.idsimu[0]].tag_loop_inputs[12]
        else:
            surfsolref = (self.domain[1][0] - self.domain[0][0]) * (self.domain[1][1] - self.domain[0][1])

        self.demandeN = []
        self.temps = []
        for k in range(len(self.idsimu)):
            self.invar[k], list_outvar[k], ls_demandeN_bis, temps = loop.daily_growth_loop(
                list_ParamP[k],
                self.invar[k],
                list_outvar[k],
                self.epsi[k],
                meteo_j,
                mng_j,
                list_nbplantes[k],
                surfsolref,
                list_ls_ftswStress[k],
                list_ls_NNIStress[k],
                list_ls_TStress[k],
                list_lsApex[k],
                list_lsApexAll[k],
                list_opt_stressW[k],
                list_opt_stressN[k],
                opt_stressGel,
            )

            self.demandeN.append(ls_demandeN_bis)
            self.temps.append(temps)

    def run(self):
        # rassemble les paramètres propres à chaque lsystem
        (
            list_outvar,
            list_invar_sc,
            list_ParamP,
            list_cutNB,
            list_nbplantes,
            list_start_time,
            list_dicFeuilBilanR,
            list_par_SN,
            list_ls_roots,
            list_ls_mat_res,
            list_vCC,
            list_ls_ftswStress,
            list_ls_NNIStress,
            list_ls_TStress,
            list_lsApex,
            list_lsApexAll,
            list_dicOrgans,
            list_deltaI_I0,
            list_nbI_I0,
            list_I_I0profilLfPlant,
            list_I_I0profilPetPlant,
            list_I_I0profilInPlant,
            list_NlClasses,
            list_NaClasses,
            list_NlinClasses,
            list_opt_stressW,
            list_opt_stressN,
        ) = ([] for i in range(27))
        for n in self.idsimu:
            (
                invar,
                outvar,
                invar_sc,
                ParamP,
                station,
                carto,
                meteo_j,
                mng_j,
                DOY,
                cutNB,
                start_time,
                nbplantes,
                surfsolref,
                m_lais,
                dicFeuilBilanR,
                surf_refVOX,
                triplets,
                ls_dif,
                S,
                par_SN,
                lims_sol,
                ls_roots,
                ls_mat_res,
                vCC,
                ls_ftswStress,
                ls_NNIStress,
                ls_TStress,
                lsApex,
                lsApexAll,
                dicOrgans,
                deltaI_I0,
                nbI_I0,
                I_I0profilLfPlant,
                I_I0profilPetPlant,
                I_I0profilInPlant,
                NlClasses,
                NaClasses,
                NlinClasses,
                opt_stressW,
                opt_stressN,
                opt_stressGel,
                opt_residu,
                dxyz,
            ) = self.lsystems[n].tag_loop_inputs

            list_dicFeuilBilanR.append(dicFeuilBilanR)
            list_ParamP.append(ParamP)
            list_outvar.append(outvar)
            list_invar_sc.append(invar_sc)
            list_cutNB.append(cutNB)
            list_vCC.append(vCC)
            list_start_time.append(start_time)
            list_nbplantes.append(nbplantes)
            list_ls_ftswStress.append(ls_ftswStress)
            list_ls_NNIStress.append(ls_NNIStress)
            list_ls_TStress.append(ls_TStress)
            list_ls_roots.append(ls_roots)
            list_lsApex.append(lsApex)
            list_lsApexAll.append(lsApexAll)
            list_opt_stressW.append(opt_stressW)
            list_opt_stressN.append(opt_stressN)
            list_par_SN.append(par_SN)
            list_I_I0profilLfPlant.append(I_I0profilLfPlant)
            list_I_I0profilPetPlant.append(I_I0profilPetPlant)
            list_I_I0profilInPlant.append(I_I0profilInPlant)
            list_NlClasses.append(NlClasses)
            list_NaClasses.append(NaClasses)
            list_NlinClasses.append(NlinClasses)
            list_dicOrgans.append(dicOrgans)
            list_deltaI_I0.append(deltaI_I0)
            list_nbI_I0.append(nbI_I0)
            list_ls_mat_res.append(ls_mat_res)

        # pour les variables communes
        (
            invar0,
            outvar0,
            invar_sc0,
            ParamP0,
            station0,
            carto0,
            meteo_j,
            mng_j,
            DOY,
            cutNB,
            start_time,
            nbplantes0,
            surfsolref0,
            m_lais0,
            dicFeuilBilanR0,
            surf_refVOX,
            triplets,
            ls_dif0,
            S,
            par_SN0,
            lims_sol0,
            ls_roots0,
            ls_mat_res0,
            vCC0,
            ls_ftswStress0,
            ls_NNIStress0,
            ls_TStress0,
            lsApex0,
            lsApexAll0,
            dicOrgans0,
            deltaI_I00,
            nbI_I00,
            I_I0profilLfPlant0,
            I_I0profilPetPlant0,
            I_I0profilInPlant0,
            NlClasses0,
            NaClasses0,
            NlinClasses0,
            opt_stressW,
            opt_stressN,
            opt_stressGel,
            opt_residu,
            dxyz,
        ) = self.lsystems[self.idsimu[0]].tag_loop_inputs

        if self.domain is None:
            surfsolref = surfsolref0
        else:
            surfsolref = (self.domain[1][0] - self.domain[0][0]) * (self.domain[1][1] - self.domain[0][1])

        [soil, stateEV, ls_ftsw, ls_transp, ls_Act_Nuptake_plt, temps_sol] = self.results_soil_legume

        # gere desagregattion par esp des sorties
        list_ls_ftsw = []
        list_ls_transp = []
        list_ls_Act_Nuptake_plt = []
        list_temps_sol = []
        for k in range(len(self.idsimu)):
            a = int(sum(self.nb_plant_per_specy[:k]))
            b = int(sum(self.nb_plant_per_specy[: k + 1]))

            list_ls_ftsw.append(ls_ftsw[a:b])
            list_ls_transp.append(ls_transp[a:b])
            list_ls_Act_Nuptake_plt.append(ls_Act_Nuptake_plt[a:b])
            list_temps_sol.append(temps_sol[a:b])

        ##########
        # setp update plant stress variables
        ##########
        for k in range(len(self.idsimu)):
            tag_inputs_stress = [
                list_ParamP[k],
                self.invar[k],
                list_invar_sc[k],
                self.temps[k],
                DOY,
                list_nbplantes[k],
                surfsolref,
                self.epsi[k],
                list_ls_ftsw[k],
                list_ls_transp[k],
                list_ls_Act_Nuptake_plt[k],
                self.demandeN[k],
                list_ls_ftswStress[k],
                list_ls_TStress[k],
                list_dicOrgans[k],
                list_dicFeuilBilanR[k],
                list_lsApex[k],
                list_start_time[k],
                list_cutNB[k],
                list_deltaI_I0[k],
                list_nbI_I0[k],
                list_I_I0profilLfPlant[k],
                list_I_I0profilPetPlant[k],
                list_I_I0profilInPlant[k],
                list_NlClasses[k],
                list_NaClasses[k],
                list_NlinClasses[k],
                list_outvar[k],
            ]

            (
                self.invar[k],
                list_invar_sc[k],
                list_outvar[k],
                list_I_I0profilInPlant[k],
                list_ls_ftswStress[k],
                list_ls_NNIStress[k],
                list_ls_TStress[k],
            ) = loop.Update_stress_loop(*tag_inputs_stress)

        ##########
        # step update soil residues senescence
        ##########

        ls_mat_res = list_ls_mat_res[0]
        ParamP = list_ParamP[0]
        for p in list_ParamP[1:]:
            ParamP = ParamP + p
        ls_roots = list_ls_roots[0]
        for r in list_ls_roots[1:]:
            ls_roots = ls_roots + r

        # refait initialisation des residues au step 1 avec ensemble des plante (ParamP commun)
        if iter == 1 and opt_residu == 1:
            CC = init_plant_residues_fromParamP(S, opt_residu, ParamP, par_SN)

        if opt_residu == 1:  # option residu activee: mise a jour des cres
            # gere l'aggregation des entrees par espce
            vCC = list_vCC[0]
            for v in list_vCC[1:]:
                vCC = vCC + v

            invar_merge = self.invar[0]
            for inv in self.invar[1:]:
                invar_merge = IOtable.merge_dict_list(
                    [invar_merge, inv],
                    ls_keys=[
                        "dMSenRoot",
                        "dMSenFeuil",
                        "dMSenTige",
                        "dMSenNonRec",
                        "dMSenPiv",
                        "dMSmortGel_aer",
                        "dMSmortPlant_aer",
                        "dMSmortPlant_racfine",
                        "dMSmortPlant_pivot",
                        "isGelDam",
                    ],
                )

            tag_inputs_residue_updt = [ls_mat_res, S, ls_roots, par_SN["PROFHUMs"], ParamP, invar_merge, opt_stressGel]
            ls_mat_res = loop.distrib_residue_mat_frominvar(
                *tag_inputs_residue_updt
            )  # update la matrice des residus (propre a l-egume/VGL)
            S = loop.merge_residue_mat(ls_mat_res, vCC, S)  # update du sol

        #########
        # reinjecte les sorties midiee dans le lsystem
        #########
        for k, n in enumerate(self.idsimu):
            self.lsystems[n].invar = self.invar[k]
            self.lsystems[n].outvar = list_outvar[k]
            self.lsystems[n].invar_sc = list_invar_sc[k]

            self.lsystems[n].S = S
            self.lsystems[n].stateEV = stateEV
            self.lsystems[n].ls_mat_res = ls_mat_res

            self.lsystems[n].res_trans = self.res_trans
            if self.res_abs_i is not None:
                self.lsystems[n].res_abs_i = numpy.array([self.res_abs_i[k]])
            self.lsystems[n].res_rfr = self.rfr

            self.lsystems[n].ls_ftswStress = list_ls_ftswStress[k]
            self.lsystems[n].ls_NNIStress = list_ls_NNIStress[k]
            self.lsystems[n].ls_TStress = list_ls_TStress[k]
            self.lsystems[n].I_I0profilInPlant = list_I_I0profilInPlant[k]

    def end(self):
        for n in self.idsimu:
            print(("".join((n, " - done"))))
            # désallocation des lsystem
            self.lsystems[n].clear()

    def voxels_size(self):
        return self.lsystems[self.idsimu[0]].tag_loop_inputs[-1]

    def number_of_voxels(self):
        leaf_area_per_voxels = self.lsystems[self.idsimu[0]].tag_loop_inputs[13]
        return leaf_area_per_voxels.shape

    def number_of_species(self):
        return len(self.idsimu)

    def concatene_angle_distributions(self):
        # return: list de array, chaque array une distrib par espèce de plantes (peu y en voir plusieurs par usm)
        list_ls_dif = [self.lsystems[n].tag_loop_inputs[17] for n in self.idsimu]
        same_entity = False
        for dis in list_ls_dif[1:]:
            same_entity = (list_ls_dif[0][0] == dis[0]).all()

        if same_entity:
            ls_dif = list_ls_dif[0][0]
        else:
            ls_dif = list_ls_dif[0]
            for d in list_ls_dif[1:]:
                ls_dif = ls_dif + d

        return ls_dif

    def concatene_leaf_area(self):
        # usm1 : [esp1, esp2, ...] ; usm2 : [esp3, esp2, ...]
        # m_lais, une grille 3D par espèce de plante
        list_m_lais = [self.lsystems[n].tag_loop_inputs[13] for n in self.idsimu]
        list_ls_dif = [self.lsystems[n].tag_loop_inputs[17] for n in self.idsimu]
        same_entity = False
        for dis in list_ls_dif[1:]:
            same_entity = (list_ls_dif[0][0] == dis[0]).all()

        if same_entity:
            m_lais = list_m_lais[0]
            for m in list_m_lais[1:]:
                m_lais = m_lais + m
        else:
            m_lais = list_m_lais[0]
            for m in list_m_lais[1:]:
                m_lais = numpy.append(m_lais, m, axis=0)

        return m_lais

    def transfer_ratp_legume(self, energy, voxels_outputs, nb0, epsilon=1e-8):
        m_lais = self.concatene_leaf_area()
        # initialize absorb energy array
        res_abs_i = numpy.zeros((m_lais.shape[0], m_lais.shape[1], m_lais.shape[2], m_lais.shape[3]))

        ratpzlayers = max(voxels_outputs["Nz"])

        # voxel top side area
        dS = self.lsystems[self.idsimu[0]].tag_loop_inputs[15]
        res_trans = numpy.ones((m_lais.shape[1], m_lais.shape[2], m_lais.shape[3]))
        # maximum transmitted energy is total incoming energy per area
        res_trans = res_trans * (energy * dS)

        for ix in range(m_lais.shape[3]):
            for iy in range(m_lais.shape[2]):
                for iz in range(ratpzlayers):
                    legume_iz = iz + nb0

                    condition_x = voxels_outputs.Nx == m_lais.shape[2] - iy
                    vox_data = voxels_outputs[
                        condition_x & (voxels_outputs.Ny == ix + 1) & (voxels_outputs.Nz == iz + 1)
                    ]
                    if not vox_data.empty:
                        a = min(sum(vox_data["Transmitted"]), dS)
                        res_trans[legume_iz, iy, ix] = energy * a

                    s_entity = 0
                    for k in range(m_lais.shape[0]):
                        s_entity += m_lais[k][legume_iz][iy][ix]

                    if s_entity > 0.0:
                        for ie in range(m_lais.shape[0]):
                            if len(vox_data) > 0:
                                v_dat = vox_data[vox_data.VegetationType == ie + 1]
                                v = v_dat["Intercepted"].values[0]
                                if v > epsilon:
                                    res_abs_i[ie, legume_iz, iy, ix] = energy * v

                                # if a voxel has leaf area > 0, it must have a minimum intercepted energy value
                                else:
                                    res_abs_i[ie, legume_iz, iy, ix] = epsilon

        return res_abs_i, res_trans

    def transfer_caribu_legume(
        self,
        energy,
        id,
        nb0,
        elements_outputs,
        sensors_outputs,
        epsilon=1e-8,
    ):
        ## Absorb radiations for each plant of each specy
        for k in range(len(self.idsimu)):
            # initialize absorb energy
            nplantes = len(self.invar[k]["Hplante"])
            self.invar[k]["parap"] = scipy.array([0.0] * nplantes)
            self.invar[k]["parip"] = scipy.array([0.0] * nplantes)

            ent_organs_outputs = pandas.DataFrame({})
            if id is None:
                filter = elements_outputs.VegetationType == k
                ent_organs_outputs = elements_outputs[filter]
            elif isinstance(id, list) or isinstance(id, tuple):
                filter = elements_outputs.VegetationType == id[k]
                ent_organs_outputs = elements_outputs[filter]

            # non empty scene
            for i in range(len(ent_organs_outputs)):
                organe_id = int(ent_organs_outputs.iloc[i]["Organ"])

                # PAR in W/m²
                par_intercept = ent_organs_outputs.iloc[i]["par Ei"] * energy
                S_leaf = ent_organs_outputs.iloc[i]["Area"]

                id_plante = self.lstrings[k][organe_id][0]
                p_s = par_intercept * S_leaf
                a = float(self.invar[k]["parip"][id_plante])
                self.invar[k]["parip"][id_plante] = a + p_s

                # we remove senescent leaves
                if self.lstrings[k][organe_id][9] != "sen":
                    a = float(self.invar[k]["parap"][id_plante])
                    self.invar[k]["parap"][id_plante] = a + p_s

            # all non empty plant must have a minimum intercepted energy
            plants_surface = self.lsystems[self.idsimu[k]].tag_loop_inputs[14]["surf"]
            if plants_surface != []:
                if len(self.invar[k]["parip"]) == len(plants_surface):
                        for p in range(len(self.invar[k]["parip"])):
                            if self.invar[k]["parip"][p] == 0.0 and plants_surface[p] > 0.0:
                                self.invar[k]["parip"][p] = epsilon

            # conversion
            c = (3600 * 24) / 1000000
            self.invar[k]["parap"] *= c
            self.invar[k]["parip"] *= c

        ## Transmitted radiations throughout a grid of voxels
        m_lais = self.lsystems[self.idsimu[0]].tag_loop_inputs[13]
        res_trans = numpy.ones((m_lais.shape[1], m_lais.shape[2], m_lais.shape[3]))

        # if non empty scene
        if not elements_outputs.empty:
            ID_capt = 0
            for ix in range(m_lais.shape[3]):
                for iy in range(m_lais.shape[2]):
                    for iz in range(m_lais.shape[1] - nb0):
                        a = min(sensors_outputs["par"][ID_capt], 1.0)
                        res_trans[((m_lais.shape[1] - 1)) - iz][iy][ix] = a
                        ID_capt += 1

        # surface d'une face d'un voxel
        dS = self.lsystems[self.idsimu[0]].tag_loop_inputs[15]
        # gives maximum transmitted energy
        res_trans = res_trans * energy * dS

        return res_trans

    def energy(self):
        meteo_j = self.lsystems[self.idsimu[0]].tag_loop_inputs[6]
        energy = 0.48 * meteo_j["RG"] * 10000 / (3600 * 24)
        return energy

    def doy(self):
        DOY = self.lsystems[self.idsimu[0]].tag_loop_inputs[8]
        return DOY

    def set_domain(self, domain):
        self.domain = domain

    @staticmethod
    def fake_scene():
        epsilon = 1e-14
        return {0 : [[(0., 0., 0.), (0., epsilon, 0.), (0., epsilon, epsilon)]]}


def passive_lighting(data, energy, DOY, scene, legume_facade, lighting_facade):
    invar_saved = deepcopy(legume_facade.invar)
    lighting_facade.run(scenes_l_egume=scene, energy=energy, day=DOY, parunit="RG")

    legume_facade.light_results(energy, lighting_facade)
    legume_facade.invar = deepcopy(invar_saved)

    for i in range(len(legume_facade.idsimu)):
        data[i]["epsi"].extend(legume_facade.epsi[i])
        data[i]["parip"].extend(legume_facade.invar[i]["parip"])
        data[i]["t"].extend([DOY] * len(legume_facade.epsi[i]))

def lsystemInputOutput_usm_with_planter(fxls_usm, foldin = 'input', ongletBatch = 'exemple', i=0, path_OUT='output', planter=None, planter_index=0):
    """" cree et update l-system en fonction du fichier usm """
    import legume
    import openalea.lpy as lpy

    # lecture de la liste des usm
    usm_path = os.path.join(foldin, fxls_usm)
    usms = IOxls.xlrd.open_workbook(usm_path)
    ls_usms = IOtable.conv_dataframe(IOxls.get_xls_col(usms.sheet_by_name(ongletBatch)))

    # force l'arrangement via le planter
    if planter is not None:
        ls_usms["typearrangement"][i] = planter.legume_typearrangement
        ls_usms['cote'][i] = planter.legume_cote
        ls_usms['nbcote'][i] = planter.legume_nbcote[planter_index]
        ls_usms['optdamier'][i] = planter.legume_optdamier

    fscenar = 'liste_scenarios.xls'
    fsd = 'exemple_sd.xls'
    fsdx = 'exemple_corr_matrix.xls'
    fopt = 'mod_susm.xls'
    fsta = 'stations_exemple.xls'
    ongletSta = 'Lusignan'

    path_opt = os.path.join(foldin, fopt)
    dic_opt = IOxls.read_plant_param(path_opt, "options")

    testsim = {}
    name = str(int(ls_usms['ID_usm'][i])) + '_' + str(ls_usms['l_system'][i])[0:-4]
    seednb = int(ls_usms['seed'][i])

    path_ = os.path.dirname(os.path.abspath(legume.__file__))
    path_lsys = os.path.join(path_, str(ls_usms['l_system'][i]))
    testsim[name] = lpy.Lsystem(path_lsys)

    meteo_path_ = os.path.join(foldin, str(ls_usms['meteo'][i]))
    ongletM_ = str(ls_usms['ongletM'][i])
    testsim[name].meteo = IOxls.read_met_file(meteo_path_, ongletM_)

    mn_path_ = os.path.join(foldin, str(ls_usms['mng'][i]))
    ongletMn_ = str(ls_usms['ongletMn'][i])
    testsim[name].mng = IOxls.read_met_file(mn_path_, ongletMn_)

    ini_path_ = os.path.join(foldin, str(ls_usms['inis'][i]))
    ongletIni_ = str(ls_usms['ongletIn'][i])
    testsim[name].inis = IOxls.read_plant_param(ini_path_, ongletIni_)

    path_plante = os.path.join(foldin, str(ls_usms['plante'][i]))
    testsim[name].path_plante = path_plante
    path_lsplt = os.path.join(foldin, str(ls_usms['lsplt'][i]))
    mixID = str(ls_usms['mixID'][i])
    tabSpe = pandas.read_excel(path_lsplt, sheet_name=mixID)
    ls_Spe = tabSpe["ongletP"].tolist()
    ongletP = ls_Spe[0]
    ongletPvois = ls_Spe[1]


    path_scenar = os.path.join(foldin, fscenar)
    testsim[name].mn_sc = path_scenar

    path_variance_geno = os.path.join(foldin, fsd)
    testsim[name].path_variance_geno = path_variance_geno

    path_variance_matrix = os.path.join(foldin, fsdx)
    testsim[name].path_variance_matrix = path_variance_matrix

    idscenar1 = int(ls_usms['scenario1'][i])
    idscenar2 = int(ls_usms['scenario2'][i])
    idscenar3 = int(ls_usms['scenario3'][i])
    idscenar4 = int(ls_usms['scenario4'][i])
    idscenar5 = int(ls_usms['scenario5'][i])
    idscenar6 = int(ls_usms['scenario6'][i])

    idscenar1_sd = int(ls_usms['scenario1_sd'][i])
    idscenar2_sd = int(ls_usms['scenario2_sd'][i])
    idscenar3_sd = int(ls_usms['scenario3_sd'][i])
    idscenar4_sd = int(ls_usms['scenario4_sd'][i])
    idscenar5_sd = int(ls_usms['scenario5_sd'][i])
    idscenar6_sd = int(ls_usms['scenario6_sd'][i])

    # sol
    path_sol = os.path.join(foldin, str(ls_usms['sol'][i]))
    ongletS = str(ls_usms['ongletS'][i])
    par_SN, par_sol = IOxls.read_sol_param(path_sol, ongletS)
    par_SN['concrr'] = 0.
    testsim[name].par_SN = par_SN
    testsim[name].par_sol = par_sol

    path_station = os.path.join(foldin, fsta)
    testsim[name].path_station = path_station
    testsim[name].ongletSta = ongletSta

    optdamier = int(ls_usms['optdamier'][i])
    nbcote = int(ls_usms['nbcote'][i])

    if str(ls_usms['typearrangement'][i]) == 'damier8':
        arrang = 'damier' + str(optdamier)
    if str(ls_usms['typearrangement'][i]) == 'damier16':
        arrang = 'damidouble' + str(optdamier)
    elif str(ls_usms['typearrangement'][i]) == 'row4':
        arrang = 'row' + str(optdamier)
    else:
        arrang = str(ls_usms['typearrangement'][i]) + str(optdamier)

    nommix = '_' + ongletP + '-' + ongletPvois + '_' + arrang + '_scenario' + str(idscenar2) + '-' + str(idscenar1)

    testsim[name].ls_Spe = ls_Spe
    testsim[name].nbcote = nbcote
    testsim[name].opt_sd = int(ls_usms['opt_sd'][i])
    testsim[name].opt_scenar = int(ls_usms['opt_scenar'][i])
    testsim[name].cote = float(ls_usms['cote'][i])
    testsim[name].deltalevmoy = float(ls_usms['deltalevmoy'][i])
    testsim[name].deltalevsd = float(ls_usms['deltalevsd'][i])
    testsim[name].typearrangement = str(ls_usms['typearrangement'][i])
    testsim[name].optdamier = optdamier
    testsim[name].ls_idscenar = [idscenar1, idscenar2, idscenar3, idscenar4, idscenar5, idscenar6]
    testsim[name].ls_idscenar_sd = [idscenar1_sd, idscenar2_sd, idscenar3_sd, idscenar4_sd, idscenar5_sd, idscenar6_sd]
    testsim[name].idscenar1_sd = idscenar1_sd
    testsim[name].idscenar2_sd = idscenar2_sd
    testsim[name].Rseed = seednb
    testsim[name].DOYdeb = int(ls_usms['DOYdeb'][i])
    testsim[name].DOYend = int(ls_usms['DOYend'][i])


    #mise a jour des options de simulation
    testsim[name].opt_residu = int(dic_opt['opt_residu'])  # si 0, pas activation de mineralisation
    testsim[name].opt_sd = int(dic_opt['opt_sd'])  # 1 #genere distribution des valeurs de parametres
    testsim[name].opt_covar = int(dic_opt['opt_covar'])  #definie matrice de cavariance a lire dans path_variance_matrix (0 opt_sd generere tirages independants)
    testsim[name].opt_shuffle = int(dic_opt['opt_shuffle']) # 1: for random order of plant species in ParamP ; 0: reular order
    testsim[name].opt_stressN = int(dic_opt['opt_stressN'])  # Active stress N; 1 = stress NNI actif (0= calcule, mais pas applique)
    testsim[name].opt_stressW = int(dic_opt['opt_stressW'])  # Active stressW; 1 = stress FTSW actif (0= calcule, mais pas applique)
    testsim[name].opt_ReadstressN = int(dic_opt['opt_ReadstressN'])  # Force stress N to read input values - for debugging/calibration
    testsim[name].opt_ReadstressW = int(dic_opt['opt_ReadstressW'])  # Force stress FTSW to read input values - for debugging/calibration
    testsim[name].opt_photomorph = int(dic_opt['opt_photomorph'])  # 1 #Activate photomorphogenetic effects on organ growth; 1 Actif (0= calcule, mais pas applique)
    testsim[name].opt_optT = int(dic_opt['opt_optT']) # option de calcul du cumul de temperature (0=betaD; 1=betaH; 2=lineaireD)
    testsim[name].opt_stressGel = int(dic_opt['opt_stressGel']) #Active gel stress option below Tgel
    testsim[name].opt_PP = int(dic_opt['opt_PP']) # Active photoperiodic effects (1 active; 0 inactive)
    testsim[name].opt_Nuptake = int(dic_opt['opt_Nuptake']) #options for calculating plant N uptake - 0:'STICS'  #1:'LocalTransporter'  #2:'old'
    testsim[name].opt_Mng = int(dic_opt['opt_Mng'])  # type of management file to be read: 0: default observed file ; 1: automatic management file #must be consistent with the management file!
    testsim[name].opt_ReadPP = int(dic_opt['opt_ReadPP'])  # Force photoperiod to read input values in management - for indoor experiment
    testsim[name].visu_root = int(dic_opt['visu_root'])  # 1# pour visualisation/interpretation root
    testsim[name].visu_shoot = int(dic_opt['visu_shoot'])  # 1# pour visualisation/interpretation shoot
    testsim[name].visu_leaf = int(dic_opt['visu_leaf'])  # 1# pour visualisation/interpretation feuilles slmt
    testsim[name].visu_sol = int(dic_opt['visu_sol'])  # 1# pour visualisation/interpretation sol
    testsim[name].visu_solsurf = int(dic_opt['visu_solsurf'])  # 0 pour visualisation du pattern
    testsim[name].frDisplay = int(dic_opt['frDisplay'])  # 1 #sauvegarde de la derniere vue
    testsim[name].movDisplay = int(dic_opt['movDisplay'])  # #sauvegarde toutes les vues pour faire un film
    testsim[name].opt_zip = int(dic_opt['opt_zip'])  # if 1, zip and delete the output csv files
    testsim[name].opt_verbose = int(dic_opt['opt_verbose'])  # 0, remove print in the console


    testsim[name].derivationLength = int(ls_usms['DOYend'][i]) - int(ls_usms['DOYdeb'][i])  # derivationLength variable predefinie dans L-py
    arr = str(ls_usms['typearrangement'][i])
    if arr == 'row4':
        nbplantes = nbcote * 4
    elif arr == 'row4_sp1' or arr == 'row4_sp2' :
        nbplantes = nbcote * 2
    elif arr == 'damier8' or arr == 'damier16' or arr == 'homogeneous' or arr == 'random8' or arr == 'damier9' or arr == 'damier10' or arr == 'damier8_4':  # carre homogene
        nbplantes = nbcote * nbcote
    elif arr == 'damier8_sp1' or arr == 'damier8_sp2' or arr == 'damier16_sp1' or arr == 'damier16_sp2' :
        nbplantes = int(nbcote * nbcote / 2)
    else:
        print('unknown arrangement and nbplant')

    a = lpy.AxialTree()
    a.append(testsim[name].attente(1))
    for j in range(0, nbplantes):
        a.append(testsim[name].Sd(j))

    testsim[name].axiom = a

    if int(ls_usms['opt_sd'][i]) == 1 or int(ls_usms['opt_sd'][i]) == 2:
        sdname = '_SD' + str(idscenar2_sd) + '-' + str(idscenar1_sd)
    else:
        sdname = '_-'

    # path fichiers de sortie
    testsim[name].path_out = path_OUT #os.path.join(path_, str(ls_usms['folder_out'][i]))
    testsim[name].outvarfile = 'toto_' + name + nommix + '_' + str(ls_usms['ongletMn'][i]) + '_' + str(seednb) + '_' + str(ls_usms['ongletM'][i]) + sdname + '_' + '.csv'
    testsim[name].lsorgfile = 'lsAxes_' + name + nommix + '_' + str(ls_usms['ongletMn'][i]) + '_' + str(seednb) + '_' + str(ls_usms['ongletM'][i]) + sdname + '_' + '.csv'
    testsim[name].outHRfile = 'outHR_' + name + nommix + '_' + str(ls_usms['ongletMn'][i]) + '_' + str(seednb) + '_' + str(ls_usms['ongletM'][i]) + sdname + '_' + '.csv'
    testsim[name].resrootfile = 'resroot_' + name + nommix + '_' + str(ls_usms['ongletMn'][i]) + '_' + str(seednb) + '_' + str(ls_usms['ongletM'][i]) + sdname + '_' + '.csv'
    testsim[name].outBilanNfile = 'BilanN_' + name + nommix + '_' + str(ls_usms['ongletMn'][i]) + '_' + str(seednb) + '_' + str(ls_usms['ongletM'][i]) + sdname + '_' + '.csv'
    testsim[name].outimagefile = 'scene_' + name + nommix + '_' + str(ls_usms['ongletMn'][i]) + '_' + str(seednb) + '_' + str(ls_usms['ongletM'][i]) + sdname + '_' + '.bmp'  # 'scene.bmp'
    testsim[name].outsdfile = 'paramSD_' + name + nommix + '_' + str(ls_usms['ongletMn'][i]) + '_' + str(seednb) + '_' + str(ls_usms['ongletM'][i]) + '_' + sdname + '_' + '.csv'
    testsim[name].outMngfile = 'MngAuto_' + name + nommix + '_' + str(ls_usms['ongletMn'][i]) + '_' + str(seednb) + '_' + str(ls_usms['ongletM'][i]) + '_' + sdname + '_' + '.csv'

    return testsim
