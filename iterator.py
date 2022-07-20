import os
import numpy as np
import pandas as pd
import codgs_juridics
import make_analysis
import parse_pdf
import read_pdf
import save_doc

def main(filepath, file):
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
                certificate_analysis = read_pdf.writeError2excel(filename)
                certificates_analysis = pd.concat([certificates_analysis, certificate_analysis])
                continue  # if all or any of the pages contains image-based information, continue with the next document
            info_df = parse_pdf.main(certificate_df, filename, loglist) # Had to put "filename" as input, because it was using "1" as was being
                                                            # assigned in the outer "filename" variable
            if (type(info_df) != type(pd.DataFrame())) and info_df == None:
                # if the document has annotations that could not be read, omit the document and notify the error in excel
                certificate_analysis = read_pdf.writeError2excel(filename)
                certificates_analysis = pd.concat([certificates_analysis, certificate_analysis])
                continue

        except:
            msg = 'No pudo extraerse información del documento\n'
            loglist.append(msg)
            print('No pudo extraerse información del documento\n')
            # Notifying the error in excel
            certificate_analysis = read_pdf.writeError2excel(filename)
            certificates_analysis = pd.concat([certificates_analysis, certificate_analysis])
            continue

        if len(info_df['no matricula'].unique()) > 1:
            msg = 'Este certificado tiene más de una matrícula asociada, lo que significa que pueden haber varios certificados en un mismo archivo. Descartando...'
            loglist.append(msg)
            loglist.append('\n')
            print(msg)
            # Notifying the error in excel
            certificate_analysis = read_pdf.writeError2excel(filename)
            certificates_analysis = pd.concat([certificates_analysis, certificate_analysis])
            continue

        info_df = codgs_juridics.read_codes(info_df, codes, loglist)

        certificate_analysis = pd.DataFrame(columns = ['no matricula', 'Nombre_archivo', 'Aprobado_revision'])
        certificate_analysis.loc[0,'no matricula'] = info_df.iloc[0,0]
        certificate_analysis.loc[0,'Nombre_archivo'] = info_df.iloc[0,1]
        certificate_analysis.loc[0,'Aprobado_revision'] = make_analysis.main(info_df, loglist)

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
    save_doc.save_loglist2text(loglist, filepath, filename_out)

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
            ask2run_again = save_doc.save_excl(filepath, filename_out, certificates_info_df,
                     certificates_analysis, num_cod_especs)
            break
        else:
            filename_out = input('Por favor ingrese el nombre del archivo de excel que contiene el análisis: ')
            print('\n')
            filename_out = filename_out+'.xlsx'
    else:
        ask2run_again = save_doc.save_excl(filepath, filename_out, certificates_info_df,
                  certificates_analysis, num_cod_especs)

    return ask2run_again