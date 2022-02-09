# certificados_tradicion

The application reads the certificados de tradición y libertad according to the format (PDF) of the Superintendencia de Notariado y Registro (SNR), extracts the information of the operations carried out with the property and verifies if the property is suitable for commercialization, according to the códigos de naturaleza jurídica established in the SNR. The application only reads documents downloaded from the SNR website in PDF format and without modifications after downloading.

The documents that cannot be read with the application are:
- Documents that are not in .pdf format
- Documents in .pdf format containing images
- Documents in .pdf format that are not certificados de libertad with the SNR format.
- .pdf files that contain several certificados de libertad with different license IDs, even if they have the same SNR format.

Written in Python 3.9.2