import pandas as pd

def save_excl(filepath, filename_out, certificates_info_df, certificates_analysis, num_cod_especs):
    '''
    Function for saving the document which collects all the info derived from the
        analysis in an excel file

    Parameters
    ----------
    filepath : String containing the path of the file.
    filename_out: String containing the name of the file.
    certificates_info_df : DataFrame containing the information collected for
                                all the CT's.
    certificates_analysis : DataFrame containing the analysis for each CT
                                according to their annotations.
    num_cod_especs : DataFrame containing the specification codes that appeared
                                the most in the analysis.

    Returns
    -------
    True if the analysis was successfully saved in the excel file. This boolean
        value is to be used for asking the user if wants to carry out another
        analysis.

    '''
    error = True
    while error:
        fullname = filepath+'\\'+filename_out
        try:
            writer = pd.ExcelWriter(fullname, engine='xlsxwriter')
            certificates_info_df.to_excel(writer, sheet_name='info_CT')
            certificates_analysis.to_excel(writer, sheet_name='analisis_CT')
            num_cod_especs.to_excel(writer, sheet_name='cods_por_cantidad')
            writer.save()
        except PermissionError:
            # Checking if file is open in excel
            try:
                myfile = open(fullname, "r+")  # or "a+", whatever you need
            except PermissionError:
                input(f'Cierre el archivo \'{fullname}\' y presione cualquier tecla:')
                print('\n')
            else:
                myfile.close()
                # If the file is not open by another process, then it must be due to permission issues for saving the
                    # file in the current filepath, so another direction must be asked
                print('La aplicación no tiene permisos para guardar el archivo en esta dirección: ', fullname)
                filepath = input('Por favor ingrese otra dirección: ')
        else:
            error = False
            print('Este archivo de excel se guardará con el nombre: ', fullname)
            print('Archivo de excel guardado con éxito')
            print('\n')
            print('Recuerde revisar el archivo de excel resultante del análisis')
            print('\n')

    return True

def save_loglist2text(loglist, filepath, filename_out):
    '''
    Function to write in a text files the log messages obtained from the analysis of a CT or a series of CTs
    Inputs
    -------
        loglist: List containing the logs
        filename_out: String with the name of the excel file to be generated. The name of the the text file is
                        filename_out + "_logfile.txt"
    Outputs
    -------
    '''

    #Put a conditional to test if the file does not exists already

    with open(filepath+'\\'+filename_out+'_logfile.txt', 'w') as file:
        for line in loglist:
            file.write(line)
        file.close()