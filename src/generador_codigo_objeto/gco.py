import re
from src.analizador_sintactico_y_semantico.js_parser import JSParser


class GCO:
    REG_AUX = '.R9'
    REG_RET = '.R8'

    def __init__(self, co_out_fd, ci, size_RAs_, TS_):
        self.ci = ci
        self.co_out_fd = co_out_fd
        self.size_RAs = size_RAs_
        self.TS = TS_
        self.n_copy = 0
        self.lista_cadenas = []

    # Después de llamar a generate_co se inician todas las globales con RES XXX y se apunta IY al primer elemento
    def convert_co(self):
        res = []
        res += self.inst_init()
        for quartet in self.ci:
            if len(quartet) == 1 and type(quartet[0]) is str:
                res += quartet,
                if re.match('.*fin.*funcion.*', quartet[0], re.IGNORECASE):
                    res += [('\n\t; Inicio de código del main',)] + \
                           [('main:', 'NOP', None, None, None)]
            else:
                res += self.convert_quartet(quartet)
        res += self.inst_end()
        return res

    def inst_init(self):
        result = [(None, 'ORG', 0, None, None)] + \
                 [(None, 'MOVE', '#beginED', '.IY', None)] + \
                 [(None, 'MOVE', '#beginStack', '.IX', None)] + \
                 [(None, 'BR', '/main', None, None)]  # IX apunta al valor anterior (beforefirst)
        return result

    def inst_end(self):
        result = [(None, 'HALT', None, None, '\n\t; Fin de código del main\n')] + \
                 [('beginED:', 'RES', self.size_RAs['#EtiqMain'], None, None)] + \
                 self.book_space_cad() + \
                 [('beginStack:', 'NOP', None, None, None)] + \
                 [(None, 'END', None, None, None)]
        return result

    def book_space_cad(self):
        result = []
        for i, str_ in enumerate(self.lista_cadenas):
            result += [(f'cad{i}_{str_[1:-1][0:4]}:', 'DATA', str_)]
        return result

    def convert_quartet(self, quartet):
        oper = quartet[0]
        op1 = quartet[1]
        op2 = quartet[2]
        res = quartet[3]

        inst_list = []
        oper_ = self.get_key_from_value(oper, JSParser.OPERATOR_CODE)
        match oper_:
            case '=EL':  # (10, (3,1), None, (2,3)) --- (10, (1,1), None
                inst_list += self.set_registry(op1, '.R1', 'Value', '; Valor de Oper1 en R1') +\
                             self.set_registry(res, '.R3', 'Dir', '; Direccion de Res en R3') +\
                             [(None, 'MOVE', '.R1', '[.R3]', '; Valor de Oper1(R1) a Res(direccion a donde apunta R3)')]
            case '=Cad':  # (11, (4, "Hola"), None, (1, 2)) --- (11, (2,4), None, (1, 2))
                inst_list += self.set_registry(op1, '.R1', 'Dir')+\
                             self.set_registry(res, '.R3', 'Dir')+\
                             self.copy_loop('.R1','.R3')
            case '=and':  # (12, (1,2), (1,3), (1,4))
                inst_list += self.set_registry(op1, '.R1', 'Value','; Valor de Oper1 en R1') +\
                             self.set_registry(op2, '.R2', 'Value','; Valor de Oper2 en R2') +\
                             self.set_registry(res, '.R3', 'Dir','; Dirección de Res en R3') +\
                             [(None, 'AND', '.R1', '.R2', None)] +\
                             [(None, 'MOVE', '.A', '[.R3]', None)]
            case '=-':
                inst_list += self.set_registry(op1, '.R1', 'Value') +\
                             self.set_registry(op2, '.R2', 'Value') +\
                             self.set_registry(res, '.R3', 'Dir') +\
                             [(None, 'ADD', '.R1', '.R2', None)] +\
                             [(None, 'MOVE', '.A', '[.R3]', None)]
            case ':':
                inst_list += [(f'{op1[1][1:]}:', 'NOP', None, None, None)]
            case 'goto':
                inst_list += [(None, 'BR', f'/{res[1][1:]}', None, None)]
            case 'if=goto':
                inst_list += self.set_registry(op1, '.R1', 'Value') +\
                             self.set_registry(op2, '.R2', 'Value') +\
                             [(None, 'CMP', '.R1', '.R2', None)] +\
                             [(None, 'BZ', f'/{res[1][1:]}:', None, None)]
            case 'paramEL':
                pass
            case 'paramCad':
                pass
            case 'callValueEL':
                pass
            case 'callValueCad':
                pass
            case 'callVoid':
                pass
            case 'returnVoid':
                inst_list += [(None, 'BR', '[.IX]', None, None)]
            case 'returnEL':
                inst_list += self.set_registry(op1, self.REG_RET, 'Value',';Valor a devolver en R8') + \
                             [(None, 'BR', '[.IX]', None, None)]
            case 'returnCad':
                inst_list += self.set_registry(op1, self.REG_RET, 'Dir', ';Direccion de la cadena a devolver en R8') + \
                             [(None, 'BR', '[.IX]', None, None)]
            case 'alertEnt':
                pass
            case 'alertCad':
                pass
            case 'inputEnt':
                pass
            case 'inputCad':
                pass
        return inst_list

    def set_registry(self, oper, reg, mode, comment=None):
        """
        [10, (3, 2), , (1, 1)]
        get_operand((3, 2)) --> MOVE #2,.R1
        get_operand((1, 4)) --> ADD .IY,#4
                                MOVE .A,{self.REG_AUX}
                                MOVE [.{self.REG_AUX}],.R3

        """
        result = [(f'\n\t\t\t\t{comment}\n',)] if comment is not None else []
        oper_ = self.get_key_from_value(oper[0], JSParser.OPERAND_CODE)
        match oper_:
            case 'global': # Global
                desp = oper[1]
                if mode == 'Value':
                    result += [(None, 'ADD', f'#{desp}', '.IY', None)] +\
                              [(None, 'MOVE', '.A', f'{self.REG_AUX}', None)] +\
                              [(None, 'MOVE', f'[{self.REG_AUX}]', reg, None)]
                elif mode == 'Dir':
                    result += [(None, 'ADD', f'#{desp}', '.IY', None)] +\
                              [(None, 'MOVE', '.A', reg, None)]
            case 'local': # VL + DT + P
                desp = oper[1] + 1 #Se suma 1 para pasar por encima del EM
                if mode == 'Value':
                    result += [(None, 'ADD', f'#{desp}','.IX', None)] +\
                              [(None, 'MOVE', '.A', f'{self.REG_AUX}', None)] +\
                              [(None, 'MOVE', f'[{self.REG_AUX}]', reg, None)]
                elif mode == 'Dir':
                    result += [(None, 'ADD', f'#{desp}', '.IX', None)] +\
                              [(None, 'MOVE', '.A', reg, None)]
            case 'ent':  # Literal (EL)
                if mode == 'Value':
                    literal = oper[1]
                    result +=  [(None, 'MOVE', f'#{literal}', reg, None)]
            case 'cad': # Cad
                if mode == 'Dir':
                    str_ = oper[1]
                    result += [(None, 'MOVE', f'#cad{len(self.lista_cadenas)}_{str_[1:-1][0:4]}', reg, None)]
                    self.lista_cadenas.append(str_)
        return result

    def copy_loop(self, r_sour, r_dest):
        result = [('; Inicio bucle de copia',)] + \
                 [(f'copia{self.n_copy}:', 'NOP', None, None, None)] + \
                 [(None, 'MOVE', f'[{r_sour}]', self.REG_AUX, None)] + \
                 [(None, 'MOVE', f'{self.REG_AUX}', f'[{r_dest}]', None)] + \
                 [(None, 'ADD', '#1', r_sour, None)] + \
                 [(None, 'MOVE', '.A', r_sour, None)] + \
                 [(None, 'ADD', '#1', r_dest, None)] + \
                 [(None, 'MOVE', '.A', r_dest, None)] + \
                 [(None, 'CMP', '#0', f'{self.REG_AUX}', None)] + \
                 [(None, 'BNZ', f'/copia{self.n_copy}', None, None)] + \
                 [('; Fin bucle de copia',)]
        self.n_copy += 1
        return result

    def get_key_from_value(self, val, dict):
        for key, value in dict.items():
            if val == value:
                return key

    # -----------------------------------------Print methods-----------------------------------------

    def print_co(self, co):
        """Prints object code to a file.

        Prints the co to the output fd specified in the class

        Args:
            co (List): A list containing tuples like (etiq_ens, add, .R2, .R3, ;comm). None not allowed
        """
        result = ''
        for inst in co:
            if len(inst) == 1 and type(inst) is str:
                result += f' \n\t\t {inst}\n'
            else:
                result += self.format_inst(inst)

        print(result, file=self.co_out_fd)

    def format_inst(self, inst):
        """Formats the tuple given into a printable string

           Returns the string formatted

        Args:
           inst (Tuple): A tuple made up of 5 items: etiq, oper, op1, op2, comment. All elements can be null except the second one.
        """
        if len(inst) > 0:
            res_inst = inst[0] if inst[0] is not None else ''
            if len(inst) < 2:
                res_inst += self.get_blank_space(None)
                return f' \t\t {res_inst} \n\n'

            res_inst += f'{self.get_blank_space(inst[0])} {inst[1]} '
            for count, sub_inst in enumerate(inst[2:], 2):
                res_inst += f' {sub_inst},' if sub_inst is not None else ''
            return f'{res_inst[:-1]}\n'
        return ''

    def get_blank_space(self, etiq):
        if etiq is None:
            return ' ' * 20
        return ' ' * (20 - len(etiq))
