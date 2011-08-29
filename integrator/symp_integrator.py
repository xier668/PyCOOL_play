﻿from jinja2 import Template
import codecs
import pycuda.driver as cuda
import pycuda.autoinit
import pycuda.gpuarray as gpuarray
from pycuda.compiler import SourceModule
import numpy as np

from lattice import *
import init.field_init as fi

def kernel_H2_gpu_code(lat, k, write_code=False):
    """
    Read kernel template from a file and compile a sourcemodule.
    Different values are read from Lattice Object lat and
    potential Object V."""

    fields = lat.fields

    if k == 0:
        eq_sign = '='
    else:
        eq_sign = '+='

    kernel_name = 'kernel_H2_'+str(k)

    print 'Compiling kernel: ' + kernel_name
    
    f = codecs.open('cuda_templates/kernel_H2.cu','r',encoding='utf-8')
    evo_code = f.read()
    f.close()

    tpl = Template(evo_code)

    "Summation term sum_i pi_i^2:"
  
    sumi = 'sum_i += pi1*pi1'
    if fields>=2:
        for i in xrange(2,fields+1):
            sumi += ' + pi'+str(i)+'*'+'pi'+str(i)
    sumi = sumi + ';'

    f_code = tpl.render(type_name_c = lat.prec_string,
                        fields_c = lat.fields,
                        stride_c = lat.stride,
                        DIM_X_c = lat.dimx,
                        DIM_Z_c = lat.dimz,
                        sum_c=sumi,
                        eq_sign_c = eq_sign)

    if write_code==True :
        g = codecs.open('output_kernels/debug_' + kernel_name + '.cu','w+',
                        encoding='utf-8')
        g.write(f_code)
        g.close()

    return SourceModule(f_code.encode( "utf-8" ),
                        options=['-maxrregcount=' + lat.reglimit,'-keep'])

def kernel_H3_gpu_code(lat, field_i, V, write_code=False):
    """
    Read kernel template from a file and compile a sourcemodule.
    Different values are read from Lattice Object lat and
    potential Object V."""

    fields = lat.fields

    i = field_i - 1

    "Write the lists of other fields:"
    other_fields = (list(set(range(1,fields+1))-set([field_i])))

    kernel_name = 'kernel_H3_' + 'field' + str(field_i)

    print 'Compiling kernel: ' + kernel_name

    f = codecs.open('cuda_templates/kernel_H3.cu','r',encoding='utf-8')
    evo_code = f.read()
    f.close()

    tpl = Template(evo_code)

    V_term = ''
    V_i_term = ''
    if V.V_i_H3[i] != None:
        V_term += V.V_i_H3[i]
        V_i_term += V.V_i_H3[i]
        if field_i == fields:
            V_term += '+(' + V.V_int_H3 + ')'

        V_term = '-(' + V_term + ')'

    else:
        if field_i == fields:
            V_term += V.V_int_H3
            V_term = '-(' + V_term + ')'

    f_code = tpl.render(kernel_name_c = kernel_name,
                        type_name_c = lat.prec_string,
                        f_coeff_l_c = V.f_coeff_l,
                        d_coeff_l_c = V.d_coeff_l,
                        field_i_c = field_i,
                        fields_c = lat.fields,
                        block_x_c = lat.block_x2,
                        block_y_c = lat.block_y2,
                        grid_x_c = lat.grid_x,
                        grid_y_c = lat.grid_y,
                        stride_c = lat.stride,
                        DIM_X_c = lat.dimx,
                        DIM_Y_c = lat.dimy,
                        DIM_Z_c = lat.dimz,
                        other_i_c = other_fields,
                        dV_c = V.dV_H3[i],
                        Vi_c = V.V_i_H3[i],
                        V_intQ = len(V.V_int_H3)>0,
                        V_int_c = V.V_int_H3,
                        V_c = V_term)

    if write_code==True :
        g = codecs.open('output_kernels/debug_' + kernel_name + '.cu','w+',
                        encoding='utf-8')
        g.write(f_code)
        g.close()

    return SourceModule(f_code.encode( "utf-8" ),
                        options=['-maxrregcount=' + lat.reglimit])

def kernel_lin_evo_gpu_code(lat, V, sim, write_code=True):
    """
    Read kernel template from a file and make compile a sourcemodule.
    Different values are read from Lattice Object lat and
    potential Object V."""

    kernel_name = 'kernel_linear_evo'

    print 'Compiling kernel: ' + kernel_name

    f = codecs.open('cuda_templates/kernel_linear_evo.cu','r',encoding='utf-8')
    evo_code = f.read()
    f.close()

    tpl = Template(evo_code)

    order = lat.order

    w_s = []

    if order == 4:
        k = 4.
        l = 1.0/(k-1)
        w1 = 1.0/(2.0 - 2.0**l)
        w0 = 1.0 - 2.0*w1
        w = [w1, w0, w1]
        for w_i in w:
            w_s.append('{number:.{digits}}'.format(number=w_i,
                                                   digits=16,
                                                   type = 'e'))

    elif order == 6:
        w1 = 0.78451361047755726382
        w2 = 0.23557321335935813368
        w3 = -1.17767998417887100695
        w4 = 1 - 2*(w1+w2+w3)
        w = [w1,w2,w3,w4,w3,w2,w1]
        for w_i in w:
            w_s.append('{number:.{digits}}'.format(number=w_i,
                                                   digits=16,
                                                   type = 'e'))

    elif order == 8:
        w1 = 0.74167036435061295345
        w2 = -0.40910082580003159400
        w3 = 0.19075471029623837995
        w4 = -0.57386247111608226666
        w5 = 0.29906418130365592384
        w6 = 0.33462491824529818378
        w7 = 0.31529309239676659663
        w8 = 1 - 2*(w1+w2+w3+w4+w5+w6+w7)
        w = [w1,w2,w3,w4,w5,w6,w7,w8,w7,w6,w5,w4,w3,w2,w1]
        for w_i in w:
            w_s.append('{number:.{digits}}'.format(number=w_i,
                                                   digits=16,
                                                   type = 'e'))


    a_c = -1.0/(6.*lat.VL_reduced)
    a_s = '{number:.{digits}}'.format(number=a_c,
                                      digits=16,
                                      type = 'e')

    f_code = tpl.render(real_name_c = lat.prec_string,
                        complex_name_c = lat.complex_string,
                        fields_c = lat.fields,
                        lin_coeff_l_c = V.lin_coeff_l,
                        stride_c = lat.stride,
                        DIM_X_c = lat.dimx,
                        DIMZ2 = lat.dimz2,
                        order = order,
                        w_i = w_s,
                        dk2 = lat.dk**2.0,
                        a_coeff = a_s,
                        VL = float(lat.VL),
                        rho_m = sim.rho_m0,
                        V_term = V.V_back,
                        dV = V.dV_back,
                        d2V0 = V.d2V_back,
                        d2V1 = V.d2V_back)

    if write_code==True :
        g = codecs.open('output_kernels/debug_' + kernel_name + '.cu','w+',
                        encoding='utf-8')
        g.write(f_code)
        g.close()

    return SourceModule(f_code.encode( "utf-8" ),
                        options=['-maxrregcount=' + lat.reglimit])

def kernel_k2_gpu_code(lat, V, write_code=False):
    """
    Read kernel template from a file and make compile a sourcemodule.
    Different values are read from Lattice Object lat and
    potential Object V."""


    kernel_name = 'kernel_k2'

    f = codecs.open('cuda_templates/'+kernel_name+'.cu','r',encoding='utf-8')
    evo_code = f.read()
    f.close()

    tpl = Template(evo_code)

    pi = np.pi
    w = 2*pi/lat.n
    w_s = '{number:.{digits}}'.format(number=w,
                                      digits=17,
                                      type = 'e')


    c0 = -64./15.
    c1 = 2*7./15.
    c2 = 4*1./10.
    c3 = 8*1./30.
    c = [c0, c1, c2, c3]
    c_s = []
    for x in c:
        c_s.append('{number:.{digits}}'.format(number=x,
                                               digits=17,
                                               type = 'e'))

    dk2_s = '{number:.{digits}}'.format(number=lat.dx**-2.,
                                        digits=17,
                                        type = 'e')


    f_code = tpl.render(real_name_c = lat.prec_string,
                        complex_name_c = lat.complex_string,
                        DIM_X = lat.dimx,
                        DIMZ2 = lat.dimz2,
                        stride = lat.stride,
                        fields_c = lat.fields, 
                        w_c = w_s,
                        ct_0 = c_s[0],
                        ct_1 = c_s[1],
                        ct_2 = c_s[2],
                        ct_3 = c_s[3],
                        dk2 = dk2_s)

    if write_code==True :
        g = codecs.open('output_kernels/debug_' + kernel_name + '.cu','w+',
                        encoding='utf-8')
        g.write(f_code)
        g.close()

    return SourceModule(f_code.encode( "utf-8" ),
                        options=['-maxrregcount=' + lat.reglimit])

