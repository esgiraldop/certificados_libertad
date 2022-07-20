import os
import pandas as pd

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


def load_codes():
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
        cods_filepath = input(
            'Por favor ingrese la dirección de la carpeta donde se encuentra la base de datos de códigos de naturaleza jurídica: ')
        cods_filepath = cods_filepath + '\\'
        print('\n')
        try:
            files_list = os.listdir(cods_filepath)
        except FileNotFoundError:
            print('No se pudo encontrar la carpeta. Por favor ingrese una opción válida.')
            print('\n')
            found_file == False  # to keep in the loop
        else:
            if filename2search not in files_list:
                print(f'No se pudo encontrar el archivo {filename2search}. Por favor ingrese otra dirección.')
                print('\n')
                found_file == False  # to keep in the loop
            else:
                codes = pd.read_csv(cods_filepath + filename2search, sep=';')
                codes.set_index('Codigo', inplace=True)
                found_file = True

    return codes