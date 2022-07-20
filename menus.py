import os
import iterator

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
            ask2run_again = iterator.main(filepath, filename)
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
                    ask2run_again = iterator.main(filepath, filename)
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