def kernel_rho_pres_gpu_code(lat, field_i, V, write_code=False):
    """
    Read kernel template from a file and compile a sourcemodule.
    Different values are read from Lattice lat."""

    fields = lat.fields

    i = field_i - 1

    "Write the lists of other fields:"
    other_fields = (list(set(range(1,fields+1))-set([field_i])))

    if field_i == 1:
        eq_sign = '='
    else:
        eq_sign = '+='

    V_term = ''
    V_i_term = ''

    if V.V_i_rp[i] != None:
        V_term += V.V_i_rp[i]
        V_i_term += V.V_i_rp[i]
        if field_i == fields:
            V_term += '+(' + V.V_int_rp + ')'
    else:
        V_i_term += '0.0'
        if field_i == fields:
            V_term += V.V_int_rp
        else:
            V_term += '0.0'

    if V.V_int_rp not in ['','0.0'] and field_i == fields:
        inter = True
    else:
        inter = False

    V_inter = V.V_int_rp

    kernel_name = 'kernel_rho_pres_' + 'field' + str(field_i)

    print 'Compiling kernel: ' + kernel_name

    f = codecs.open('cuda_templates/rho_pres.cu','r',encoding='utf-8')
    evo_code = f.read()
    f.close()

    tpl = Template(evo_code)

    f_code = tpl.render(kernel_name_c = kernel_name,
                        type_name_c = lat.prec_string,
                        g_coeff_l_c = V.g_coeff_l,
                        d_coeff_l_c = V.d_coeff_l,
                        field_i_c = field_i,
                        fields_c = lat.fields,
                        block_x_c = lat.block_x2,
                        block_y_c = lat.block_y2,
                        grid_x_c = lat.grid_x,
                        grid_y_c = lat.grid_y,
                        stride_c = lat.stride,
                        DIM_X_c = lat.dimx,
                        DIM_Y_c = lat.dimy,
                        DIM_Z_c = lat.dimz,
                        other_i_c = other_fields,
                        eq_sign_c = eq_sign,
                        field_rho_c = lat.field_rho,
                        Vi_c = V_i_term,
                        V_c = V_term,
                        inter_c = inter,
                        V_int_c = V_inter)

    if write_code==True :
        g = codecs.open('output_kernels/debug_' + kernel_name + '.cu','w+',
                        encoding='utf-8')
        g.write(f_code)
        g.close()

    return SourceModule(f_code.encode( "utf-8" ),
                        options=['-maxrregcount='+lat.reglimit])

def kernel_spat_corr_gpu_code(lat, write_code=False):
    """
    Read kernel template from a file and compile a sourcemodule.
    Different values are read from Lattice lat."""

    kernel_name = 'kernel_spat_corr'

    print 'Compiling kernel: ' + kernel_name

    f = codecs.open('cuda_templates/spatial_corr.cu','r',encoding='utf-8')
    evo_code = f.read()
    f.close()

    tpl = Template(evo_code)

    f_code = tpl.render(kernel_name_c = kernel_name,
                        type_name_c = lat.prec_string,
                        block_x_c = lat.block_x2,
                        block_y_c = lat.block_y2,
                        grid_x_c = lat.grid_x,
                        grid_y_c = lat.grid_y,
                        stride_c = lat.stride,
                        DIM_X_c = lat.dimx,
                        DIM_Y_c = lat.dimy,
                        DIM_Z_c = lat.dimz)

    if write_code==True :
        g = codecs.open('output_kernels/debug_' + kernel_name + '.cu','w+',
                        encoding='utf-8')
        g.write(f_code)
        g.close()

    return SourceModule(f_code.encode( "utf-8" ),
                        options=['-maxrregcount='+lat.reglimit])



###############################################################################
# Class definitions
###############################################################################


