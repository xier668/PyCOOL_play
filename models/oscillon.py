import numpy as np
pi = np.pi

"""
###############################################################################
# Define a scalar field model and a lattice
###############################################################################
"""

model_name = 'oscillon'

"Model parameters and values:"

"Reduced Planck mass (mpl) and regular Planck mass (MPl):"
mpl = 1.
MPl = np.sqrt(8*pi)*mpl

"Mass unit that is used to define other variables:"
m = 5e-6*mpl

"Scalar field masses:"
m2f1 = m**2.

"Coupling strength:"
lamb = 2.8125e-6
g2 = lamb**2/0.1

"Initial values for the fields and the field time derivatives:"

f10 = np.sqrt((3*lamb)/(5*g2))*m

df1_dt0 = 1e-16*m

fields0 = [f10]
pis0 = [df1_dt0]

"List of the potential functions:"

"Potentials functions of the fields:"
V_list = ["0.5*C1*f1**2"]

"Interaction terms of the fields:"
V_int = ["(-0.25*C2*f1**4)","0.16666666666666666*C3*f1**6"]

"Numerical values for C1, C2, ..."
C_coeff = [m2f1, lamb, g2/m**2]

"Numerical values for bare coefficients D1, D2, ..."
D_coeff = []

"""List of functions which are in 'powerform' in potential. For
   example for potential V = 1 + sin(f1)**2 power_list = ['sin(f1)'].
   Field variables are included automatically."""
power_list = []

"Initial values for homogeneous radiation and matter components:"
rho_r0 = 0.
rho_m0 = 0.

"Time step:"
dtau_m = 0.005/m

"Lattice side length:"
L_m = 400./m

"Lattice size, where n should be a power of two:"
n = 128

"Initial scale parameter:"
a_in = 1.

"Initial and final times:"
t_in = 0.
t_fin = 5000./m

"How frequently to save data:"
flush_freq = 4*1024

"If lin_evo = True use linearized evolution:"
lin_evo = False

"If calc_spect = True calculate spectrums at the end:"
calc_spect = True

"""The used method to calculate spectrums. Options 'latticeeasy' and 'defrost'.
   Defrost uses aliasing polynomial to smooth the spectrums."""
spectQ = 'defrost'#'latticeeasy'

"""If field_r = True calculate also energy densities of fields
without interaction terms:"""
field_r = True

"""If field_lpQ = True calculate correlation lengths of the energy densities
   of the fields without interaction terms:"""
field_lpQ = False

"If deSitter = True include -9H^2/(4m^2) terms in \omega_k^2 term:"
deSitterQ = False

"If testQ = True use a constant seed. Can be used for debugging and testing:"
testQ = False

"If m2_effQ = True writes a*m_eff/m to SILO file."
m2_effQ = False

"""Maximum number of registers useb per thread. If set to None uses
default values 24 for single and 32 for double precision.
Note that this will also affect the used block size"""
max_reg = None
