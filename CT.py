# -*- coding: utf-8 -*-
"""
Created on Sat Oct 17 21:44:04 2020

@author: ASUS
"""

import numpy as np
import pandas as pd
import os
import datetime as dt
import re
import time
import read_pdf
    
def parsePDF(certificate_df, filename, loglist):
    
    ''' Function for reading the  certificado de libertad as a pdf and parsing
        the data in it


        '''
    
    # Extracting the date in which the certificate was generated
    for i in certificate_df.columns:
        print_date_series = certificate_df[i][certificate_df[i].str.match('Impreso el \d{,2} de')]
        if print_date_series.empty == False:
            break
    str_date = '(\d{,2}) de (Enero|Febrero|Marzo|Abril|Mayo|Junio|Julio|Agosto|Septiembre|Octubre|Noviembre|Diciembre) de (\d{,4})'  
    print_date_sep = print_date_series.\
        str.\
            findall(str_date).iloc[0][0]   # fix this way to extract the dates. They should be in a single column
    # formating the print date
    dic_months = {'Enero':'01', 'Febrero':'02', 'Marzo':'03', 'Abril':'04',
                  'Mayo':'05', 'Junio':'06', 'Julio': '07', 'Agosto':'08',
                  'Septiembre':'09', 'Octubre':'10', 'Noviembre':'11',
                  'Diciembre':'12'}
    print_date = '-'.join(print_date_sep)
    month_letters = re.findall('[a-zA-Z]+', print_date)[0]
    print_date = print_date.replace(month_letters, dic_months[month_letters])
    print_date = dt.datetime.strptime(print_date, '%d-%m-%Y')
    # Getting the current date
    date_now = dt.datetime.now().strftime('%d-%m-%Y') # getting rid of hour
    date_now = dt.datetime.strptime(date_now, '%d-%m-%Y') # formating the current time
    # Checking if the certificate is more than 90 days old
    delta_time = date_now-print_date
    msg = f'Este certificado tiene {delta_time.days} días'
    loglist.append(msg)
    loglist.append('\n')
    print(msg)
    # if delta_time.days > 90:
        # return
    # 'too old'
    
    
    # Extracting the number of the pin of the certificate
    for i in certificate_df.columns:
        pin_series = certificate_df[i][certificate_df[i].str.match('Certificado generado con el Pin No:')]
        if pin_series.empty == False:
            break
    pin = pin_series.str.extract('(\d+)', expand=False).iloc[0] # this number must be validated in the page of the SNR
    
    
    
    # Extracting the number of the matricula and more info
    no_matricula = certificate_df[1].loc[certificate_df[1]\
                                         .str.startswith('Nro Matrícula: ') == True]
    try:
        no_matricula = no_matricula.str.partition('Nro Matrícula: ').iloc[0,-1]  # pendiente guardar en el dataframe
    except:
        no_matricula = certificate_df[0].str.extract(r'Nro Matrícula: (.*)',
                                                     expand=False)
        no_matricula = no_matricula[no_matricula.isnull()==False]
    
    # anotaciones = certificate_df[0][certificate_df[0].str.\
    #                                 startswith('ANOTACION') == True]
    anotaciones = certificate_df[0][certificate_df[0].str.\
                                    startswith('ANOTACION: ') == True]
    
    no_anotaciones = anotaciones.str.extract(r'Nro ([0-9]*)', expand=False)
    
    
    
    # extracting the cancelled anotations
    cancel_anots = certificate_df[0][certificate_df[0].str.\
                                     startswith('Se cancela anotación No: ')]\
        .str.extract(r'\: (.*)')
    cancel_anots[0] = cancel_anots[0].str.split(',').apply(lambda x: [int(i) for i in x])
    cancel_anotaciones = pd.Series(np.zeros(len(no_anotaciones)))
    cancel_anotaciones.index = no_anotaciones.index
    # Finding the number of anotation which cancells a previous anotation by relating
        # "no_anotaciones" and "cancel_anots"
    cancel_anots[1] = None
    for item in cancel_anots.itertuples():
        index = item.Index
        not_found = True
        original_index = index
        while not_found:
            if index not in no_anotaciones.index:
                index -= 1
            else:
                cancel_anots.loc[original_index, 1] = index
                not_found = False
        
    cancel_anotaciones.loc[list(cancel_anots[1].values)] = cancel_anots[0].values
    cancel_anotaciones.replace(0, np.nan, inplace=True)
    
    fechas_anotaciones = anotaciones.str.extract(r'Fecha: ([0-9]{2}\-[0-9]{2}\-[0-9]{4})', expand=False)
    radicados_anotaciones = anotaciones.str.extract('Radicación: ([0-9]*\-[0-9]*)', expand=False)
    especs = certificate_df[0][certificate_df[0].str.startswith('ESPECIFICACION:') == True]
    
    # Searching if there are more info between lines "ESPECIFICACION: " and 
        # "PERSONAS QUE INTERVIENEN EN EL ACTO" in order to append it to the info
        # in "ESPECIFICACION"
    rows_not_to_collect = ['Certificado generado con el Pin', 'Pagina', 
                           'Impreso el', '\"ESTE CERTIFICADO REFLEJA',
                          'HASTA LA FECHA Y HORA DE SU EXPEDICION',
                          'No tiene validez sin la firma']    
    for idx in especs.index:
        found_var = False
        appended_info = ' '
        count = idx # counter starts right from the position of the indexer
        while found_var == False:
            count += 1
            next_line = certificate_df.loc[count, 0]
            bool_empty = all([next_line != '', next_line != ' ',next_line != None])
            # Checking if "next_line" starts with any of the sentences in "rows_not_to_collect"
            bool_rows_not_to_collect = \
                all([next_line.startswith(k) == False for k in rows_not_to_collect])
                
            if next_line.startswith('PERSONAS QUE INTERVIENEN EN EL ACTO') == False \
                and bool_empty and bool_rows_not_to_collect:
                appended_info = appended_info + ' ' + certificate_df.loc[count, 0]
            else: found_var = True # The code found the line where the next "PERSONAS QUE INTERVIENEN EN EL ACTO" is
        especs.loc[idx] =  especs.loc[idx] + appended_info
    
    # Extracting the "codigo de naturaleza jurídica"
    especs = especs.str.extract(r':(?:[^:]*:){1} (\d{3,4} ?\D.*)', expand=False).str.split(r'\s', n=1, expand=True)
    # especs.str.extract(r':.*: (\d.*)', expand=False)
    
    # regex # 1 --> r':.*: (\d.*)'
    # regex # 2 --> r'(?!:.*)(\d.*)'
    # regex # 3 --> r'(?!:.*: )(\d.*)'
    # regex # 4 --> r':.*: (\d{3,4} ?\D.*)'
    # regex # 5 --> r':(?:.*:){1} (\d{3,4} ?\D.*)'
    # regex # 6 (best so far 2022-03-25) --> r':(?:[^:]*:){1} (\d{3,4} ?\D.*)'
    
    # where there are specification numbers starting with a zero, eliminate the zero
    especs.loc[especs[0][especs[0].str.startswith('0')].index,0] = especs.loc[especs[0][especs[0].str.startswith('0')].index,0].str.replace('^0', '', regex=True)
    

    valor = certificate_df[1][certificate_df[1].str.startswith('VALOR ACTO') == True]\
        .str.extract('\$(.*)', expand=False)
        
    if valor.empty is True:
        valor = certificate_df[0].str.extract('VALOR ACTO: \$(.*)', expand=False)
        valor = valor[valor.isnull()==False]


    # Checking the total number of anotations by looping through all the columns in the dataframe
    for i in certificate_df.columns:
        total_anots = certificate_df[i]\
            .loc[certificate_df[i].str\
                 .contains('N\nRO TOTAL DE ANOTACIONES:|NRO TOTAL DE ANOTACIONES:')]
        if total_anots.empty == False:   
            total_anots = int(total_anots.str.extract('\*(\d*)\*').values[0][0])
            break
        else: 
            msg = 'No se encontró el número total de anotaciones al final del documento. \nPor favor revise el archivo y asegúrese que coincidan con la cantidad de anotaciones extraídas en la hoja de excel resultante de este análisis'
            loglist.append(msg)
            loglist.append('\n')
            print(msg)
            total_anots = 0
    
    
    # Before joining dataframe, it is necessary resetting the indexes
    no_anotaciones.reset_index(drop=True, inplace=True)
    fechas_anotaciones.reset_index(drop=True, inplace=True)
    radicados_anotaciones.reset_index(drop=True, inplace=True)
    valor.reset_index(drop=True, inplace=True)
    especs.reset_index(drop=True, inplace=True)
    cancel_anotaciones.reset_index(drop=True, inplace=True)
    nom_archivos = [filename]*len(no_anotaciones) # Why the hell am I doing this?
    cod_espec = especs[0].astype('int') # This line fails when, mistakenly, a specification code that not only contains
                                            # a number is extracted from the regex some lines above.
                                            # For example: "2001-00148-00"
       
    info_df = pd.DataFrame([nom_archivos, no_anotaciones, fechas_anotaciones, radicados_anotaciones,
                                valor, cod_espec, especs[1], cancel_anotaciones]).T
    
    info_df.columns = ['Nombre_archivo', 'No anotacion', 'Fecha', 'No radicado', 'valor',
                       'Cod. espec.', 'Espec.', 'Cancela anotacion']

    info_df['no matricula'] = no_matricula
    
    info_df = pd.concat([info_df['no matricula'], info_df.iloc[:,0:-1]], axis=1)
    
    
    
    # Cheking if the extracted total number of annotations is coincident with the number of annotations extracted with camelot
    if (total_anots != len(no_anotaciones)) | (total_anots != len(especs)):

        if (total_anots < len(no_anotaciones)) | (total_anots < len(especs)):
            msg = 'Al parecer, hay más de un certificado de libertad en el PDF.\nRecuerde que solo puede haber un certificado por PDF. Descartando documento...'
            loglist.append(msg)
            print(msg)
            loglist.append('\n')
            return None

        msg = 'Hay algunas anotaciones que no pudieron ser identificadas, por lo que no puede realizarse el análisis. Descartando documento...'
        loglist.append(msg)
        print(msg)
        loglist.append('\n')
        wrong_cod_especs = list(cod_espec.where((cod_espec > 999) | (cod_espec < 100)).value_counts().index)
        
        wrongs_cod_especs_anots = info_df[info_df['Cod. espec.'].isin(wrong_cod_especs)]['No anotacion'].values
        
        if len(wrongs_cod_especs_anots) == 1:
            msg = f'Por favor revisar la anotación: {wrongs_cod_especs_anots}'
            loglist.append(msg)
            print(msg)
        if len(wrongs_cod_especs_anots) > 1:
            msg = f'Por favor revisar la anotaciones: {wrongs_cod_especs_anots}'
            loglist.append(msg)
            print(msg)
            
        return None
        
    elif (total_anots == len(no_anotaciones)) | (total_anots == len(especs)): 
        msg = f'El número total de anotaciones es: {total_anots}'
        loglist.append(msg)
        loglist.append('\n')
        print(msg)
    
        return info_df

