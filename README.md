# Starshot

A Python library for the Starshot initiative.

![](images/cool_image.png)
* Credit: Atwater et al. (2018)

## Description

The Breakthrough Starshot Initiative aims to accelerate an ultralight spacecraft to 20% of the speed of light, reaching Proxima Centauri in approximately 20 years. The spacecraft would consist of a low-density ‘lightsail’ and a payload which contains the electronics responsible for transmitting data back to Earth (Atwater et al. 2018). The lightsail would be remotely propelled by radiation pressure, using an Earth-based laser array operating in the near-infrared spectral range.

## Assumptions

* Flat, circular lightsail
* Mass of payload is equal to the mass of the lightsail; the optimal mass condition (Kulkarni 2018)
* Circular laser array emits a Gaussian beam
* Beam is focused so that the beam waist tracks the lightsail, and the beam waist is as small as diffraction allows
* Beam strikes and reflects off lightsail orthogonally
* Heat transfer between layers of multilayer sail is instantaneous
* Special relativity is taken into account

## Installation

* Clone this repo to your local machine using [https://github.com/anly2178/Starshot.git](https://github.com/anly2178/Starshot.git)
* Install the Python module [Dill](https://pypi.org/project/dill/) (required for saving and loading)

### Setup

The directory tree should appear like this:

```bash
root
├── test.py
├── saved_materials
└── Starshot
    ├── README.md
    ├── __pycache__
    ├── __init__.py
    ├── sail.py
    ├── multilayer_sail.py
    ├── diffractive_sail.py
    ├── motion.py
    ├── gaussbeam.py
    ├── results.py
    ├── gaussbeam.py
    ├── motion.py
    ├── materials
    │   ├── README.txt
    │   ├── __pycache__
    │   ├── material.py
    │   └── save_load_mat.py
    └── tmm
        ├── __pycache__
        ├── tmm.py
        └── make_transfer_matrix.py
```
* Starshot directory is downloaded from github.

* test.py is to be created by the user. It is the script that the user runs.
The user may name the script something else. It is important that the script
is located parallel to the Starshot directory.

* saved_materials is automatically created when the user initialises a Material object.

## Usage

**To initialise a new** ```Material```:

```python
from Starshot.materials.material import Material

new_material = Material(name=insert_name, density=insert_density, n_list=insert_n_list, k_list=insert_k_list)
```
* For more detail, see the Material section.

**To initialise a new** ```Sail```:

```python
from Starshot.sail import Sail

new_sail = Sail(name=insert_name, mass=insert_mass, area=insert_area, reflectance=insert_reflectance,
  target=insert_target, power=insert_power, wavelength=insert_wavelength)
```
* For more detail, see the Sail section.

**To initialise a new** ```MultilayerSail```:

```python
from Starshot.multilayer_sail import MultilayerSail

new_multi = MultilayerSail(name=insert_name, materials=insert_materials, mass=insert_mass,
  thickness=insert_thickness, reflectance=insert_reflectance, target=insert_target,
  max_Starchip_temp=insert_max_temp, power=insert_power, wavelength=insert_wavelength)
```
* For more detail, see the Multilayer Sail section.

**To calculate mission scenario**:

```python
sail_name.calculate_mission()
```

*Note*: The ```DiffractiveSail``` class will be included when it is in a useful state.

## Sail

The ```Sail``` class is the superclass for all subclasses of sails, such as ```MultilayerSail``` and ```DiffractiveSail```. Therefore, these subclasses inherit the ```Sail``` attributes and methods.
* Sail is flat and circular. Generalising the shape is to be completed.
* Gaussian beam is produced by circular laser array.

### Attributes

* *name* (str) - a unique name or code that identifies the sail. Defaults to None.
* *mass* (float) [kg] - mass of lightsail (*excluding payload*). It is assumed that payload mass equals to lightsail mass as per optimal mass condition (Kulkarni 2018). Defaults to None.
* *area* (float) [m^2] - surface area of lightsail on one side. Defaults to None.
* *radius* (float) [m] - radius of lightsail.
* *s_density* (float) [kg/m^2] - surface density of lightsail.
* *reflectance* (float) - fraction of incident power that is reflected by lighsail.
* *transmittace* (float) - fraction of incident power that is transmitted through lightsail.
* *target* (float) - target speed as fraction of speed of light. Defaults to 0.2c.
* *power* (float) [W] - power of laser array. Defaults to None.
* *wavelength* (float) [m] - laser wavelength, not Doppler-shifted. Defaults to 1.064e-6 m.
* *W* (float) [sqrt(g)/m] - square root of 'reflectivity-adjusted-area-density' as defined by Ilic et al. (2018).
* *diameter* (float) [m] - diameter of circular laser array.
* *angles_coeffs* (list of tuples of three floats) - angle [degrees], reflection efficiency and transmission efficiency of each order.

### Methods

```python
__init__(   self, name=None, mass=None, area=None, reflectance=None,
                  target=0.2, power=None, wavelength=1.064e-6)
```
* Constructor for ```Sail``` class

```python
calculate_mission()
```
* Calculates the mission scenario, including distance, speed and time.
* A folder is created with 2 txt files and 1 png file. ```trajectory.txt``` file includes distance, speed and time results. ```variables.txt``` file includes the variables of the mission. ```plots.png``` file includes speed vs distance and speed vs time graphs.

## Multilayer Sail

The ```MultilayerSail``` class is a subclass of ```Sail```. It includes sails with 1 or more layered materials.

### Attributes

* *materials* (list of str) - list of strings representing the materials in each layer, starting from the layer closest to the laser array. The tag for each material is its chemical formula, or as defined by the user.
* *thickness* (list of floats) [m] - list of the thicknesses of each layer, starting from the layer closest to the laser array.
* *max_Starchip_temp* (float) [K] - maximum temperature of payload. Defaults to 1000 K.
* *absorptance* (float) - fraction of incident power absorbed by lightsail.

*Note*: The ```MultilayerSail``` class inherits the attributes of the ```Sail``` class.

### Methods

```python
__init__(   self, name=None, materials=None, mass=None, thickness=None,
                  reflectance=None, abs_coeff=None, target=0.2,
                  max_Starchip_temp=1000, power=None, wavelength=1.064e-6)
```

* Constructor for  ```MultilayerSail``` class.

```python
calculate_mission()
```

* Inherited from ```Sail``` class.  

## Material

The ```Material``` class.

* Materials are automatically saved in a pkl file with the same stem name as the material. The pkl file is saved inside a ```saved_materials``` directory within the current working directory. Any updates to materials are automatically saved.  

### Attributes

* *name* (str) - a code or tag that represents the material, usually chemical formula.
* *density* (float) [kg/m^3] - density of the material.
* *max_temp* (float) [K] - the temperature beyond which the material is not structurally sound. For most materials, this would be the melting point, but may vary in
special cases. For example, glasses like SiO2, GeO2 can become quite viscous past their glass transition temperature which lies lower than melting point.
* *abs_coeff* (float) [cm^-1] - absorption coefficient of the material.
* *n_list_path* (str) - path to file including a space-separated or comma-separated list of real refractive index for a range of wavelengths in microns.
* *k_list_path* (str) - path to file including a space-separated or comma-separated list of real refractive index for a range of wavelengths in microns.
* *n_equations* (list of lists) - a list of lists corresponding to equations for the refractive index. Each sublist includes a name (str), wavelength range (list), and function.
* *k_equations* (list of lists) - a list of lists corresponding to equations for the extinction coefficient. Each sublist includes a name (str), wavelength range (list), and function.

| Attribute | From | Required? |
| --------- | ---- | --------- |
| name | User input | Yes |
| density | User input | Yes |
| max_temp | User input | No |
| abs_coeff | User input | Optional, to find temperature |
| n_list_path | User input | Either path or equation required |
| k_list_path | User input | Either path or equation required |
| n_equations | User input | Either path or equation required |
| k_equations | User input | Either path or equation required |

### Methods

```python
__init__(name, density, max_temp, abs_coeff = None, n_list_path = None, k_list_path = None)
```
* Constructor for ```Material``` class.
* ```n_list_path``` and ```k_list_path``` are the filepaths to the list of real refractive index and extinction coefficient respectively.

```python
print_variables()
```
* Prints the values for each attribute of a material.
* Method is useful for checking the properties of a material and identifying which equations to add/remove.

```python
add_equation(name, range, filepath, n_or_k):
```
* Save a function for calculating the refractive index or extinction coefficient to the material. Functions are saved according to a unique name.
* A guide on creating this function is in the Material Equations section.

```python
rmv_equation(name, n_or_k)
```
* Delete equation from a material, according to the name.

### Material Equations

## Future Work

Improvements can be made by relaxing the assumptions outlined earlier. Notably, the library should be compatible with:

* lightsails of any shape/geometry
* different (and more realistic) beam profiles
* stabilisation dynamics and diffractive lightsails as a subclass

## Creators
**Andrew Ly**
* [anly2178@uni.sydney.edu.au](anly2178@uni.sydney.edu.au)
* [https://github.com/anly2178](https://github.com/anly2178)

**Justin Widjaja**
* [jwid8259@uni.sydney.edu.au](jwid8259@uni.sydney.edu.au)
* [https://github.com/jwid8259](https://github.com/jwid8259)

Supervised by Boris Kuhlmey, Martijn de Sterke, and Mohammad Rafat as part of a project for the University of Sydney.
