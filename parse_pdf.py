import re
import pandas as pd
import numpy as np
import datetime as dt

def main(certificate_df, filename, loglist):
    ''' Function for reading the  certificado de libertad as a pdf and parsing
        the data in it


        '''

    # Extracting the date in which the certificate was generated
    for i in certificate_df.columns:
        print_date_series = certificate_df[i][certificate_df[i].str.match('Impreso el \d{,2} de')]
        if print_date_series.empty == False:
            break
    str_date = '(\d{,2}) de (Enero|Febrero|Marzo|Abril|Mayo|Junio|Julio|Agosto|Septiembre|Octubre|Noviembre|Diciembre) de (\d{,4})'
    print_date_sep = print_date_series. \
        str. \
        findall(str_date).iloc[0][0]  # fix this way to extract the dates. They should be in a single column
    # formating the print date
    dic_months = {'Enero': '01', 'Febrero': '02', 'Marzo': '03', 'Abril': '04',
                  'Mayo': '05', 'Junio': '06', 'Julio': '07', 'Agosto': '08',
                  'Septiembre': '09', 'Octubre': '10', 'Noviembre': '11',
                  'Diciembre': '12'}
    print_date = '-'.join(print_date_sep)
    month_letters = re.findall('[a-zA-Z]+', print_date)[0]
    print_date = print_date.replace(month_letters, dic_months[month_letters])
    print_date = dt.datetime.strptime(print_date, '%d-%m-%Y')
    # Getting the current date
    date_now = dt.datetime.now().strftime('%d-%m-%Y')  # getting rid of hour
    date_now = dt.datetime.strptime(date_now, '%d-%m-%Y')  # formating the current time
    # Checking if the certificate is more than 90 days old
    delta_time = date_now - print_date
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
    pin = pin_series.str.extract('(\d+)', expand=False).iloc[0]  # this number must be validated in the page of the SNR

    # Extracting the number of the matricula and more info
    no_matricula = certificate_df[1].loc[certificate_df[1] \
                                             .str.startswith('Nro Matrícula: ') == True]
    try:
        no_matricula = no_matricula.str.partition('Nro Matrícula: ').iloc[0, -1]  # pendiente guardar en el dataframe
    except:
        no_matricula = certificate_df[0].str.extract(r'Nro Matrícula: (.*)',
                                                     expand=False)
        no_matricula = no_matricula[no_matricula.isnull() == False]

    # anotaciones = certificate_df[0][certificate_df[0].str.\
    #                                 startswith('ANOTACION') == True]
    anotaciones = certificate_df[0][certificate_df[0].str. \
                                        startswith('ANOTACION: ') == True]

    no_anotaciones = anotaciones.str.extract(r'Nro ([0-9]*)', expand=False)

    # extracting the cancelled anotations
    cancel_anots = certificate_df[0][certificate_df[0].str. \
        startswith('Se cancela anotación No: ')] \
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
        count = idx  # counter starts right from the position of the indexer
        while found_var == False:
            count += 1
            next_line = certificate_df.loc[count, 0]
            bool_empty = all([next_line != '', next_line != ' ', next_line != None])
            # Checking if "next_line" starts with any of the sentences in "rows_not_to_collect"
            bool_rows_not_to_collect = \
                all([next_line.startswith(k) == False for k in rows_not_to_collect])

            if next_line.startswith('PERSONAS QUE INTERVIENEN EN EL ACTO') == False \
                    and bool_empty and bool_rows_not_to_collect:
                appended_info = appended_info + ' ' + certificate_df.loc[count, 0]
            else:
                found_var = True  # The code found the line where the next "PERSONAS QUE INTERVIENEN EN EL ACTO" is
        especs.loc[idx] = especs.loc[idx] + appended_info

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
    especs.loc[especs[0][especs[0].str.startswith('0')].index, 0] = especs.loc[
        especs[0][especs[0].str.startswith('0')].index, 0].str.replace('^0', '', regex=True)

    valor = certificate_df[1][certificate_df[1].str.startswith('VALOR ACTO') == True] \
        .str.extract('\$(.*)', expand=False)

    if valor.empty is True:
        valor = certificate_df[0].str.extract('VALOR ACTO: \$(.*)', expand=False)
        valor = valor[valor.isnull() == False]

    # Checking the total number of anotations by looping through all the columns in the dataframe
    for i in certificate_df.columns:
        total_anots = certificate_df[i] \
            .loc[certificate_df[i].str \
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
    nom_archivos = [filename] * len(no_anotaciones)  # Why the hell am I doing this?
    cod_espec = especs[0].astype('int')  # This line fails when, mistakenly, a specification code that not only contains
    # a number is extracted from the regex some lines above.
    # For example: "2001-00148-00"

    info_df = pd.DataFrame([nom_archivos, no_anotaciones, fechas_anotaciones, radicados_anotaciones,
                            valor, cod_espec, especs[1], cancel_anotaciones]).T

    info_df.columns = ['Nombre_archivo', 'No anotacion', 'Fecha', 'No radicado', 'valor',
                       'Cod. espec.', 'Espec.', 'Cancela anotacion']

    info_df['no matricula'] = no_matricula

    # concat column with num of matricula and the rest of the dataframe
    info_df = pd.concat([info_df['no matricula'], info_df.iloc[:, 0:-1]], axis=1)
    # Eliminating all the zeroes at the left on column "No anotacion"
    info_df['No anotacion'] = info_df['No anotacion'].str.replace('^0*', '', regex=True)

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
