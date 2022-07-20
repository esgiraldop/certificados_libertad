# -*- coding: utf-8 -*-
"""
Created on Sat Oct 17 21:44:04 2020

@author: ASUS
"""

import numpy as np
import pandas as pd
import os
import read_pdf
import parse_pdf
import codgs_juridics
    
def make_analysis(info_df, loglist):
    '''Function to evaluate if the document is approved or not.
            - Returns "ERROR EN EL ANALISIS" if there are "Cod. especs." that could not be found in the
                database.
            - Returns "REVISION" if the amount of "ABRE" + "LIMITA" is greater than 
                "CANCELA" in the column "Tipo" of "info_df".
            - Returns "APROBADO" otherwise.
            
            '''
    
    if info_df['Tipo'].isnull().any():
        # If the CT has any 'Cod. espec.' that could not be found in the database, skip this function
        return 'ERROR EN EL ANALISIS'
    
    Tipo_counts = pd.Series([0,0,0,0,0],index=['ABRE', 'LIMITA', 'CANCELA', 'INFORMA', 'A REVISION'])
    info_df_types = info_df['Tipo'].value_counts()
    
    # taking into account that an "anotación" can cancell multiple other "anotaciones" as well
    num_cancelaciones_totales = 0
    for index, item in info_df['Cancela anotacion'].iteritems():
        if type(item) == type(list()):
            num_cancelaciones_totales += len(item)   
    info_df_types.loc['CANCELAN'] = num_cancelaciones_totales
    
    for info_df_type, amount in info_df_types.iteritems():
        Tipo_counts.loc[info_df_type] = amount
        
        
    if 'A REVISION' in info_df_types.index and info_df_types['A REVISION'] > 0: # if there is any "anotacion" with "A REVISION", the document is sent to be reviewed by the lawers
        a_revision_anots = info_df['No anotacion'][info_df['Tipo'] == 'A REVISION'].values
        msg = 'El documento debe enviarse a revisión. Revisar cuidadosamente las anotaciones:\n' + ', '.join(a_revision_anots)
        loglist.append(msg)
        loglist.append('\n')
        print("El documento debe enviarse a revisión. Revisar cuidadosamente las anotaciones: ", *a_revision_anots, sep='\n')
        print("\n")
        return 'REVISION'
    elif Tipo_counts.loc['ABRE'] + Tipo_counts.loc['LIMITA'] > Tipo_counts.loc['CANCELA']:
        msg = 'Hay más aperturas y limitaciones que cancelaciones. El documento debe ir a revisión\nAnálisis exitoso\n\n'
        loglist.append(msg)
        # loglist.append('\n')
        print(msg)
        return 'REVISION'
    elif Tipo_counts.loc['ABRE'] + Tipo_counts.loc['LIMITA'] < Tipo_counts.loc['CANCELA']:
        msg = 'Hay más cancelaciones que aperturas y limitaciones. El documento debe ir a revisión\nAnálisis exitoso\n\n'
        loglist.append(msg)
        loglist.append('\n')
        print(msg)
        return 'REVISION'
    else:
        msg = 'El documento está aprobado\nAnálisis exitoso\n\n'
        loglist.append(msg)
        print(msg)
        loglist.append('\n')
        return 'APROBADO'


def init_choice_func():
    '''
    Function to ask for the first option

    Returns
    -------
    choice : integer that indicated the election of the user.

    '''
    
    choice = 4
    
    while choice not in ['1', '2', '3']:
        
        print('Seleccione la opción de acuerdo a su preferencia:')
        print('\n')
        print('*1* Si desea realizar el análisis de varios certificados.')
        print('*2* Si desea analizar solo un certificado.')
        print('*3* Salir del programa')
        choice = input()
        print('\n')
        
        if choice not in ['1', '2', '3']:
            print('Respuesta incorrecta. Por favor ingrese un número válido.')
            print('\n')
            
    return int(choice)

def init_choice_is_1(filepath, filename):
    
    while type(filepath) != type(str()) and filepath != '0':
    
        filepath = input('Por favor ingrese la dirección de la carpeta en donde se encuentran los archivos para analizar, o ingrese *0* para volver al menú anterior: ')
        print('\n')
        
        if filepath == '0':
            return '0'
        
        # catch error to repeat the question in case the folder cannot be found
        try:
            os.listdir(filepath)
        except FileNotFoundError:
            print('No se pudo encontrar la carpeta. Por favor ingrese una opción válida')
            print('\n')
            filepath = 1 # to keep in the loop
        else:
            # If filepath is ok, analyze the documents inside the folder or filepath
            ask2run_again = iterator(filepath, filename)
            return ask2run_again