class Simulation:
    """Simulation class carries information on
        - scale parameter a
        - canonical momentum p
        - physical time t
        - number of steps taken i0

        - initial radiation energy density rho_r0
        - initial matter energy density rho_m0
        - total energy density rho
        - initial energy density rho_in
        - homogeneous energy density rho_0
        - Hubble parameter H

        - initial squares of effective masses m2_eff
        - list of the scalar field objects
          (See field class for further info.)

        - total energy density field rho_gpu
        - total pressure density field pres_gpu
        - sum over z-direction of energy density rhosum_gpu
        - sum_gpu that is used when updating canonical momentum p
        - pa_gpu used in calc_wk_conf function. It equals p'/a.
        - filetype = The used filetype. Either hdf5 or silo.
        """
    
    def __init__(self, lat, V, t0, a0, rho_r0, rho_m0, f0, pi0,
                 deSitter=False, steps = 1000000, filetype='silo',
                 lin_evo = True):

        print "-" * 79

        self.t = t0
        self.t_list = [t0]
        self.a = a0
        self.a_list = [a0]
        self.i0 = 0
        self.i0_list = [0]

        self.rho_r0 = rho_r0
        self.rho_m0 = rho_m0
        self.rho = rho_init(V, f0, pi0) + rho_r0 + rho_m0
        self.rho_in = self.rho
        self.rho_0 = self.rho
        self.H = np.sqrt(lat.mpl**2.*self.rho/3.)
        self.H_in = np.sqrt(lat.mpl**2.*self.rho_in/3.)

        self.H_list = [self.H]
        self.p = -6.*lat.VL_reduced*self.H*self.a**2.
        self.p_list = [self.p]

        self.t_gpu = gpuarray.to_gpu(np.array(self.t, dtype = lat.prec_real))
        self.a_gpu = gpuarray.to_gpu(np.array(self.a, dtype = lat.prec_real))
        self.p_gpu = gpuarray.to_gpu(np.array(self.p, dtype = lat.prec_real))


        self.deSitter = deSitter

        self.lin_evo = lin_evo

        self.zeros = np.zeros(lat.dim_lH, dtype = lat.prec_real)
        self.zeros_i = np.zeros(lat.dims_k, dtype = np.int32)

        if self.lin_evo:
            "Array of k^2 values corresponding to discrete Laplacian:"
            self.k2_field = gpuarray.to_gpu(np.zeros(lat.dims_k))
            self.k2_bins = self.zeros
            self.k2_bins_gpu = gpuarray.to_gpu(self.k2_bins)
            self.k2_bin_id = gpuarray.to_gpu(self.zeros_i)


        """Number of steps in linearized CUDA kernel.
           If only one CUDA device in the system more than 1e6 steps
           can cause kernel fail."""
        if cuda.Device.count() == 1 and steps > 1000000:
            self.steps = 1000000
            print 'Only one CUDA device detected. Set steps to 1000000.\n'
        elif cuda.Device.count() == 1 and steps <= 1000000:
            self.steps = steps
        elif cuda.Device.count() > 1:
            self.steps = steps


        "These are used when flushing data:"
        self.flush_t = []
        self.flush_a = []
        self.flush_p = []
        self.flush_H = []
        "Absolute error:"
        self.fried_1 = []
        "Relative error:"
        self.k_error = []
        "Energy densities:"
        self.omega_rad_list = []
        self.omega_mat_list = []
        self.omega_int_list = []

        """This is used when reading data from files to store the read time
           and scale parameter values:"""
        self.t_read_list = []
        self.a_read_list = []

        "Correlation length list:"
        self.lp_list = []

        "Store the values of a and p after the linearized evolution:"
        self.a_lin_end = self.a
        self.p_lin_end = self.p

        "Create the fields:"
        if lat.test:
            print'Testing mode on! Set testQ to False to disable this.\n'
        
        self.m2_eff = mass_eff(V, lat.field_list, f0, self.H, deSitter)
        self.fields = [field(lat, V, f0[i], pi0[i], i+1, self.m2_eff[i], a0, 
                             lat.init_mode, lat.hom_mode)
                       for i in xrange(lat.fields)]
        "Function to calculate the numerical value of the potential function:"
        self.V = V_func(lat, V)

        "Various GPU-memory arrays:"
        self.rho_gpu = gpuarray.zeros(lat.dims_xyz, dtype = lat.prec_real)
        self.pres_gpu = gpuarray.zeros(lat.dims_xyz, dtype = lat.prec_real)

        self.rhosum_gpu = gpuarray.zeros(lat.dims_xy, dtype = lat.prec_real)
        self.rhosum_host = cuda.pagelocked_zeros(lat.dims_xy,
                                                 dtype = lat.prec_real)

        self.sum_gpu = gpuarray.zeros(lat.dims_xy, dtype = lat.prec_real)
        self.sum_host = cuda.pagelocked_zeros(lat.dims_xy,
                                              dtype = lat.prec_real)

        self.inter_sum_gpu = gpuarray.zeros(lat.dims_xy, dtype = lat.prec_real)
        self.inter_sum_host = cuda.pagelocked_zeros(lat.dims_xy,
                                                    dtype = lat.prec_real)

        "These arrays are used in the spatial correlation length kernels:"
        self.sum_nabla_rho_gpu = gpuarray.zeros(lat.dims_xy,
                                                dtype = lat.prec_real)
        self.sum_nabla_rho_h = cuda.pagelocked_zeros(lat.dims_xy,
                                                     dtype = lat.prec_real)

        self.sum_rho_squ_gpu = gpuarray.zeros(lat.dims_xy,
                                                dtype = lat.prec_real)
        self.sum_rho_squ_host = cuda.pagelocked_zeros(lat.dims_xy,
                                              dtype = lat.prec_real)


        "This array is used when calculating average of d2V/df^2:"
        self.pd_gpu = gpuarray.zeros(shape = lat.dims_xy,
                                     dtype = lat.prec_real)

        "These are used for storing constant memory arrays:"
        self.d_array = cuda.pagelocked_empty(V.d_coeff_l,
                                             dtype = lat.prec_real)
        self.f_array = cuda.pagelocked_empty(V.f_coeff_l,
                                             dtype = lat.prec_real)
        self.g_array = cuda.pagelocked_empty(V.g_coeff_l,
                                             dtype = lat.prec_real)
        self.h_array = cuda.pagelocked_empty(V.h_coeff_l,
                                             dtype = lat.prec_real)
        self.lin_array = cuda.pagelocked_empty(V.lin_coeff_l,
                                               dtype = lat.prec_real)

        "List used when calculating distributions of the energy densities:"
        self.rho_cdf = []
        self.rho_pdf = []

        "Create a Cuda Stream for the simulation:"
        self.stream = cuda.Stream()

        "Filetype to be used:"
        self.filetype = filetype

    def add_to_lists(self, lat):
        self.i0_list.append(self.i0)
        self.t_list.append(self.t)
        self.a_list.append(self.a)
        self.p_list.append(self.p)
        self.H_list.append(-self.p/(6*self.a**2.*lat.VL_reduced))

        for field in self.fields:
            field.f0_list.append(field.f0)
            field.pi0_list.append(field.pi0)

    def adjust_p(self, lat):
        """Use this only after initialization of the fields at t=t0 to include
           also the energy density of the perturbations in p"""
        H = np.sqrt(self.rho/3.)
        self.p = -6*lat.VL_reduced*H*self.a**2.

    def adjust_fields(self, lat):

        for field in self.fields:
            f = field.f_gpu.get()
            pi = field.pi_gpu.get()

            f_ave = sum(sum(sum(f)))/float(lat.VL)
            pi_ave = sum(sum(sum(pi)))/float(lat.VL)

            field.f = f + field.f0 - f_ave
            field.pi = pi + field.pi0 - pi_ave

            cuda.memcpy_htod(field.f_gpu.gpudata, field.f)
            cuda.memcpy_htod(field.pi_gpu.gpudata, field.pi)
            
        

    def flush(self, lat, path = 'data', physical = False,
              save_evo = False):
        """Write data to a hdf5 or silo file.
           path = Directory where to save data.
           physical = Write a comoving or a physical lattice into file.
                      This mainly affects the visualization of the lattice.
           scale = Multiply rho by 1.0/m**2."""

        import numpy as np

        mode = self.filetype

        "Physically global variables"
        a = self.a
        t = self.t
        p = self.p
        if physical:
            c = a
        else:
            c = 1.

        """
        if save_evo:
            import pickle
            
            data = {}
            data['i0'] = self.i0_list
            data['t'] = self.t_list
            data['a'] = self.a_list
            data['p'] = self.p_list
            for field in self.fields:
                data['field'+field.field_var+'_f0'] = field.f0_list
                data['field'+field.field_var+'_pi0'] = field.pi0_list

            pickle.dump( data, open( path + '/data.p', "wb" ) )
        """


        if mode == 'hdf5':
            import h5py
    
            f = h5py.File(path+'/sim_data_time.'+"%.6f" %t+' .hdf5', 'w')
            #f = h5py.File(path + '/sim_i0_' + str(self.i0) + '.hdf5', 'w')

            f['a'] = np.array(a, lat.prec_real)
            f['p'] = np.array(p, lat.prec_real)
            f['t'] = np.array(t, lat.prec_real)
            f['field_n'] = np.array(len(self.fields), np.int32)
    
            i = 1
            for field in self.fields:
                subgroup = f.create_group('field'+str(i))
                dset = subgroup.create_dataset('f', data=field.f_gpu.get())
                dset2 = subgroup.create_dataset('pi', data=field.pi_gpu.get())
                dset3 = subgroup.create_dataset('f0', data=field.f0)
                dset4 = subgroup.create_dataset('pi0', data=field.pi0)
                i += 1

            "Write pressure and energy densities:"
            subgroup = f.create_group('rp')
            dset = subgroup.create_dataset('rho', data=self.rho_gpu.get())
            dset2 = subgroup.create_dataset('pres', data=self.pres_gpu.get())
    
            f.close()

        elif mode == 'silo':
            import pyvisfile.silo as silo

            f = silo.SiloFile(path+'/sim_data_time.'+ str(self.i0) +'.silo',
                              mode=silo.DB_CLOBBER)

            coord = [
                np.linspace(-c*lat.L/2,c*lat.L/2, lat.dimx),
                np.linspace(-c*lat.L/2,c*lat.L/2, lat.dimy),
                np.linspace(-c*lat.L/2,c*lat.L/2, lat.dimz)
                ]

            f.put_quadmesh("meshxy", coord)

            options={}
            options[silo.DBOPT_DTIME] = t
            options[silo.DBOPT_CYCLE] = self.i0

            options2={}
            options2[silo.DBOPT_LABEL] = self.i0

            i = 1
            for field in self.fields:

                f.put_quadvar1('field'+str(i)+'_f', "meshxy",
                               np.asarray(field.f_gpu.get(), order="F"),
                               field.f_gpu.get().shape,
                               centering=silo.DB_NODECENT,
                               optlist=options)
                f.put_quadvar1('field'+str(i)+'_pi', "meshxy",
                               np.asarray(field.pi_gpu.get(), order="F"),
                               field.f_gpu.get().shape,
                               centering=silo.DB_NODECENT,
                               optlist=options)
                
                if lat.field_rho:
                    f.put_quadvar1('field'+str(i)+'_rho', "meshxy",
                                   np.asarray(field.rho_gpu.get(), order="F"),
                                   field.f_gpu.get().shape,
                                   centering=silo.DB_NODECENT,
                                   optlist=options)

                i += 1
            if lat.scale:
                c1 = 1.0/lat.m**2.
            else:
                c1 = 1.0

            f.put_quadvar1('rho', "meshxy",
                           np.asarray(c1*self.rho_gpu.get(), order="F"),
                           self.rho_gpu.get().shape,
                           centering=silo.DB_NODECENT,
                           optlist=options)
            f.put_quadvar1('pres', "meshxy",
                           np.asarray(c1*self.pres_gpu.get(), order="F"),
                           self.pres_gpu.get().shape,
                           centering=silo.DB_NODECENT,
                           optlist=options)

            t_val = lat.m*np.asarray(self.flush_t,dtype=np.float64)
            a_val = np.asarray(self.flush_a,dtype=np.float64)
            p_val = np.asarray(self.flush_p,dtype=np.float64)
            H_val = np.asarray(self.flush_H,dtype=np.float64)
            omega_r_val = np.asarray(self.omega_rad_list,dtype=np.float64)
            omega_m_val = np.asarray(self.omega_mat_list,dtype=np.float64)
            omega_int_val = np.asarray(self.omega_int_list,dtype=np.float64)

            lp_val = np.asarray(self.lp_list,dtype=np.float64)

            evo_val = 1.0/(a_val**(1.5)*H_val)*lat.m
            evo2_val = 1.0/(a_val**(2)*H_val)*lat.m

            
            "Numerical errors:"
            e_val = np.abs(np.asarray(self.fried_1,dtype=np.float64))
            er_val = np.abs(np.asarray(self.k_error,dtype=np.float64))

            f.put_curve('a',t_val,a_val,optlist=options2)
            f.put_curve('p',t_val,p_val,optlist=options2)
            f.put_curve('H',t_val,H_val,optlist=options2)
            f.put_curve('matscaledH',t_val, evo_val,optlist=options2)
            f.put_curve('radscaledH',t_val, evo2_val,optlist=options2)
            f.put_curve('lp',t_val, lp_val,optlist=options2)
            f.put_curve('omega_r',t_val,omega_r_val,optlist=options2)
            f.put_curve('omega_m',t_val,omega_m_val,optlist=options2)
            f.put_curve('omega_int',t_val,omega_int_val,optlist=options2)
            f.put_curve('Abs_num_error',t_val,e_val,optlist=options2)
            f.put_curve('rel_num_error',t_val,er_val,optlist=options2)

            i = 1
            for field in self.fields:
                w_val = np.asarray(field.w_list,dtype=np.float64)

                omega_val = np.asarray(field.omega_list,dtype=np.float64)

                f.put_curve('field'+str(i)+'_w',t_val,w_val,
                            optlist=options2)
                f.put_curve('omega_'+'field'+str(i),t_val,omega_val,
                            optlist=options2)

                if lat.field_rho and lat.field_lp:
                    lp_f_val = np.asarray(field.lp_list,dtype=np.float64)
                    f.put_curve('lp_field'+str(i),t_val,lp_f_val,
                                optlist=options2)

                i += 1



            if save_evo:
                t_val = np.asarray(self.t_list,dtype=np.float64)
                a_val = np.asarray(self.a_list,dtype=np.float64)
                p_val = np.asarray(self.p_list,dtype=np.float64)
                H_val = np.asarray(self.H_list,dtype=np.float64)

                f.put_curve('a_full',t_val,a_val,optlist=options2)
                f.put_curve('p_full',t_val,p_val,optlist=options2)
                f.put_curve('H_full',t_val,H_val,optlist=options2)

                i = 1
                for field in self.fields:
                    f.put_curve('field'+str(i)+'_f0',
                                t_val,
                                np.asarray(field.f0_list,
                                           dtype=np.float64),
                                optlist=options2)
                    f.put_curve('field'+str(i)+'_pi0',
                                t_val,
                                np.asarray(field.pi0_list,
                                           dtype=np.float64),
                                optlist=options2)

                    i += 1

            f.close()

    def calc_k2_bins(self, lat):
        """Return an array of different values of k^2 inside the lattice:"""

        k2n = lat.dx**2.*(self.k2_field.get())

        tmp = np.array(sorted(set(k2n.flatten())),dtype=np.float64)
        diff_list = np.diff(tmp)

        k2_bins = [tmp[0]]
        for i in xrange(1,len(diff_list)+1):
            if abs(diff_list[i-1])>1e-14:
                k2_bins.append(tmp[i])

        "Used CUDA block size:"
        block = lat.cuda_lin_block[0]

        new_len = int(np.ceil(len(k2_bins)/float(block))*block)

        """Make k2_bin a multiple of CUDA block size. What this means is
           that the last of the k2_bins are set to -1 and lead to clearly
           unphysical solutions and might become infinite. They are
           not however used when evolving the actual scalar field
           perturbations andcause no problems."""

        if new_len > len(k2_bins):
            for i in xrange(new_len-len(k2_bins)):
                k2_bins.append(-1.)

        self.k2_bins = lat.dx**-2.*np.array(k2_bins, dtype=lat.prec_real)
        self.k2_bins_gpu = gpuarray.to_gpu(self.k2_bins)

    def read(self, lat, filename):
        "Read data from a hdf5 or a silo file."

        import numpy as np
        mode = self.filetype

        self.i0 = sort_func(filename)
        i0 = self.i0

        if mode == 'hdf5':
            import h5py
    
            f = h5py.File(filename, 'r')

            "Global variables:"

            self.a =  f['a'].value
            self.p = f['p'].value
            self.t = f['t'].value
            field_number = f['field_n'].value
    
            i = 1
            for field in self.fields:
                field.f = f['field'+str(i)]['f'].value
                field.pi = f['field'+str(i)]['pi'].value
                cuda.memcpy_htod(field.f_gpu.gpudata, field.f)
                cuda.memcpy_htod(field.pi_gpu.gpudata, field.pi)

                field.f0 = f['field'+str(i)]['f0'].value
                field.pi0 = f['field'+str(i)]['pi0'].value
                i += 1

            "Write pressure and energy densities:"

            cuda.memcpy_htod(self.rho_gpu.gpudata, f['rp']['rho'].value)
            cuda.memcpy_htod(self.pres_gpu.gpudata, f['rp']['pres'].value)

            f.close()

        elif mode == 'silo':
            import pyvisfile.silo as silo

            f = silo.SiloFile(filename, create=False, mode=silo.DB_READ)

            self.a = f.get_curve('a').y[-1]
            self.p = f.get_curve('p').y[-1]
            self.H = f.get_curve('H').y[-1]
            self.t = f.get_curve('a').x[-1]

            self.t_read_list.append(self.t)
            self.a_read_list.append(self.a)

            i = 1
            for field in self.fields:
                field.f = np.array(f.get_quadvar('field'+str(i)+'_f').vals,
                                   lat.prec_real)
                field.pi = np.array(f.get_quadvar('field'+str(i)+'_pi').vals,
                                   lat.prec_real)
                cuda.memcpy_htod(field.f_gpu.gpudata, field.f)
                cuda.memcpy_htod(field.pi_gpu.gpudata, field.pi)

                i += 1

            if lat.scale:
                c1 = lat.m**2.
            else:
                c1 = 1.0

            cuda.memcpy_htod(self.rho_gpu.gpudata,
                             c1*np.array(f.get_quadvar('rho').vals,
                                      lat.prec_real))
            cuda.memcpy_htod(self.pres_gpu.gpudata,
                             c1*np.array(f.get_quadvar('pres').vals,
                                      lat.prec_real))

            f.close()

    def set_non_lin(self):
        """Set the values of a and p equal to the values
           after the linearized evolution:"""
        self.a = self.a_lin_end
        self.p = self.p_lin_end

    def store_lin_end(self):
        "Store the values of a and p after the linearized evolution:"
        self.a_lin_end = self.a
        self.p_lin_end = self.p

    def sample_fields(self, lat, init_m = 'cpu'):
        """Re-sample the initial perturbations of the fields"""

        for field in self.fields:
            field.sample_field(lat, init_m)

