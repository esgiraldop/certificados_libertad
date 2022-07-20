import camelot
import pandas as pd

def main(fullname, filename, loglist):
    '''Function for reading a pdf with camelot and storing the certificado de libertad
        in a dataframe'''

    CT2parse = camelot.handlers.PDFHandler(fullname, pages='all')
    certificate_table = camelot.read_pdf(fullname, pages='all', flavor='stream',
                                         split_text=False, edge_tol=10,
                                         suppress_stdout=True)
    # extracting what pages have 5 rows or less. (it means it is a scanned document)
    page_lengths = []
    for page in certificate_table:
        page_lengths.append(len(page.df))
    filtered_lengths = list(filter(lambda page_length: page_length <= 5, page_lengths))

    if certificate_table.n == 0 or len(filtered_lengths) > 0:
        msg = f'Hubo un error leyendo el archivo \'{filename}\'. Por favor revise que no contenga imágenes.'
        loglist.append(msg)
        print(msg)
        loglist.append('\n')
        return None
    elif certificate_table.n < len(CT2parse.pages):
        # If there are less parsed pages than the actual pages, probably there are
        # some that are image-based (e.g. scanned docs) instead of text-based pages
        msg = f'Hubo un error leyendo una de las páginas del archivo \'{filename}\'. Por favor revise que ninguna de las páginas contenga imágenes.'
        loglist.append(msg)
        print(msg)
        loglist.append('\n')
        return None

    certificate_df = pd.DataFrame()

    for i in range(certificate_table.n):
        certificate_df = pd.concat([certificate_df, certificate_table[i].df], axis=0)

    certificate_df.reset_index(drop=True, inplace=True)

    # After checking the PDF has not any image-based page, it is necessary to check
    # whether the document is actually a CT or not

    for item in certificate_df.itertuples():
        # print(item)
        # print(item._2)

        for elem in item:

            if elem == 'CERTIFICADO DE TRADICION':
                # print('Es un CT')
                return certificate_df

        if item.Index > 10:  # No need of going throughout the document
            break

    msg = 'El documento no es un Certificado de tradición. Se omite el análisis del documento.'
    loglist.append(msg)
    print(msg)
    print('\n')
    return None

def plot_pdf(table):
    ''' Function for visual debugging of the pdfs'''

    camelot.plot(table, kind='contour')


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