def init_choice_is_2(filepath, filename):
    
    while type(filepath) != type(str()) or filepath != '0':

        filepath = input('Por favor ingrese la dirección de la carpeta en donde se encuentra el archivo a analizar, o ingrese *0* para volver al menú principal: ')
        print('\n')
        
        if filepath == '0':
            return '0'
        
        try:
            listdir = os.listdir(filepath)
        except FileNotFoundError:
            print('No se pudo encontrar la carpeta. Por favor ingrese una opción válida')
            print('\n')
            filepath = 1 # to keep in the loop
        else:
            
            while type(filename) != type(str()) and filename != '0':
                filename = input('Por favor ingrese el nombre del archivo a analizar (sin la extensión), o ingrese *0* para volver al menú principal: ')
                print('\n')

                if filename == '0':
                    return '0' # For coming back to the read_codes menu

                filename = filename+'.pdf'
                
                if filename not in listdir:
                    print('No se pudo encontrar el archivo dentro de la carpeta. Por favor ingrese una opción válida')
                    print('Estas son los archivos disponibles dentro de la carpeta actual:')
                    print(listdir)
                    print('\n')
                    filename = 1 # to keep in the loop
                else:
                    # If filepath and filename are ok, analyze the document
                    ask2run_again = iterator(filepath, filename)
                    return ask2run_again

def writeError2excel(filename):
    '''
    Function to write in excel an error in case the document cannot be read
    Inputs
    -------
        filename: Name of the current filename
    Outputs
    -------
        certificate_analysis : DataFrame containing error message for the current document
    '''
    certificate_analysis = pd.DataFrame(columns=['no matricula', 'Nombre_archivo', 'Aprobado_revision'])
    certificate_analysis.loc[0, 'no matricula'] = ''
    certificate_analysis.loc[0, 'Nombre_archivo'] = filename
    certificate_analysis.loc[0, 'Aprobado_revision'] = 'ERROR'

    return certificate_analysis


def save_doc(filepath, filename_out, certificates_info_df, certificates_analysis, num_cod_especs):
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

def iterator(filepath, file):
    '''
    Function that iterates trough the documents (CT's) inside a folder (or one single
            document), extracts the information, organizes it and analyzes the
            data according to the recommendations from the lawyers from C21.
    
    Returns
    ---------
    ask2run_again: Boolean value to evaluate in the read_codes body of the code whether
                the user wants to run the program again or not.
    
    '''

    # filepath = r'C:\Users\Usuario\OneDrive - Universidad EAFIT\darsetech\parse_cert_libertad\\'
    # subfolder = r'batch_4_pruebas\\'
    # subfolder = r'Casos_especiales\\'
    # filenames = os.listdir(filepath+subfolder)
    
    # # for finding position of a long list of filenames and be able to debug. Comment when not debugging
    # doc2find = 'CLT LOTE 105 - Adrian Boros.pdf'
    # count = 0
    # for item in filenames:
    #     if item == doc2find:
    #         print('the position is: ', count)
    #     count += 1
    
    filenames = os.listdir(filepath)
    
    codes = codgs_juridics.load_codes()
    ask2run_again = False

    loglist = list() # List for saving all the "log" messages comming out from the CT reading
      
    if file != 1: # in case the chosen option is *2*
        filenames = [file]
    
    # filename = filenames[15]
    
    certificates_info_df = pd.DataFrame() #dataframe where all the info of the certificates will be stored
    certificates_analysis = pd.DataFrame() # stores the analysis of "REVISION/APROBADO" for all the parsed CT's

    successAnalysis = 0 # To count how many successfull analyses were carried out in the current folder

    pdf_filenames = list()
    for filename in filenames:
        #Appending only the .pdf filenames
        if filename.endswith('.pdf'):
            pdf_filenames.append(filename)
    if len(pdf_filenames) == 0:
        # Making sure there are PDF documents in the current folder
        print("No pudieron encontrarse archivos PDF en esta carpeta.\n")
        return True

    for filename in pdf_filenames:
        if filename.endswith('.pdf') is False: continue
        loglist.append('\n')
        print('\n')
        loglist.append('-------------------------------------')
        print('-------------------------------------')
        loglist.append('\n')
        msg = f'Analizando documento \"{filename}\"'
        loglist.append(msg)
        print(msg)
        loglist.append('\n')

        try:
            certificate_df = read_pdf.main(filepath+'\\'+filename, filename, loglist)
            if np.all(certificate_df == None):
                # Notifying the error in excel
                certificate_analysis = writeError2excel(filename)
                certificates_analysis = pd.concat([certificates_analysis, certificate_analysis])
                continue  # if all or any of the pages contains image-based information, continue with the next document
            info_df = parse_pdf.main(certificate_df, filename, loglist) # Had to put "filename" as input, because it was using "1" as was being
                                                            # assigned in the outer "filename" variable
            if (type(info_df) != type(pd.DataFrame())) and info_df == None:
                # if the document has annotations that could not be read, omit the document and notify the error in excel
                certificate_analysis = writeError2excel(filename)
                certificates_analysis = pd.concat([certificates_analysis, certificate_analysis])
                continue

        except:
            msg = 'No pudo extraerse información del documento\n'
            loglist.append(msg)
            print('No pudo extraerse información del documento\n')
            # Notifying the error in excel
            certificate_analysis = writeError2excel(filename)
            certificates_analysis = pd.concat([certificates_analysis, certificate_analysis])
            continue
        
        if len(info_df['no matricula'].unique()) > 1:
            msg = 'Este certificado tiene más de una matrícula asociada, lo que significa que pueden haber varios certificados en un mismo archivo. Descartando...'
            loglist.append(msg)
            loglist.append('\n')
            print(msg)
            # Notifying the error in excel
            certificate_analysis = writeError2excel(filename)
            certificates_analysis = pd.concat([certificates_analysis, certificate_analysis])
            continue
        
        info_df = codgs_juridics.read_codes(info_df, codes, loglist)
        
        certificate_analysis = pd.DataFrame(columns = ['no matricula', 'Nombre_archivo', 'Aprobado_revision'])
        certificate_analysis.loc[0,'no matricula'] = info_df.iloc[0,0]
        certificate_analysis.loc[0,'Nombre_archivo'] = info_df.iloc[0,1]
        certificate_analysis.loc[0,'Aprobado_revision'] = make_analysis(info_df, loglist)
    
        certificates_info_df = pd.concat([certificates_info_df, info_df])
        certificates_analysis = pd.concat([certificates_analysis, certificate_analysis])
        successAnalysis += 1

    if successAnalysis == 0:
        # Conditional for avoiding an error downstream
        print('\n')
        print('Ninguno de los documentos PDF pudo ser analizado con éxito.')
        print('\n')
        return True
    certificates_analysis.set_index('no matricula', inplace=True)
    certificates_info_df.set_index('no matricula', inplace=True)
    # in case only one certificate is selected, but could not be read
    if len(certificates_info_df) == 0:
        return True
    # Finding the different codigos de especificación and their frequency of appearance
    num_cod_especs = pd.DataFrame(certificates_info_df['Cod. espec.'].value_counts())
    
    # Assigning the meaning of the especification from the codigos de naturaleza juridica database
    num_cod_especs = pd.DataFrame(num_cod_especs).merge(codes, left_index=True, right_index=True, how='left')
    # num_cod_especs['Cod. espec.'].plot(xlabel='Código de especificación', ylabel='Cantidad', kind='bar')
    
    # filename = 'Analisis_certificados_libertad.xlsx'
    filename_out = input('Por favor ingrese el nombre del archivo de excel que contiene el análisis: ')
    print('\n')
    # Saving all the "log" messages into a text file
    save_loglist2text(loglist, filepath, filename_out)

    filename_out = filename_out+'.xlsx'

    # checking there are not files in the current folder with the same name already
    while filename_out in os.listdir(filepath):
        
        choice = 3
        
        while choice not in [1, 2]:
            print('Ya existe un archivo con el mismo nombre. Desea sobreescribirlo?')
            print('*1* Si')
            choice = input('*2* No: ')
            
            if choice not in ['1', '2']:
                print('Por favor seleccione una opción válida')
            else:
                choice  = int(choice)

        if choice == 1:
            ask2run_again = save_doc(filepath, filename_out, certificates_info_df,
                     certificates_analysis, num_cod_especs)
            break
        else:
            filename_out = input('Por favor ingrese el nombre del archivo de excel que contiene el análisis: ')
            print('\n')
            filename_out = filename_out+'.xlsx' 
    else:
        ask2run_again = save_doc(filepath, filename_out, certificates_info_df,
                  certificates_analysis, num_cod_especs)
        
    return ask2run_again