class field:
    """Field class:
        - self.field_i = field number
        - self.field_var = field variable
        - self.m2_eff = field effective mass squared

        - self.f0 = homogeneous background value of field
        - self.pi0 = homogeneous background value of pi

        - self.f0_list = store time evolution of homogeneous background value
        - self.pi0_list = store time evolution of homogeneous background value
        
        - self.f = field variable in host memory.
                   Currently used only in the initialization.
        - self.pi = canonical momentum in host memory.
                   Currently used only in the initialization.
        
        - self.f_gpu = field variable in device memory.
        - self.pi_gpu = canonical momentum in device memory.

        - self.f_perturb0_gpu = gpu_array of zeros used in the linearized
                                perturbation evolution as initial value
        - self.pi_perturb0_gpu = gpu_array of zeros used in the linearized
                                perturbation evolution as initial value
        - self.f_perturb1_gpu = gpu_array of ones used in the linearized
                                perturbation evolution as initial value
        - self.pi_perturb1_gpu = gpu_array of ones used in the linearized
                                perturbation evolution as initial value
        - self.d2V_sum_gpu = sum over z-direction of effective mass."""

    def __init__(self, lat, V, f0, pi0, field_i, m2_eff, a_in, init_m, hom_m):

        self.field_i = field_i
        self.field_var = 'f'+str(field_i)

        self.m2_eff = m2_eff

        "Initial homogeneous values:"
        self.f0_in = f0
        self.pi0_in = pi0

        "Homogeneous values:"
        self.f0 = f0
        self.pi0 = pi0

        self.f0_list = [f0]
        self.pi0_list = [pi0]

        self.f = fi.f_init(lat, f0, field_i, m2_eff, init_m, hom_m)
        self.pi = fi.fp_init(lat, pi0, field_i, m2_eff, a_in, init_m, hom_m)

        self.f_gpu = gpuarray.to_gpu(self.f)
        self.pi_gpu = gpuarray.to_gpu(self.pi)

        self.zeros = np.zeros(lat.dim_lH, dtype = lat.prec_real)
        self.ones = np.ones(lat.dim_lH, dtype = lat.prec_real)

        self.f0_field = np.zeros(1, dtype = lat.prec_real)
        self.pi0_field = np.zeros(1, dtype = lat.prec_real)

        self.f0_field[0] = f0
        self.pi0_field[0] = pi0

        self.f0_gpu = gpuarray.to_gpu(self.f0_field)
        self.pi0_gpu = gpuarray.to_gpu(self.pi0_field)

        self.f_lin_01_gpu = gpuarray.to_gpu(self.zeros)
        self.pi_lin_01_gpu = gpuarray.to_gpu(self.zeros)

        self.f_lin_10_gpu = gpuarray.to_gpu(self.ones)
        self.pi_lin_10_gpu = gpuarray.to_gpu(self.ones)

        self.rho_sum_gpu = gpuarray.zeros(shape = lat.dims_xy,
                                          dtype = lat.prec_real)
        self.pres_sum_gpu = gpuarray.zeros(shape = lat.dims_xy,
                                           dtype = lat.prec_real)

        if lat.field_rho:
            self.rho_gpu = gpuarray.zeros(lat.dims_xyz,
                                          dtype = lat.prec_real)
            #self.pres_gpu = gpuarray.zeros(lat.dims_xyz,
            #                               dtype = lat.prec_real)

            "These arrays are used in the spatial correlation length kernels:"
            self.sum_nabla_rho_gpu = gpuarray.zeros(lat.dims_xy,
                                                    dtype = lat.prec_real)
            self.sum_nabla_rho_h = cuda.pagelocked_zeros(lat.dims_xy,
                                                         dtype = lat.prec_real)

            self.sum_rho_squ_gpu = gpuarray.zeros(lat.dims_xy,
                                                  dtype = lat.prec_real)
            self.sum_rho_squ_h = cuda.pagelocked_zeros(lat.dims_xy,
                                                       dtype = lat.prec_real)

            self.lp_list = []



        "dV/df and d^2V/df^2 functions used in the background evolution:"
        self.dV = dV_func(lat, V, self.field_var)
        self.d2V = d2V_func(lat, V, self.field_var)

        "Store the values of equations of state:"
        self.w_list = []

        "Store the values of relative energy density:"
        self.omega_list = []

        "Arrays used in the spectrum calculations:"

        self.d2V_sum_gpu = gpuarray.zeros(shape = lat.dims_xy,
                                        dtype = lat.prec_real)

        self.w_k = 0

        self.n_k = np.zeros(lat.ns, dtype = np.float64)
        self.rho_k = np.zeros(lat.ns, dtype = np.float64)
        self.S = np.zeros(lat.ns, dtype = np.float64)
        #self.Fpk_sq = np.zeros(lat.ns, dtype = np.float64)
        self.W = np.zeros(lat.ns, dtype = np.int32)
        self.W_df = np.zeros(lat.ns, dtype = np.float64)
        
        "List of distinct k values used in the spectrums:"
        self.k_vals = np.arange(0,lat.ns)*lat.dk
        #np.linspace(0, lat.ns*lat.dk, num = lat.ns)

        "List used when calculating distributions of the energy densities:"
        self.rho_cdf = []
        self.rho_pdf = []

        """Store values of m2_eff. Note that m2_eff_list is actually
           list of a^2*d2V/df^2:"""
        self.m2_eff_list = []

        """Store the values of number of relativistic particles in
           the lattice as a fraction of all particles. Condition for this is
           k > a*m_eff."""
        self.rel_num_list = []

        """Store the values of comoving number densities of the field."""
        self.n_cov_list = []

        """Store the values of field skewness and kurtosis, respectively:"""
        self.skew_list = []
        self.kurt_list = []



    def perturb_field(self):
        "Subtract the homogeneous value from the f_gpu and pi_gpu arrays"
        tmp = self.f_gpu.get() - self.f0
        tmp2 = self.pi_gpu.get() - self.pi0

        cuda.memcpy_htod(self.f_gpu.gpudata, tmp)
        cuda.memcpy_htod(self.pi_gpu.gpudata, tmp2)

    def unperturb_field(self):
        "Add the homogeneous value to the f_gpu and pi_gpu arrays"
        tmp = self.f_gpu.get() + self.f0
        tmp2 = self.pi_gpu.get() + self.pi0

        cuda.memcpy_htod(self.f_gpu.gpudata, tmp)
        cuda.memcpy_htod(self.pi_gpu.gpudata, tmp2)

    def fft(self):
        """Fourier transform of f_gpu and pi_gpu. Note that this will change
           the id of f_gpu and pi_gpu. Update function has to be called after
           this in an Evolution object."""

        import numpy.fft as fft

        tmp = fft.rfftn(self.f_gpu.get()).transpose()
        tmp2 = fft.rfftn(self.pi_gpu.get()).transpose()
        self.f_gpu = gpuarray.to_gpu(np.array(tmp))
        self.pi_gpu = gpuarray.to_gpu(np.array(tmp2))

    def ifft(self):
        """Inverse Fourier transform of f_gpu and pi_gpu.
           Note that this will change the id of f_gpu and pi_gpu.
           Update function has to be called after this in
           an Evolution object."""

        import numpy.fft as fft

        tmp = fft.irfftn(self.f_gpu.get().transpose())
        tmp2 = fft.irfftn(self.pi_gpu.get().transpose())
        self.f_gpu = gpuarray.to_gpu(np.array(tmp))
        self.pi_gpu = gpuarray.to_gpu(np.array(tmp2))

    def set_perturb(self):
        """Set f_lin_0_gpu and pi_lin_0_gpu arrays to zero and
           Set f_lin_1_gpu and pi_lin_1_gpu arrays to one."""
        cuda.memcpy_htod(self.f_lin_0_gpu.gpudata, self.zeros)
        cuda.memcpy_htod(self.pi_lin_0_gpu.gpudata, self.zeros)

        cuda.memcpy_htod(self.f_lin_1_gpu.gpudata, self.ones)
        cuda.memcpy_htod(self.pi_lin_1_gpu.gpudata, self.ones)

    def sample_field(self, lat, flag_method):
        """Recreate the initial perturbations if needed without
           the homogeneous values:"""
        
        self.f = fi.f_init(lat, self.f0_in, self.field_i, self.m2_eff,
                           flag_method, homogQ = False)
        self.pi = fi.fp_init(lat, self.pi0_in, self.field_i, self.m2_eff,
                             flag_method, homogQ = False)

        print 'f shape', self.f.shape, self.pi.shape

        cuda.memcpy_htod(self.f_gpu.gpudata, self.f)
        cuda.memcpy_htod(self.pi_gpu.gpudata, self.pi)



