from sly import Lexer
from sly.lex import Token
from pyTable import SymTable
# from Lexer import Token
import sys


class JSLexer(Lexer):
    """The class which makes an lexer from javascript.

    Attributes:
        data (str): the code which is going to be analyzed by the lexer

    """

    def __init__(self, data):
        self.data = data

    tokens = {CTEENTERA, CADENA, CTELOGICA, OPARIT, OPESP,
              OPREL, OPLOG, OPASIG, ID, NUMBER, STRING, BOOLEAN, LET, ALERT,
              INPUT, FUNCTION, ABPAREN, CEPAREN, ABLLAVE, CELLAVE, COMA, PUNTOYCOMA, RETURN, IF, FOR, EOF}

    ignore = ' \t'

    # Tokens
    CTEENTERA = r'\d+'
    CADENA = r'".*?"'
    CTELOGICA = r'true|false'
    OPESP = r'--'
    OPARIT = r'\+|-'
    OPREL = r'=='
    OPASIG = r'='
    OPLOG = r'&&'

    ABPAREN = r'[(]'
    CEPAREN = r'[)]'
    ABLLAVE = r'[{]'
    CELLAVE = r'[}]'
    COMA = r'[,]'
    PUNTOYCOMA = r'[;]'
    # EOF = '\Z'

    ID = r'[a-zA-Z][a-zA-Z0-9_]*'
    ID['number'] = NUMBER
    ID['string'] = STRING
    ID['boolean'] = BOOLEAN
    ID['let'] = LET
    ID['alert'] = ALERT
    ID['input'] = INPUT
    ID['function'] = FUNCTION
    ID['return'] = RETURN
    ID['if'] = IF
    ID['for'] = FOR

    # Revisar EOF quizá lo hace automáticamente
    literals = {'{', '}', ',', ';', '/d'}

    def CTEENTERA(self, t):
        """Function called when a token which belongs to an integer constant is found.

        If the number found is bigger than 32767, this function will print an error
        by stderr and will stop the lexer.

        Args:
            t(token): An integer constant token.

        Returns:
            token: The return value. It's modified to change its value from an String value to an Integer value.
        """

        t.value = int(t.value)
        if t.value > 32767:
            self.error(t, "CTE_ENTERA")
        return t

    def CADENA(self, t):
        """Function called when a token which belongs to an string constant is found.

        If the string length is bigger than 64 it will print an error by stderr and will stop the lexer.

        Args:
            t(token): The String constant token.

        Returns:
            token: The return value which is modified to delete the quotation marks.
        """
        t.value = t.value[1:-1]
        if len(t.value) > 64:
            self.error(t, "CADENA")
        return t

    def CTELOGICA(self, t):
        """Called when a token which is a logical constant is found

        It modifies the argument token changing its str value to an integer value.
        The token value will be 0 if "false" is found or 1 if "true"

        Args:
            t(Token): Token which matches the logical constant pattern

        Returns:
            Token: Token modified
        """

        if t.value == 'false':
            t.value = 0
        else:
            t.value = 1
        return t

    # TODO: Para hacer cuando se de la TS
    # def ID(self,t):

    def OPARIT(self, t):
        """Function called when a token which arithmetical operator is found.

        The token is modified to change the str value to an Integer value.
        This token's integer value will be 0 if "+" is found or 1 if "-"

        Args:
            t(token): The token which matches an arithmetic operation.

        Returns:
            token: The return token modified.
        """
        if t.value == '+':
            t.value = 0
        else:
            t.value = 1
        return t

    @_('\n+',
       r'(?s:/\*.*?\*/)')
    def newline(self, t):
        """Function called when a comment or a newline (\n) are found.

        It's used to increase the line number where the lexer is working to
        provide a correct information when an error is found.

        Args:
            t(token): The token which contains a comment or a newline.
        """
        self.lineno += t.value.count('\n')

    # Compute column.
    #     input is the input text string
    #     token is a token instance
    def find_column(self, token):
        """Function called to provide the column where the error has been found.

        Args:
            t(token): The only parameter.
        """
        last_cr = self.text.rfind('\n', 0, token.index)
        if last_cr < 0:
            last_cr = 0
        column = (token.index - last_cr)
        return column

    def error(self, t, type_error="default"):
        """Function called when an error has been found.

        An error is reported when a wrong character is found, a token which contains
        a number bigger than 32767 is found or when a String token is found whom length is bigger than 64.
        It prints a description of the error and provides the number of the line and the column where the error has
        been found.

        Args:
            t(token): The only parameter.
        """

        if type_error == "CADENA":
            res = f'Cadena demasiado larga: "{t.value}", con logitud mayor que 64: {len(t.value)},'
        elif type_error == "CTE_ENTERA":
            res = f'Número fuera de rango: "{t.value}"'
        else:  # TODO: hacer cambios de idioma, para que tenga consistencia, en español el output, y en ingles todo lo demas, ¿no?
            res = f'Illegal character "{t.value[0]}"'
        print(f'{res} en la linea {self.lineno} y columna {self.find_column(t)}', file=sys.stderr)
        exit()

    def get_token(self):
        """Principal function which is responsible for give the different tokens one by one.

        Finally, it gives a different token which represents the end of file.

        Yields:
            token: The next token.
        """
        for tok in self.tokenize(self.data):
            yield tok

        tok_EOF = Token()
        tok_EOF.type = 'EOF'
        tok_EOF.value = '-'
        yield tok_EOF


if __name__ == '__main__':
    tables = SymTable.SymTable()  # Creación de la instancia para el manejador de tablas
    id0 = tables.newTable()  # Creación de la tabla global (id = 0)
    id1 = tables.newTable()  # Creación de la tabla local (id = 1)
    tables.add(id0, ("string", 0))  # Añadimos en la tabla global el lex string con desplazamiento 0
    lex = ("number", 8)  # Se define number con desplazamiento 8
    pos = tables.add(id0, lex)  # Se añade en la tabla global lex
    print(pos)  # Imprime posición de escritura
    quizaFalse = tables.add(id0, lex)  # Se intenta añadir otra vez lex
    print(quizaFalse)
    pos = tables.getPos(id0, ("string", 0))  # Buscamos posición del lex insertado en la línea 174
    e = tables.removeLexAt(id0, pos)  # Eliminamos el lex en la posición encontrada previamente
    print(e)  # Imprimimos el lex eliminado
    print(tables.getPos(id0, (
        1, "hola")))  # Intentamos buscar el lex eliminado previamente y mostramos por stdout su resultado
    # data = 'x_Aa= 3 + 42 * (s - t)'
    # data = '''int a=2;
    #     a = a + 2; a_1/*a &
    #
    #     adasdas */
    #     /* asd/asd*/ true
    #     false true
    #     /*"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"*/
    #
    #     if (a ==32766 & b == 2) _
    #     a--;'''

    # f = open('Prueba.txt', 'r')
    # data = f.read()
    # sys.stdout = open("Tokens.txt", "w")
    # sys.stderr = open("Error.txt", "w")
    # lexer = JSLexer(data)

    # for tok in lexer.get_token():
    #    print(f'< {tok.type} , {tok.value} >')