def read_codes(info_df, codes, loglist):
    '''
    Function to read the codigos de naturaleza jurídica. Returns the type of
    operation that was made in each annotation according to its codigo of naturaleza
    juridica
    '''
    
    info_df = info_df.merge(codes, how='left', left_on='Cod. espec.', right_index=True)
    
    missing_codes = info_df[info_df['Tipo'].isnull()]['Cod. espec.'].values
    
    if len(missing_codes) == 1:
        msg = f'El código {missing_codes} no está en la base de datos. No se pudo analizar el documento.\n\n'
        loglist.append(msg)
        print(msg)
    elif len(missing_codes) > 1:
        msg = f'Los códigos {missing_codes} no están en la base de datos. No se pudo analizar el documento.\n\n'
        loglist.append(msg)
        print(msg)
    
    return info_df
    
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
      

def plot_pdf(table):
    ''' Function for visual debugging of the pdfs'''
    
    camelot.plot(table, kind='contour')

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
                    return '0' # For coming back to the main menu

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

def load_codgs_natur_juridica():
    '''
    Function which asks the user for the filepath where the database of codigos
        the naturaleza juridica is and generates the database in a dataframe
        for using in the analysis.

    Returns
    -------
    codes : DataFrame containing the database for the codes.

    '''
    found_file = False
    filename2search = 'cods_naturaleza_juridica.csv'
    
    while found_file == False:
        
        # cods_filepath = r'C:\Users\Usuario\OneDrive - Universidad EAFIT\darsetech\parse_cert_libertad\\'
        cods_filepath = input('Por favor ingrese la dirección de la carpeta donde se encuentra la base de datos de códigos de naturaleza jurídica: ')
        cods_filepath = cods_filepath+'\\'
        print('\n')
        try:
            files_list = os.listdir(cods_filepath)
        except FileNotFoundError:
            print('No se pudo encontrar la carpeta. Por favor ingrese una opción válida.')
            print('\n')
            found_file == False # to keep in the loop
        else:
            if filename2search not in files_list:
                print(f'No se pudo encontrar el archivo {filename2search}. Por favor ingrese otra dirección.')
                print('\n')
                found_file == False # to keep in the loop
            else:
                codes = pd.read_csv(cods_filepath + filename2search, sep=';')
                codes.set_index('Codigo', inplace=True)
                found_file = True
        
    return codes
    

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
    ask2run_again: Boolean value to evaluate in the main body of the code whether
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
    
    codes = load_codgs_natur_juridica()
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
                certificates_analysis = certificates_analysis.append(certificate_analysis)
                continue  # if all or any of the pages contains image-based information, continue with the next document
            info_df = parsePDF(certificate_df, filename, loglist) # Had to put "filename" as input, because it was using "1" as was being
                                                            # assigned in the outer "filename" variable
            if (type(info_df) != type(pd.DataFrame())) and info_df == None:
                # if the document has annotations that could not be read, omit the document and notify the error in excel
                certificate_analysis = writeError2excel(filename)
                certificates_analysis = certificates_analysis.append(certificate_analysis)
                continue

        except:
            msg = 'No pudo extraerse información del documento\n'
            loglist.append(msg)
            print('No pudo extraerse información del documento\n')
            # Notifying the error in excel
            certificate_analysis = writeError2excel(filename)
            certificates_analysis = certificates_analysis.append(certificate_analysis)
            continue
        
        if len(info_df['no matricula'].unique()) > 1:
            msg = 'Este certificado tiene más de una matrícula asociada, lo que significa que pueden haber varios certificados en un mismo archivo. Descartando...'
            loglist.append(msg)
            loglist.append('\n')
            print(msg)
            # Notifying the error in excel
            certificate_analysis = writeError2excel(filename)
            certificates_analysis = certificates_analysis.append(certificate_analysis)
            continue
        
        info_df = read_codes(info_df, codes, loglist)
        
        certificate_analysis = pd.DataFrame(columns = ['no matricula', 'Nombre_archivo', 'Aprobado_revision'])
        certificate_analysis.loc[0,'no matricula'] = info_df.iloc[0,0]
        certificate_analysis.loc[0,'Nombre_archivo'] = info_df.iloc[0,1]
        certificate_analysis.loc[0,'Aprobado_revision'] = make_analysis(info_df, loglist)
    
        certificates_info_df = certificates_info_df.append(info_df)
        certificates_analysis = certificates_analysis.append(certificate_analysis)
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
##################### main body of the code #####################
#################################################################

program_title()

stay_program = True

while stay_program:
    stay_program = main()


input('Presione cualquier tecla para salir de la aplicación: ')
############## Program finishes ######################
