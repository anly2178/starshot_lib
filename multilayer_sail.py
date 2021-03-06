from Starshot.sail import Sail
from Starshot.tmm.tmm import tmm
from Starshot.materials.save_load_mat import load_material
import scipy
import scipy.integrate as integrate
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from numpy import sin, cos, pi
from copy import deepcopy

class MultilayerSail(Sail):
    """
    Multilayer lightsails.
    ...
    Attributes
    ----------

    name : str
        A name or code that identifies the sail
    mass : float
        Mass of lightsail (excluding payload) [kg]
    area : float
        Area of lightsail [m^2]
    radius : float
        Radius of lightsail [m]
    s_density : float
        Surface density of lightsail [kg/m^2]
    reflectance : float
        Absolute reflectance of lightsail
    transmittance : float
        Absolute transmittance of lightsail
    target : float
        Target speed as fraction of speed of light. E.g. 0.2c
    power : float
        Laser power [W]
    wavelength : float
        Laser wavelength [m]
    W : float
        Figure of merit; the square root of 'Reflectivity-adjusted-area-density'
        as defined by Ilic et al. (2018) [sqrt(g)/m]
    diameter : float
        Diameter of laser array [m]
    angles_coeffs : list of tuples of three floats
        Angle [degrees], reflection efficiency and transmission efficiency of each order.
    materials : list of str
        List of strings representing the materials in each layer
    thickness : list (of floats)
        Thickness of layers [m]
    max_temp : float
        Maximum temperature of sail [K]
    abs_coeff : float
        Absorption coefficient of lightsail. [cm^-1]
    absorptance : float
        Absolute absorption of lightsail
    Methods (for user)
    ------------------
    def __init__(   name=None, materials=None, mass=None, thickness=None,
                    area=None, radius=None, s_density=None, abs_coeff=None,
                    absorptance=None, reflectance=None, transmittance=None,
                    W=None):
        The constructor for Sail class
    print_variables()
        Prints the variables of the sail
    change_variables()
        Change the variables of the sail
    calculate_mission()
        Calculates the mission scenario, including distance vs speed vs time.
        A folder is created with 2 txt files and 1 png file.
        1 txt file includes distance, speed and time results, the other txt file
        includes the variables of the mission. The png file includes
        speed vs distance and speed vs time graphs.
    """
    def __init__(   self, name=None, materials=None, mass=None, thickness=None, area=None,
                    target=0.2, max_Starchip_temp=1000, power=None, wavelength=1.064e-6):
        """The constructor for MultilayerSail class
        Parameters
        ----------
        name : str
            A name or code that identifies the sail
        materials : list of str
            List of strings representing the materials in each layer
        mass : float
            Mass of lightsail (excluding payload) [kg]
        thickness : list (of floats)
            Thickness of layers [m]
        area : float
            Area of lightsail [m^2]
        reflectance : float
            Absolute reflectance of lightsail
        target : float
            Target speed as fraction of speed of light. E.g. 0.2c
        max_Starchip_temp : float
            Maximum temperature of sail payload [K]
        power : float
            Laser power [W]
        wavelength : float
            Laser wavelength [m]
        Returns
        -------
        MultilayerSail
            MultilayerSail with variables specified by user
        """
        if materials is None:
            raise ValueError("Enter material(s)")
        self.materials = materials
        if thickness is None:
            raise ValueError("Enter thickness(es)")
        self.thickness = thickness #m
        self.s_density = self._find_SA_density()
        if area is None and mass is None:
            raise ValueError("Enter mass and/or area")
        elif area is None:
            area = mass / self.s_density
        elif mass is None:
            mass = area * self.s_density
        reflectance = None #To pass into sail constructor.
        super().__init__(name, mass, area, reflectance, target, power, wavelength)
        self.max_Starchip_temp = max_Starchip_temp #K
        self.absorptance = self._find_absorptance()
        if self.power is None:
            self.power = self._find_max_power() #Estimate max power that sail can use.
            self.temp_reached = min([mat.get_max_temp() for mat in self._material_objects()] + [self.max_Starchip_temp])
        else:
            print('Calculating temperature...')
            self.temp_reached = self._find_eq_temps_given_abs_coeff()
            print(f'Temperature reached = {self.temp_reached}')
        if self.reflectance is None:
            self.reflectance = self._find_reflectance()
        if self.transmittance is None:
            self.transmittance = self._find_transmittance()
        self.angles_coeffs = [(0, self.reflectance, self.transmittance)]
        self.W = self._find_W()
        self.diameter = self._find_diameter()
        self._reorder_vars()
        self.print_variables()

    def _reorder_vars(self):
        """Reorder variables to make it print nicer"""
        old_vars = vars(self)
        new_order = ['name','mass','area','radius','materials','thickness','s_density',
        'absorptance', 'reflectance','transmittance', 'angles_coeffs','target','power',
        'wavelength', 'diameter', 'W','max_Starchip_temp', 'temp_reached']
        new_vars = {lab: old_vars[lab] for lab in new_order}
        self.__dict__ = new_vars

    def _material_objects(self):
        """Convert list of material tags to material objects"""
        try:
            mats = [load_material(mat) for mat in self.materials]
        except ValueError:
            raise ValueError('Check that materials have been initialised and saved in saved_materials')
        return mats


    def _find_structure(self, wavelength = None):
        """Creates a list representing the structure of the MultilayerSail.
        Parameters
        ----------
        None required
        Returns
        -------
        list of tuples of two floats
            [(refractive index, -thickness [m]), ...]
        """
        if wavelength == None:
            wavelength = self.wavelength
        structure = []
        for material, thickness in zip(self._material_objects(), self.thickness):
            structure.append( (material.get_n(wavelength) + 1j*material.get_k(wavelength), -thickness) )
        return structure

    def _find_SA_density(self):
        """ Determines the surface area density of the sail given its structure
            and mass densities of each material
            Parameters
            ----------
            None required
            Returns
            ----------
            float
                surface area density [kg m-2]
        """
        SA_density = 0
        for material, thickness in zip(self._material_objects(), self.thickness):
            SA_density += material.get_density()*thickness
        return SA_density

    def _find_absorptance(self, wavelength = None):
        """Calculates absorptance of MultilayerSail based on the (expected)
        absorption coefficients of the sail materials (material.abs_coeff
        attribute) and a wavelength being analysed within the laser bandwidth.
        Assumes the absorption coefficient is constant over the laser range
        in the near IR. Usage of absorption coefficient in the laser bandwidth
        is due to extinction coefficients for most materials not being well
        established in this range. Further, results for extinction and
        absorption coefficients may vary depending on purity and manufacture of
        materials.
        Parameters
        ----------
        float (optional)
            wavelength [m]
        Returns
        -------
        float
            Absorptance of MultilayerSail
        """
        if wavelength is None:
            wavelength = self.wavelength
        structure_near_IR = []
        for material, thickness in zip(self._material_objects(), self.thickness):
            k = 1j*wavelength*100*material.get_abs_coeff()/(4*pi)   # conversion from abs_coeff to extinction coeff
            structure_near_IR.append( (material.get_n(wavelength) + k, -thickness) )

        r_p, t_p, r_s, t_s = tmm(structure_near_IR, wavelength, 0)

        R = ((r_p*np.conj(r_p) + r_s*np.conj(r_s))/2).real
        T = ((t_p*np.conj(t_p) + t_s*np.conj(t_s))/2).real
        A = 1 - R - T
        return A

    def _find_reflectance(self):
        """Calculates reflectance of MultilayerSail, averaged over wavelength.
        Parameters
        ----------
        None required
        Returns
        -------
        float
            Reflectance of MultilayerSail
        """
        #Get parameters
        wavelength = self.wavelength
        target = self.target
        structure = self._find_structure()
        shift = np.sqrt((1+target)/(1-target))
        bandwidth = np.linspace(wavelength, wavelength*shift, 100)
        R_all = []
        for b in bandwidth:
            r_p, _, r_s, _ = tmm(structure, b, 0)
            R_all.append( ((r_p*np.conj(r_p) + r_s*np.conj(r_s))/2) )
        R_avg = (sum(R_all)/100).real
        return R_avg

    def _find_transmittance(self):
        """Calculates transmittance of MultilayerSail, averaged over wavelength.
        Parameters
        ----------
        None required
        Returns
        -------
        float
            Transmittance of MultilayerSail
        """
        #Get parameters
        wavelength = self.wavelength
        target = self.target
        structure = self._find_structure()
        shift = np.sqrt((1+target)/(1-target))
        bandwidth = np.linspace(wavelength, wavelength*shift, 100)
        T_all = []
        for b in bandwidth:
            _, t_p, _, t_s = tmm(structure, b, 0)
            T_all.append( ((t_p*np.conj(t_p) + t_s*np.conj(t_s))/2) )
        T_avg = (sum(T_all)/100).real
        return T_avg

    def _spectral_power_flux(self, wavelength, temperature, points_in_integration = 50):

        """ Finds the spectral power flux of an "ideal" (perfectly flat and smooth)
        sail. This is the energy emitted per unit area at given wavelength.
        Accounts for asymmetric multilayer_sails
        (along the axis of the incident laser light)

        Uses trapezoidal rule to integrate power emitted at all angles to
        produce the spectral power flux

        Parameters
        ----------
        float
            wavelength [m]
        float
            temperature [m]
        int
            points_in_integration
                - this is the number of points used in the trapezoidal rule
                  integration
        Returns
        -------
        float
            emissivity in direction described by angle and sail structure
        """

        def _directional_emissivity(sail, angle, wavelength, front_or_back):
            """ Calculates the directional emissivity of a given multilayer_sail
                structure based on a wavelength (float) and incident angle (i.e.
                angle of elevation). This assumes the sail is perfectly smooth and
                the structure is radially symmetric along the surface of the sail at
                each point of the sail.
                Parameters
                ----------
                float
                    angle [radians]
                float
                    wavelength [m]
                string
                    front_or_back
                        - denotes whether we are calculating the directional
                          emissivity of the front or back face of the sail
                Returns
                -------
                float
                    emissivity in direction described by angle and sail structure
            """
            # Creates a new structure list that is based on calculated optical constants using wavelength
            if front_or_back == 'front':
                structure = self._find_structure(wavelength)
            elif front_or_back == 'back':
                structure = self._find_structure(wavelength)
                structure.reverse()

            # This block gives an expression for emissivity in terms of theta (and wavelength)
            # First set out by finding the reflectance and transmittance of structure at
            # this wavelength and angle
            r_p, t_p, r_s, t_s = tmm(structure, wavelength, theta)
            R = ( r_p*np.conj(r_p) + r_s*np.conj(r_s) )/2
            T = ( t_p*np.conj(t_p) + t_s*np.conj(t_s) )/2
            dEpsilon = (1-R-T)
            return dEpsilon.real

        # First, give expression for radiation emitted by a black body
        h = 6.62607004e-34       # Planck's constant in SI
        c = 299792458             # speed of light in SI
        k_B = 1.38064852e-23        # Boltzmann constant in SI
        I = ((2*h*c**2)/wavelength**5)*(1/(np.exp(h*c/(wavelength*k_B*temperature))-1))         # Planck's Law

        # Now give expression for hemispherical emissivity. Note factor of 2: 2 comes
        # from integrating wrt phi (the azimuth)
        bounds = np.linspace(0,pi/2,points_in_integration)

        # Use trapezoidal integration to speed things up
        direc_ems = points_in_integration*[None]
        i = 0
        for theta in bounds:
            direc_ems[i] = (2*_directional_emissivity(self, theta, wavelength, 'front')*cos(theta)*sin(theta))
            i += 1
        # In the below line, note that the integration returns the spectral hemispherical emissivity
        front_power_flux = pi*I*np.trapz(direc_ems, bounds, pi/2/points_in_integration)

        # SECOND TIME FOR BACK FACE
        direc_ems = points_in_integration   *[None]
        i = 0
        for theta in bounds:
            direc_ems[i] = (2*_directional_emissivity(self, theta, wavelength, 'back')*cos(theta)*sin(theta))
            i += 1
        back_power_flux = pi*I*np.trapz(direc_ems, bounds, pi/2/points_in_integration)

        power_flux = front_power_flux + back_power_flux
        return power_flux

    def _find_eq_temps_given_abs_coeff(self):
        """ Determines the maximum equilibrium temperature of the sail given
            the absorption coefficients of each material in the sail.
            If any of the materials do not have an allocated absorption
            coefficient, will raise an exception.
            Parameters
            ----------
            None required
            Returns
            -------
            float
                equilibrium temperature [K]
        """
        initial_wavelength = self.wavelength        # laser wavelength
        target = self.target

        # Below block of code finds the maximum power absorbed by the sail throughout its journey
        betas = np.linspace(0,target,100)  # fraction of speed of light sail is travelling at
        power_absorbed = 0       # need to find maximum p_in based on beta
        power_mass_ratio = self.power/self.mass     # laser power to mass ratio of sail
        s_density = self.s_density         # surface area density

        # Loop that gets the maximum power value
        for beta in betas:
            wavelength = initial_wavelength*np.sqrt((1+beta)/(1-beta))
            A = self._find_absorptance(wavelength)

            # Finding the LHS of Atwater et al. 2018's  equation
            power_beta = power_mass_ratio*A*s_density*(1-beta)/(1+beta)       # power absorbed when v/c = beta

            if power_beta > power_absorbed:
                power_absorbed = power_beta     # since maximum power in results in highest equilibrium temperature

        def power_in_minus_out(T, power_absorbed):
            """ Uses an input temperature to find the total power emitted by the
                sail per unit sail area. Subtracts this value from the power absorbed, given as input.
                Roots occur when the power in = power out, and hence at thermal
                equilibrium.
                Parameters
                ----------
                float
                    T(emperature) [K]
                float
                    power_absorbed []
                Returns
                ----------
                float
                    difference []
                        - difference between power_absorbed and power_emitted
            """

            def find_power_emitted(T, points_in_integration = 100, integration_range = [1e-6, 25e-6]):
                """ Finds the power emitted by a sail with given structure at a
                    specific temperature. Determnied by performing a trapezoidal
                    integration over a (default 1-25 micron) wavelength range of the
                    spectral power flux, calculated by the _spectral_power_flux()
                    method.
                    Parameters
                    ----------
                    float
                        T(emperature) [K]
                    int (optional)
                        points_in_integration
                            - number of points used in trapezoidal integration
                    list/tuple (optional)
                        integration_range
                            - wavelength range over which spectral power flux
                              is integrated over to determine total power per
                              unit area of sail emitted (note the area of the
                              sail in this respect is the area of one face,
                              NOT the surface area = 2 * sail area)
                    Returns
                    ----------
                    float
                        power_emitted []
                """
                lower_bound, upper_bound = integration_range
                points = np.linspace(lower_bound, upper_bound, points_in_integration)
                # Calling _spectral_power_flux at each point and adding to the list for integration
                power_out_at_wl = [self._spectral_power_flux(wavelength,T) for wavelength in points]
                power_emitted = np.trapz(power_out_at_wl, points, (upper_bound - lower_bound)/points_in_integration)
                return power_emitted

            return power_absorbed - find_power_emitted(T)

        # The zero of the _power_in_minus_out function occurs when the sail is at
        # equilibrium temperature. Hence, we can use Newton's method to estimate
        # this temperature

        # Use the starting point of Newton's method as the black body temperature
        # given the power_absorbed (per unit area)

        bb_temp = (power_absorbed/(2*1*5.67e-8))**0.25
        a = bb_temp         # Beginning of interval for Brent's method
        b = bb_temp*2       # End of interval for Brent's method

        # Since we don't accurately know where the temperature lies, set b to be
        # initially twice the temperature of a black body. If the root does not
        # lie in the interval [a,b], then the below block of code will
        # work to double b until the root does lie within [a,b] (that is,
        # the function has different signs at a and b)
        solved = False

        while not solved:
            try:
                eq_temp = scipy.optimize.brentq(power_in_minus_out, a, b, args = [(power_absorbed)])
                solved = True
            except ValueError:
                b = b*2
                solved = False

        return eq_temp

    def _find_max_power(self):
        """Find the highest power the MultilayerSail can be subject to."""
        max_temp = min([mat.get_max_temp() for mat in self._material_objects()] + [self.max_Starchip_temp]) #max temp the sail can endure
        print('Finding max power...')
        print(f'Maximum temp the sail can be subject to = {max_temp} K')
        copied_sail = deepcopy(self) #To protect from changing variables accidentally
        #Define function to solve.
        def f(P, multisail, max_temp):
            multisail.power = P
            temp = multisail._find_eq_temps_given_abs_coeff()
            print(f'At power = {P * 1e-9:.2f} GW, equilibrium temperature = {temp:.2f} K')
            return temp - max_temp

        max_power = scipy.optimize.newton(f, 100e9, args=(copied_sail, max_temp), tol=1e9)
        return max_power