def run_again_func(ask2run_again):
    
    run_again = '0'
    
    if ask2run_again == True:
    
        while run_again not in ['1', '2']:
            
            print('Desea realizar otro análisis?\n*1* No')
            run_again = input('*2* Si: ')
            
            if run_again not in ['1', '2']:
                print('Por favor ingrese una opción válida')
            else:
                #run_again= int(run_again)
                pass
        
        if run_again == '1':
            return False
        elif run_again == '2':
            return True

def program_title():
    print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
    print('Lector de certificados de libertad')
    print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
    print('\n')
    print('Bienvenido a la aplicación para extracción de información de certificados de libertad')
    print('\n')


def main():

    init_choice = init_choice_func()

    if init_choice == 1:

        filepath = 1
        filename = 1

        ask2run_again = init_choice_is_1(filepath, filename)

        if ask2run_again == '0':
            return True

        if run_again_func(ask2run_again):
            return True
        else:
            print('Gracias por usar la aplicación. Vuelva pronto!')
            print('\n')
            return False

    elif init_choice == 2:

        filepath = 1
        filename = 1

        ask2run_again = init_choice_is_2(filepath, filename)

        if ask2run_again == '0':
            return True

        print('Recuerde revisar el archivo de excel resultante del análisis')
        print('\n')

        if run_again_func(ask2run_again):
            return True
        else:
            print('Gracias por usar la aplicación. Vuelva pronto!')
            print('\n')
            return False

    elif init_choice == 3:

        # Exit of the loop

        print('Gracias por usar la aplicación. Vuelva pronto!')
        print('\n')
        stay_program = False


#################################################################
##################### read_codes body of the code #####################
#################################################################

program_title()

stay_program = True

while stay_program:
    stay_program = main()


input('Presione cualquier tecla para salir de la aplicación: ')
############## Program finishes ######################