class H2_Kernel:
    "Used to evolve the field variables"
    def __init__(self, lat, k, write_code=False):
        self.mod = kernel_H2_gpu_code(lat, k, write_code)
        self.evo = self.mod.get_function('kernelH2')
        self.hc_add = self.mod.get_global("h_coeff")

    "Constant memory management:"
    def update_h(self, x, stream):
        cuda.memcpy_htod_async(self.hc_add[0],x, stream=None)
    def read_h(self,x):
        cuda.memcpy_dtoh(x,self.hc_add[0])


class H3_Kernel:
    "Used to evolve the canonical momentums of the fields"
    def __init__(self, lat, field_i, V, write_code=False):
        self.mod = kernel_H3_gpu_code(lat, field_i, V, write_code)
        self.evo = self.mod.get_function('kernel_H3_' + 'field' + str(field_i))
        self.cc_add = self.mod.get_global("c_coeff")
        self.dc_add = self.mod.get_global("d_coeff")
        self.fc_add = self.mod.get_global("f_coeff")

    "Constant memory management:"
    def update_c(self,x):
        cuda.memcpy_htod(self.cc_add[0],x)
    def read_c(self,x):
        cuda.memcpy_dtoh(x,self.cc_add[0])

    def update_d(self,x):
        cuda.memcpy_htod(self.dc_add[0],x)
    def read_d(self,x):
        cuda.memcpy_dtoh(x,self.dc_add[0])

    def update_f(self, x , stream):
        cuda.memcpy_htod_async(self.fc_add[0], x, stream=None)
    def read_f(self,x):
        cuda.memcpy_dtoh(x,self.fc_add[0])

class lin_evo_Kernel:
    "Used to evolve the canonical momentums of the fields"
    def __init__(self, lat, V, sim, write_code=False):
        self.mod = kernel_lin_evo_gpu_code(lat, V, sim, write_code)
        self.evo = self.mod.get_function('linear_evo')
        self.mod2 = kernel_k2_gpu_code(lat, V, write_code)
        self.k2_calc = self.mod2.get_function('gpu_k2')
        self.k2_bins_calc = self.mod2.get_function('gpu_k2_to_bin')
        self.lin_field_evo = self.mod2.get_function('gpu_evolve_lin_fields')

