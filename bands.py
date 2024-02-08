import numpy as np
import matplotlib.pyplot as plt

from copy import deepcopy
import os
from datetime import datetime

from mp_api.client import MPRester
from pymatgen.io.ase import AseAtomsAdaptor

from ase.io.espresso import write_espresso_in
from config import bandgapConfig

import espresso

## Global Config ##
PW = bandgapConfig.PW
BANDS = bandgapConfig.BANDS
DOS = bandgapConfig.DOS
PROJWFC = bandgapConfig.PROJWFC

PPDIR = bandgapConfig.PSEUDOPOTENTIALS
MP_API_KEY = bandgapConfig.MP_API_KEY

## ASE + Materials Project Environment Setup ##

MP_ID = "mp-224" # Materials Project ID for WS2
            
## Get the structure from the Materials Project and convert to ASE
def get_cif(material_id):
    m = MPRester(MP_API_KEY)
    structure = m.get_structure_by_material_id(material_id)
    return structure

cif = get_cif(MP_ID)  
reduced_formula = str(cif).split("\n")[1].split(": ")[1]

AAA = AseAtomsAdaptor()
lattice = AAA.get_atoms(cif)

if not os.path.exists("./results"):
    os.mkdir("./results")   
outdir = "./results/{}".format(reduced_formula)
if not os.path.exists(outdir):
    os.mkdir(outdir)

# Quantum Espresso Settings
# fix parameter inputs

pseudopotentials = {}
for symbol in np.unique(lattice.get_chemical_symbols()):
    for pp in os.listdir(PPDIR):
        if pp.lower().startswith(symbol.lower()) and not (pp.lower()[1].isalpha() and not (len(symbol) > 1 and symbol[1].islower())):
            pseudopotentials[symbol] = pp  

n_cores = 4
k_pts = 8
magnetization = [0.3, 0.3, 0.1, 0.1, 0.1, 0.1]

scf_params = {
    'control': {
        'calculation': 'scf',
        'restart_mode': 'from_scratch',
        'tprnfor': True,
        'tstress': True,
        'nstep': 0, # set to 0 for test runs
        'pseudo_dir': PPDIR,
    },
    'system': {
        'ecutwfc': 30,  # PW cutoff
        'ecutrho': 240,   # Charge cutoff
        'ibrav': 0, # Bravais lattice type; 0 means no lattice set
        'ntyp': 2, # number of different atomic species
        'occupations': 'smearing',
        'smearing': 'gaussian',
        'degauss': 0.01,
        'nspin': 2,
    },
    'electrons': {
        'diagonalization': 'david',
        'mixing_beta': 0.4,
        'conv_thr': 1e-6,
    },
    'kpts': tuple([k_pts for _ in range(3)]),
    'parallel': 'all',
    'directory': outdir,  # Custom directory for calculation files
    'label': reduced_formula,  # Prefix for the filenames
    'logfile': "{}.log".format(reduced_formula),  # Logfile name
    'command': "mpirun -np {} " + PW + " -in {}.scf.pwi > {}.scf.pwo".format(n_cores, reduced_formula, reduced_formula),
}

lattice.set_initial_magnetic_moments(magmoms=2 * [0.3 * 18] + 4 * [0.1 * 6])

pwi = open(outdir + "/{}.scf.pwi".format(reduced_formula), "w")
write_espresso_in(
    pwi,
    lattice,
    input_data=scf_params,
    pseudopotentials=pseudopotentials,
    kpts=(k_pts, k_pts, k_pts),
)
pwi.close()

scf_params["control"]["calculation"] = "bands"
pwi = open(outdir + "/{}.bands.pwi".format(reduced_formula), "w")
write_espresso_in(
    pwi,
    lattice,
    input_data=scf_params,
    pseudopotentials=pseudopotentials,
    kpts=(k_pts, k_pts, k_pts),
)
pwi.close()

# BANDS SCF AND NSCF CALCULATION
espresso.run_pwscf(2, outdir, reduced_formula + ".scf.pwi", reduced_formula + ".scf.pwo")
espresso.run_pwscf(2, outdir, reduced_formula + ".bands.pwi", reduced_formula + ".bands.pwo")

# Read the band structure
spin_components = {
    "flat": 0,
    "up": 1,
    "down": 2
}
for k,v in spin_components.items():
    espresso.create_qe_file(
        {
            "bands": {
                "outdir": outdir,
                "prefix": reduced_formula,
                "filband": f"{reduced_formula}-bands.dat",
                "spin_component": v,
            }
        },
        outdir,
        reduced_formula + f".bands-pp-{k}.in",
    )

    espresso.run_bands(
        outdir,
        reduced_formula + f".bands-pp-{k}.in",
        reduced_formula + f".bands-pp-{k}.out",
    )

# DOS CALCULATIONS

scf_params["control"]["calculation"] = "nscf"
pwi = open(outdir + "/{}.nscf.pwi".format(reduced_formula), "w")
write_espresso_in(
    pwi,
    lattice,
    input_data=scf_params,
    pseudopotentials=pseudopotentials,
    kpts=(k_pts, k_pts, k_pts),
)
pwi.close()

espresso.run_pwscf(2, outdir, reduced_formula + ".nscf.pwi", reduced_formula + ".nscf.pwo")

# Read the density of states
espresso.create_qe_file(
    {
        "dos": {
            "outdir": outdir,
            "prefix": reduced_formula,
            "fildos": f"{reduced_formula}-dos.dat",
            "spin_component": v,
            "DeltaE": 0.1,
            "!emin": -10,
            "!emax": 35,
        }
    },
    outdir,
    reduced_formula + f".dos.in",
)

espresso.run_dos(outdir, reduced_formula + ".dos.in", reduced_formula + ".dos.out")

espresso.create_qe_file(
    {
        "projwfc": {
            "outdir": outdir,
            "prefix": reduced_formula,
            "filpdos": f"{reduced_formula}-pdos.dat",
            "DeltaE": 0.1,
            "ngauss": 1,
            "degauss": 0.02,
            "!emin": -10,
            "!emax": 35,
        }
    },
    outdir,
    reduced_formula + f".pdos.in",
)

espresso.run_pdos(outdir, reduced_formula + ".pdos.in", reduced_formula + ".pdos.out")
