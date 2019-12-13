  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
# 5G-EVE Portal Components
This repository contains part of the back-end modules implementing the functionality provided by 5G-EVE portal. It contains modules for authentication/authorization relying on Keycloak and a ticketing system which basically relies on bugzilla.

# Packages included
## File Storage component
The File Storage module is intended to be used by other modules or by some actors to upload large files, similar to a cloud storage system. The main user of this module is the VNF Storage component at the Portal GUI layer, which is used by VNF providers to upload VNF packages, so the site managers selected in this process will receive a ticket requesting the onboarding of the selected packages in their sites. As commented before, the File Storage module, after a successful uploading of the file, has to create as many tickets as the sites selected by the VNF provider. These tickets should include the link to the uploaded package, so site managers can download such file.

## Implementation details
This component is based on [Flask](http://flask.palletsprojects.com/en/1.1.x/) lightweight WSGI web application framework.

## Authors
Ginés García Avilés [Gitlab](https://gitlab.com/GinesGarcia) [Github](https://github.com/GinesGarcia) [website](https://www.it.uc3m.es/gigarcia/index.html)

## Acknowledgments
* [5G EVE](https://www.5g-eve.eu/)