class rp_Kernel:
    "Used to calculate the energy densities of the fields"
    def __init__(self, lat, field_i, V, write_code=False):
        self.mod = kernel_rho_pres_gpu_code(lat, field_i, V, write_code)
        self.calc = self.mod.get_function('kernel_rho_pres_' +
                                          'field' + str(field_i))
        self.cc_add = self.mod.get_global("c_coeff")
        self.dc_add = self.mod.get_global("d_coeff")
        self.gc_add = self.mod.get_global("g_coeff")

    "Constant memory management:"

    def update_c(self,x):
        cuda.memcpy_htod(self.cc_add[0],x)
    def read_c(self,x):
        cuda.memcpy_dtoh(x,self.cc_add[0])

    def update_d(self,x):
        cuda.memcpy_htod(self.dc_add[0],x)
    def read_d(self,x):
        cuda.memcpy_dtoh(x,self.dc_add[0])

    def update_g(self, x, stream=None):
        cuda.memcpy_htod_async(self.gc_add[0], x, stream)
    def read_g(self,x):
        cuda.memcpy_dtoh(x,self.gc_add[0])


class corr_Kernel:
    "Used to calculate spatial correlation of variables"
    def __init__(self, lat, write_code=False):
        self.mod = kernel_spat_corr_gpu_code(lat, write_code)
        self.calc = self.mod.get_function('kernel_spat_corr')
        self.cc_add = self.mod.get_global("c_coeff")
        self.cor_c_add = self.mod.get_global("cor_coeff")

    "Constant memory management:"

    def update_c(self,x):
        cuda.memcpy_htod(self.cc_add[0],x)
    def read_c(self,x):
        cuda.memcpy_dtoh(x,self.cc_add[0])

    def update_corr(self,x):
        cuda.memcpy_htod(self.cor_c_add[0],x)
    def read_cor(self,x):
        cuda.memcpy_dtoh(x,self.cor_c_add[0])


class Evolution:
    """Create the necessary functions for the simulation,
       energy density and pressure calculations."""

    def __init__(self, lat, V, sim, write_code=True):

        print "-" * 79
        print 'Compiling necessary evolution kernels:'

        self.H2_kernels = [H2_Kernel( lat, 0, write_code),
                           H2_Kernel( lat, 1, write_code)]
        self.H3_kernels = [H3_Kernel(lat, i+1, V, write_code)
                           for i in xrange(lat.fields)]

        if sim.lin_evo:
            self.lin_evo_kernel = lin_evo_Kernel(lat, V, sim, write_code)

        self.rp_kernels = [rp_Kernel(lat, i+1, V, write_code)
                           for i in xrange(lat.fields)]

        self.sc_kernel = corr_Kernel(lat, write_code)

        "Load the discretization coefficients to constant memory:"
        for kernel in self.H3_kernels:
            kernel.update_c(lat.cc)
            kernel.update_d(V.D_coeffs_np)

        for kernel in self.rp_kernels:
            kernel.update_c(lat.cc)
            kernel.update_d(V.D_coeffs_np)

        self.sc_kernel.update_c(lat.cc)
        self.sc_kernel.update_corr(np.array(lat.dx**-2.,
                                            dtype = lat.prec_real))

        "Cuda function arguments used in H2 and H3:"
        self.cuda_arg = [sim.sum_gpu]
        for f in sim.fields:
            self.cuda_arg.append(f.f_gpu)
        for f in sim.fields:
            self.cuda_arg.append(f.pi_gpu)

        self.cuda_param_H2 = dict(block=lat.cuda_block_1,
                                  grid=lat.cuda_grid,
                                  stream = sim.stream)
        self.cuda_param_H3 = dict(block=lat.cuda_block_2,
                                  grid=lat.cuda_grid,
                                  stream = sim.stream)

        if sim.lin_evo:
            """Calculate k2_eff-terms needed in the perturbation evolution:"""
            self.lin_evo_kernel.k2_calc(sim.k2_field, **self.cuda_param_H2)

            "Calculate the bins:"
            sim.calc_k2_bins(lat)

            "Calculate into which bin an element of sim.k2_field belongs:"
            self.k2_arg = []
            self.k2_arg.append(sim.k2_field)
            self.k2_arg.append(sim.k2_bins_gpu)
            self.k2_arg.append(sim.k2_bin_id)
            self.k2_arg.append(np.int32(len(sim.k2_bins)))

            self.lin_evo_kernel.k2_bins_calc(*self.k2_arg, **self.cuda_param_H2)


            "Create the perturbation solution fields:"
            for field in sim.fields:
                field.f_lin_01_gpu = gpuarray.zeros_like(sim.k2_bins_gpu)
                field.pi_lin_01_gpu = gpuarray.zeros_like(sim.k2_bins_gpu)

                field.f_lin_10_gpu = gpuarray.zeros_like(sim.k2_bins_gpu)
                field.pi_lin_10_gpu = gpuarray.zeros_like(sim.k2_bins_gpu)


            "Cuda function arguments used in lin_evo:"
            self.lin_e_arg = []
            for f in sim.fields:
                self.lin_e_arg.append(f.f0_gpu)
            for f in sim.fields:
                self.lin_e_arg.append(f.pi0_gpu)
            for f in sim.fields:
                self.lin_e_arg.append(f.f_lin_01_gpu)
            for f in sim.fields:
                self.lin_e_arg.append(f.pi_lin_01_gpu)
            for f in sim.fields:
                self.lin_e_arg.append(f.f_lin_10_gpu)
            for f in sim.fields:
                self.lin_e_arg.append(f.pi_lin_10_gpu)

            self.lin_e_arg.append(sim.a_gpu)
            self.lin_e_arg.append(sim.p_gpu)
            self.lin_e_arg.append(sim.t_gpu)
            self.lin_e_arg.append(np.float64(lat.dtau))
            self.lin_e_arg.append(np.int32(sim.steps))
            self.lin_e_arg.append(sim.k2_bins_gpu)

            grid_lin = len(sim.k2_bins_gpu)/lat.cuda_lin_block[0]

            self.cuda_param_lin_e = dict(block=lat.cuda_lin_block,
                                         grid = (grid_lin,1),
                                         stream = sim.stream)

        "Cuda function arguments used in rho and pressure kernels:"
        self.rp_arg = [sim.rho_gpu, sim.pres_gpu, sim.rhosum_gpu,
                       sim.inter_sum_gpu]
        for f in sim.fields:
            self.rp_arg.append(f.f_gpu)
        for f in sim.fields:
            self.rp_arg.append(f.pi_gpu)
        for f in sim.fields:
            self.rp_arg.append(f.rho_sum_gpu)
        for f in sim.fields:
            self.rp_arg.append(f.pres_sum_gpu)
        if lat.field_rho:
            for f in sim.fields:
                self.rp_arg.append(f.rho_gpu)

        self.cuda_param_rp = dict(block=lat.cuda_block_2, grid=lat.cuda_grid)

        self.sc_arg = [sim.rho_gpu, sim.sum_nabla_rho_gpu,
                       sim.sum_rho_squ_gpu]
        self.cuda_param_sc = dict(block=lat.cuda_block_2, grid=lat.cuda_grid)

        print "-" * 79

    def update(self, lat, sim):
        """Update the argument list to take into account any changes that
           could have changed the memory ids of the numpy arrays in sim.fields.
           This has to be done after perturb, unperturb, fft or ifft
           operations or when a different Simulation object than the one during
           initialization is being evolved."""

        
        "Cuda function arguments used in H2 and H3:"
        self.cuda_arg = [sim.sum_gpu]
        for f in sim.fields:
            self.cuda_arg.append(f.f_gpu)
        for f in sim.fields:
            self.cuda_arg.append(f.pi_gpu)

        self.cuda_param_H2 = dict(block=lat.cuda_block_1, grid=lat.cuda_grid,
                                  stream = sim.stream)
        self.cuda_param_H3 = dict(block=lat.cuda_block_2, grid=lat.cuda_grid,
                                  stream = sim.stream)

        if sim.lin_evo:

            "Cuda function arguments used in lin_evo:"
            self.lin_e_arg = []
            for f in sim.fields:
                self.lin_e_arg.append(f.f0_gpu)
            for f in sim.fields:
                self.lin_e_arg.append(f.pi0_gpu)
            for f in sim.fields:
                self.lin_e_arg.append(f.f_lin_01_gpu)
            for f in sim.fields:
                self.lin_e_arg.append(f.pi_lin_01_gpu)
            for f in sim.fields:
                self.lin_e_arg.append(f.f_lin_10_gpu)
            for f in sim.fields:
                self.lin_e_arg.append(f.pi_lin_10_gpu)

            self.lin_e_arg.append(sim.a_gpu)
            self.lin_e_arg.append(sim.p_gpu)
            self.lin_e_arg.append(sim.t_gpu)
            self.lin_e_arg.append(np.float64(lat.dtau))
            self.lin_e_arg.append(np.int32(sim.steps))
            self.lin_e_arg.append(sim.k2_bins_gpu)

            grid_lin = len(sim.k2_bins_gpu)/lat.cuda_lin_block[0]

            self.cuda_param_lin_e = dict(block=lat.cuda_lin_block,
                                         grid = (grid_lin,1),
                                         stream = sim.stream)

        "Cuda function arguments used in rho and pressure kernels:"
        self.rp_arg = [sim.rho_gpu, sim.pres_gpu, sim.rhosum_gpu,
                       sim.inter_sum_gpu]
        for f in sim.fields:
            self.rp_arg.append(f.f_gpu)
        for f in sim.fields:
            self.rp_arg.append(f.pi_gpu)
        for f in sim.fields:
            self.rp_arg.append(f.rho_sum_gpu)
        for f in sim.fields:
            self.rp_arg.append(f.pres_sum_gpu)
        if lat.field_rho:
            for f in sim.fields:
                self.rp_arg.append(f.rho_gpu)

        self.cuda_param_rp = dict(block=lat.cuda_block_2, grid=lat.cuda_grid)


    def print_id(self, array_type):
        """Print ids of the arrays in different cuda_args. This can be used to
           verify that the Cuda functions are pointing to correct arrays."""
        if array_type == 'evo':
            res = [id(x) for x in self.cuda_arg]
        elif array_type == 'rp':
            res = [id(x) for x in self.rp_arg]
        return res

    def evo_step_2(self, lat, V, sim, dt):
        "Integrator order = 2"
        evo_step_2(lat, V, sim, self.H2_kernels, self.H3_kernels,
                   self.cuda_param_H2, self.cuda_param_H3,
                   self.cuda_arg, dt)
        sim.add_to_lists(lat)

    def evo_step_4(self, lat, V, sim, dt):
        "Integrator order = 4"
        evo_step_4(lat, V, sim, self.H2_kernels, self.H3_kernels,
                   self.cuda_param_H2, self.cuda_param_H3,
                   self.cuda_arg, dt)
        sim.add_to_lists(lat)

    def evo_step_6(self, lat, V, sim, dt):
        "Integrator order = 6"
        evo_step_6(lat, V, sim, self.H2_kernels, self.H3_kernels,
                   self.cuda_param_H2, self.cuda_param_H3,
                   self.cuda_arg, dt)
        sim.add_to_lists(lat)

    def lin_evo_step(self, lat, V, sim):
        lin_step(lat, V, sim, self.lin_evo_kernel, self.lin_e_arg,
                 self.cuda_param_lin_e)

        "Update values in host memory:" 
        sim.a = sim.a_gpu.get().item()
        sim.p = sim.p_gpu.get().item()
        sim.t = sim.t_gpu.get().item()

        sim.a_list.append(sim.a)
        sim.p_list.append(sim.p)
        sim.t_list.append(sim.t)
        sim.H_list.append(-sim.p/(6*sim.a**2.*lat.VL_reduced))

        for field in sim.fields:
            field.f0 = field.f0_gpu.get().item()
            field.pi0 = field.pi0_gpu.get().item()

            field.f0_list.append(field.f0)
            field.pi0_list.append(field.pi0)

    def transform(self, lat, sim):
        """Evolve the linear perturbations of the fields with
           the solutions of initial value problems f_{i}=1, pi_{i}=0
           and f_{i}=0, pi_{i}=1:"""

        args = []
        for field in sim.fields:
            args.append(field.f_gpu)
        for field in sim.fields:
            args.append(field.pi_gpu)
        for field in sim.fields:
            args.append(field.f_lin_01_gpu)
        for field in sim.fields:
            args.append(field.pi_lin_01_gpu)
        for field in sim.fields:
            args.append(field.f_lin_10_gpu)
        for field in sim.fields:
            args.append(field.pi_lin_10_gpu)
        args.append(sim.k2_bin_id)

        params = dict(block=lat.cuda_block_1, grid=lat.cuda_grid,
                      stream = sim.stream)

        self.lin_evo_kernel.lin_field_evo(*args, **params)

    def k_to_x_space(self, lat, sim, unperturb = False):
        """Transform perturbed fields from Fourier space to unperturbed fields
           in position space:"""
        for field in sim.fields:
            field.ifft()
        if unperturb:
            for field in sim.fields:
                field.unperturb_field()

        self.update(lat, sim)

    def x_to_k_space(self, lat, sim, perturb = False):
        """Transform unperturbed fields in position space to perturbed fields
           in Fourier space:"""
        if perturb:
            for field in sim.fields:
                field.perturb_field()

        for field in sim.fields:
            field.fft()

        self.update(lat, sim)

    def calc_rho_pres(self, lat, V, sim, print_Q = True, print_w = False,
                      flush = True):
        """Perform energy density and pressure calculations of the homogeneous
        field variables:"""
        calc_rho_pres(lat, V, sim,
                      self.rp_kernels, self.cuda_param_rp, self.rp_arg,
                      self.sc_kernel, self.cuda_param_sc, self.sc_arg,
                      print_Q, print_w, flush)

    def calc_rho_pres_back(self, lat, V, sim, print_Q = True, flush = True):
        "Perform energy density and pressure calculations:"
        calc_rho_pres_back(lat, V, sim, print_Q, flush)


