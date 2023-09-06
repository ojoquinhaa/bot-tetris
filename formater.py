class Formater:
    def __init__(self, signals_file: str) -> None:
        # Caminho para o arquivo com os sinais
        self.signals_file: str = signals_file

        # Lista das linhas com os sinais
        self.lines: list[str] = self.get_lines() 

        # Formatando as linhas separadas em uma lista
        self.formated_lines: list[str] = self.get_formated_lines()

        print(self.formated_lines)

    def get_lines(self) -> list[str]:
        # Percorrendo o arquivo
        with open(self.signals_file, 'r') as read_file:
            # Retornando as linhas em uma lista 
            return read_file.readlines()
        
    def get_formated_lines(self) -> list[str]:
        # Formatando todas as linhas removendo o '-OTC'
        return [line.replace('-OTC', '') for line in self.lines]
        
    def save_in_file(self) -> None:
        # Percorrendo o arquivo para salvamento
        with open(self.signals_file, 'w') as file:
            # Salvando as linhas formatadas
            file.writelines(self.formated_lines)