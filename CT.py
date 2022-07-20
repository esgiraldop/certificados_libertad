# -*- coding: utf-8 -*-
"""
Created on Sat Oct 17 21:44:04 2020

@author: ASUS
"""

import menus

def program_title():
    print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
    print('Lector de certificados de libertad')
    print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
    print('\n')
    print('Bienvenido a la aplicación para extracción de información de certificados de libertad')
    print('\n')


def main():

    init_choice = menus.init_choice_func()

    if init_choice == 1:

        filepath = 1
        filename = 1

        ask2run_again = menus.init_choice_is_1(filepath, filename)

        if ask2run_again == '0':
            return True

        if menus.run_again_func(ask2run_again):
            return True
        else:
            print('Gracias por usar la aplicación. Vuelva pronto!')
            print('\n')
            return False

    elif init_choice == 2:

        filepath = 1
        filename = 1

        ask2run_again = menus.init_choice_is_2(filepath, filename)

        if ask2run_again == '0':
            return True

        print('Recuerde revisar el archivo de excel resultante del análisis')
        print('\n')

        if menus.run_again_func(ask2run_again):
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