###############################################################################
# Energy-density and pressure codes
###############################################################################

def calc_rho_pres(lat, V, sim, rp_list, cuda_param_rp, cuda_args,
                  corr_kernel, cuda_param_sc, cuda_sc_args,
                  print_Q, print_w=False, flush=True):
    "This function updates the energy density and the pressure fields."

    a = sim.a
    p = sim.p
    i0 = sim.i0
    VL = lat.VL
    t = sim.t
    rho_r0 = sim.rho_r0
    rho_m0 = sim.rho_m0

    sim.g_array[:] = np.concatenate([V.g_array(lat, sim.a),
                             V.C_coeffs_np])[:]

    for kernel in rp_list:
        kernel.update_g(sim.g_array, sim.stream)
        kernel.calc(*cuda_args, **cuda_param_rp)

    sim.stream.synchronize()

    "Total energy density of the system:"
    cuda.memcpy_dtoh_async(sim.rhosum_host, sim.rhosum_gpu.gpudata, sim.stream)

    "Inter action energy density:"
    cuda.memcpy_dtoh_async(sim.inter_sum_host,
                           sim.inter_sum_gpu.gpudata, sim.stream)

    sim.stream.synchronize()

    "Calculate average energy densities:"


    rho_tot = sum(sum(sim.rhosum_host))/VL + rho_m0/a**3.0 + rho_r0/a**4.0

    rho_inter = sum(sum(sim.inter_sum_host))/VL
    
    sim.rho = rho_tot
    sim.H = (-p/(6*a**2.*lat.VL_reduced))

    "Total energy densities of the fields without the interaction terms:"
    field_rho_avgs = [sum(sum(x.rho_sum_gpu.get()))/VL for x in sim.fields]
    omega_f = [x/rho_tot for x in field_rho_avgs]

    "Equations of state w = P/rho:"
    w = [sum(sum(x.pres_sum_gpu.get()))/sum(sum(x.rho_sum_gpu.get()))
         for x in sim.fields]

    "Radiation and matter energy density fractions:"
    omega_rad = (rho_r0/a**4.0)/rho_tot
    omega_mat = (rho_m0/a**3.0)/rho_tot

    "Energy density fraction of interaction terms:"
    omega_int = rho_inter/rho_tot
    
    Fried_1 = a**2.*((sim.H)**2.- lat.mpl**2.*rho_tot/3.0)
    num_error_rel = Fried_1/(a**2.*sim.H**2.)


    "Calculate spatial correlation length:"
    corr_kernel.calc(*cuda_sc_args, **cuda_param_sc)

    sim.stream.synchronize()

    "Total energy density of the system:"
    cuda.memcpy_dtoh_async(sim.sum_nabla_rho_h,
                           sim.sum_nabla_rho_gpu.gpudata,
                           sim.stream)

    "Total energy density of the system:"
    cuda.memcpy_dtoh_async(sim.sum_rho_squ_host,
                           sim.sum_rho_squ_gpu.gpudata,
                           sim.stream)

    sim.stream.synchronize()
    
    lp = np.sqrt(sum(sum(sim.sum_rho_squ_host))/
                 sum(sum(sim.sum_nabla_rho_h)))*lat.m

    if lat.field_rho and lat.field_lp:
        for field in sim.fields:
            corr_kernel.calc(field.rho_gpu,
                             field.sum_nabla_rho_gpu,
                             field.sum_rho_squ_gpu,
                             **cuda_param_sc)

            sim.stream.synchronize()

            "Total energy density of the system:"
            cuda.memcpy_dtoh_async(field.sum_nabla_rho_h,
                           field.sum_nabla_rho_gpu.gpudata,
                           sim.stream)

            "Total energy density of the system:"
            cuda.memcpy_dtoh_async(field.sum_rho_squ_h,
                           field.sum_rho_squ_gpu.gpudata,
                           sim.stream)

            sim.stream.synchronize()
        
            lp_field = np.sqrt(sum(sum(field.sum_rho_squ_h))/
                               sum(sum(field.sum_nabla_rho_h)))*lat.m

            if flush:
                field.lp_list.append(lp_field)


    if flush:

        "Append the values to flush lists:"
        sim.flush_t.append(t)
        sim.flush_a.append(a)
        sim.flush_p.append(p/VL)
        sim.flush_H.append(sim.H)
        sim.fried_1.append(Fried_1)
        sim.k_error.append(num_error_rel)

        sim.omega_rad_list.append(omega_rad)
        sim.omega_mat_list.append(omega_mat)

        i = 0
        for field in sim.fields:
            field.w_list.append(w[i])
            field.omega_list.append(omega_f[i])

            i += 1
        
        sim.omega_int_list.append(omega_int)

        sim.lp_list.append(lp)

    if print_Q == True:
        values = [i0, Fried_1, num_error_rel, lat.m*sim.t, sim.a,
                  p/VL]
        print ('i0 {0} rho-error {1:5} k/(a^2H^2) {2:5} t [1/m] {3:5}'+
               ' a {4:5} p/VL {5:5}').format(*values)

    if print_w:
        print 'Ω_field {0}, Ω_γ {1}, Ω_m {2}'.format(omega_f,
                                                     omega_rad,
                                                     omega_mat)

        print  'Equations of state', w

