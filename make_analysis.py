import pandas as pd

def main(info_df, loglist):
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

    Tipo_counts = pd.Series([0, 0, 0, 0, 0], index=['ABRE', 'LIMITA', 'CANCELA', 'INFORMA', 'A REVISION'])
    info_df_types = info_df['Tipo'].value_counts()

    # taking into account that an "anotación" can cancell multiple other "anotaciones" as well
    num_cancelaciones_totales = 0
    for index, item in info_df['Cancela anotacion'].iteritems():
        if type(item) == type(list()):
            num_cancelaciones_totales += len(item)
    info_df_types.loc['CANCELAN'] = num_cancelaciones_totales

    for info_df_type, amount in info_df_types.iteritems():
        Tipo_counts.loc[info_df_type] = amount

    if 'A REVISION' in info_df_types.index and info_df_types[
        'A REVISION'] > 0:  # if there is any "anotacion" with "A REVISION", the document is sent to be reviewed by the lawers
        a_revision_anots = info_df['No anotacion'][info_df['Tipo'] == 'A REVISION'].values
        msg = 'El documento debe enviarse a revisión. Revisar cuidadosamente las anotaciones:\n' + ', '.join(
            a_revision_anots)
        loglist.append(msg)
        loglist.append('\n')
        print("El documento debe enviarse a revisión. Revisar cuidadosamente las anotaciones: ", *a_revision_anots,
              sep='\n')
        print("\n")
        return 'REVISION'
    elif Tipo_counts.loc['ABRE'] + Tipo_counts.loc['LIMITA'] > Tipo_counts.loc['CANCELA']:
        # Implement here the revision of open mortgages
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