def calc_rho_pres_back(lat, V, sim, print_Q, flush=True):
    """This function updates the background energy density for
       linear evolution:"""

    a = sim.a
    p = sim.p
    i0 = sim.i0
    VL = lat.VL
    rho_r0 = sim.rho_r0
    rho_m0 = sim.rho_m0

    rho0 = 0
    for field in sim.fields:
        rho0 += 0.5*(field.pi0)**2./(a**6.)

    f0 = [field.f0 for field in sim.fields]
    
    rho0 += sim.V(*f0)

    rho0 += rho_m0/a**3.0 + rho_r0/a**4.0

    sim.rho_0 = rho0

    sim.H = (-p/(6*a**2.*lat.VL_reduced))

    Fried_1 = a**2.*((sim.H)**2. -
                     lat.mpl**2.*(rho0)/3.0)
    num_error_rel = Fried_1/(a**2.*sim.H**2.)

    if print_Q == True:
        values = [i0, Fried_1, num_error_rel, lat.m*sim.t, sim.a,
                  p/VL]
        print ('i0 {0} rho-error {1:5} k/(a^2H^2) {2:5} t [1/m] {3:5}'+
               ' a {4:5} p/VL {5:5}').format(*values)

def rho_field(lat, V, a, pis, fields):

    rho0 = 0.0
    V = V_func(lat, V)

    for pi in pis:
        rho0 += 0.5*(pi)**2./(a**6.)

    rho0 += V(*fields)

    return rho0

###############################################################################
# Non-linear Evolution codes
###############################################################################

def H1_step(lat, sim, dt):
    """The integrator related to H1 part of the Hamiltonian function
    in conformal time."""

    a0 = sim.a
    p0 = sim.p

    sim.a = a0 - p0/(6.*lat.VL_reduced)*dt

def H2_step1(lat, sim, H2_list, cuda_args, cuda_param_H2, dt):
    """This function is written by write_integrator.py"""

    H2_list[0].evo(*cuda_args, **cuda_param_H2)

    sim.p += -lat.VL*sim.rho_m0*dt

def H2_step2(lat, sim, H2_list, cuda_args, cuda_param_H2, dt):
    """This function is written by write_integrator.py"""

    H2_list[1].evo(*cuda_args, **cuda_param_H2)

    cuda.memcpy_dtoh_async(sim.sum_host, sim.sum_gpu.gpudata, sim.stream)
    sim.stream.synchronize()

    sim.p += sum(sum(sim.sum_host)) - lat.VL*sim.rho_m0*(dt)
    #sim.p += sum(sum(sim.sum_gpu.get())) - lat.VL*sim.rho_m0*(2*dt)

def H3_step(lat, V, sim, H3_list, cuda_args, cuda_param_H3, dt):
    """This function is written by write_integrator.py"""

    for kernel in H3_list:
        kernel.evo(*cuda_args, **cuda_param_H3)

    sim.t += sim.a*dt

def evo_step_2(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, dt):
    "Second-order time evolution step"

    H1_step(lat, sim, dt/2)

    sim.h_array[:] = V.h_array(lat, sim.a, dt/2)[:]

    for kernel in H2_list:
        kernel.update_h(sim.h_array, sim.stream)

    sim.f_array[:] = np.concatenate([V.f_array(lat, sim.a, dt),
                             sim.a**3.*dt*V.C_coeffs_np])[:]

    for kernel in H3_list:
        kernel.update_f(sim.f_array, sim.stream)

    sim.stream.synchronize()

    H2_step1(lat, sim, H2_list, cuda_args, cuda_param_H2, dt/2)
    H3_step(lat, V, sim, H3_list, cuda_args, cuda_param_H3, dt)
    H2_step2(lat, sim, H2_list, cuda_args, cuda_param_H2, dt/2)

    H1_step(lat, sim, dt/2)

    #sim.t += sim.a*dt
    sim.H = -sim.p/(6*sim.a)

def evo_step_4(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, dt):
    "Fourth-order time evolution step:"
    k = 4.
    l = 1.0/(k-1)
    c1 = 1.0/(2.0 - 2.0**l)
    c0 = 1.0 - 2.0*c1

    evo_step_2(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, c1*dt)
    evo_step_2(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, c0*dt)
    evo_step_2(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, c1*dt)

def evo_step_6_slow(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, dt):
    "Sixth-order time evolution step:"
    k = 6.
    l = 1.0/(k-1)
    c1 = 1.0/(2.0 - 2.0**l)
    c0 = 1.0 - 2.0*c1


    evo_step_4(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, c1*dt)
    evo_step_4(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, c0*dt)
    evo_step_4(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, c1*dt)

def evo_step_6(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, dt):
    """Sixth-order time evolution step.
       w_i values taken from B. Leimkuhler and S. Reich: Simulating Hamiltonian
       Dynamics."""

    w1 = 0.78451361047755726382
    w2 = 0.23557321335935813368
    w3 = -1.17767998417887100695
    w4 = 1 - 2*(w1+w2+w3)

    evo_step_2(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, w1*dt)
    evo_step_2(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, w2*dt)
    evo_step_2(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, w3*dt)
    evo_step_2(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, w4*dt)
    evo_step_2(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, w3*dt)
    evo_step_2(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, w2*dt)
    evo_step_2(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, w1*dt)

def evo_step_8_slow(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, dt):
    "Eight-order time evolution step:"
    k = 8.
    l = 1.0/(k-1)
    c1 = 1.0/(2.0 - 2.0**l)
    c0 = 1.0 - 2.0*c1

    evo_step_6(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, c1*dt)
    evo_step_6(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, c0*dt)
    evo_step_6(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, c1*dt)

def evo_step_8(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, dt):
    """Eight-order time evolution step.
       w_i values taken from B. Leimkuhler and S. Reich: Simulating Hamiltonian
       Dynamics."""

    w1 = 0.74167036435061295345
    w2 = -0.40910082580003159400
    w3 = 0.19075471029623837995
    w4 = -0.57386247111608226666
    w5 = 0.29906418130365592384
    w6 = 0.33462491824529818378
    w7 = 0.31529309239676659663
    w8 = 1 - 2*(w1+w2+w3+w4+w5+w6+w7)

    evo_step_2(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, w1*dt)
    evo_step_2(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, w2*dt)
    evo_step_2(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, w3*dt)
    evo_step_2(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, w4*dt)
    evo_step_2(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, w5*dt)
    evo_step_2(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, w6*dt)
    evo_step_2(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, w7*dt)
    evo_step_2(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, w8*dt)
    evo_step_2(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, w7*dt)
    evo_step_2(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, w6*dt)
    evo_step_2(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, w5*dt)
    evo_step_2(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, w4*dt)
    evo_step_2(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, w3*dt)
    evo_step_2(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, w2*dt)
    evo_step_2(lat, V, sim, H2_list, H3_list, cuda_param_H2, cuda_param_H3,
               cuda_args, w1*dt)


###############################################################################
# Linearized Evolution codes
###############################################################################

def lin_step(lat, V, sim, lin_evo_kernel, lin_args, cuda_param_lin_evo):

    lin_evo_kernel.evo(*lin_args, **cuda_param_lin_evo)
    