import os,time
from quotexapi.stable_api import Quotex
from dotenv import load_dotenv

load_dotenv()

class QtAPI:
    def __init__(self, email, passwd):
        self.__client = Quotex(email=email, password=passwd)

    def check_asset_open(self, asset):
        # Verifica se o nome do ativo possui um hífen (indicativo de OTC) na string
        if '-' in asset:
            # Divide o nome do ativo pelo hífen e pega a primeira parte
            asset_parts = asset.split('-')[0]
            # Formata o nome do ativo adicionando ' (OTC)' no final
            formatted_asset = f'{asset_parts[:3]}/{asset_parts[3:]} (OTC)'
        else:
            # Se não houver hífen, formata o nome do ativo diretamente
            formatted_asset = f'{asset[:3]}/{asset[3:]}'

        double_check: bool = False
        
        # Realiza uma verificação do estado do ativo (não mostrada no código)
        res = self.__client.check_asset_open(formatted_asset)

        # Se o estado do ativo não for encontrado sem OTC
        if not res[2]:
            print("Passsando pelo double check")
            # Verificar o estado do ativo com OTC
            formatted_asset = formatted_asset + " (OTC)"
            res = self.__client.check_asset_open(formatted_asset)
            double_check = True
        
        # Fecha a conexão (não mostrada no código)
        self.__client.close()
        # Retorna o nome do ativo formatado e o resultado da verificação
        return formatted_asset, res, double_check

    def login(self, attempts=2):
        check, reason = self.__client.connect()
        
        attempt = 1
        while attempt < attempts:
            if not self.__client.check_connect():
                print(f"Tentando reconectar, tentativa {attempt} de {attempts}")
                check, reason = self.__client.connect()
                if check:
                    print("Reconectado com sucesso!!!")
                    break
                else:
                    print("Erro ao reconectar.")
                    attempt += 1
                    if os.path.isfile("session.json"):
                        os.remove("session.json")
            elif not check:
                attempt += 1
            else:
                break
            time.sleep(0.5)
        return check, reason

    def buy_and_check_win(self, signal, isOTC: bool):
        _, asset, signal_time, direction = signal.split(";")
        if len(asset.split("-")) == 2:
            asset = asset.split("-")[0] + "_" + asset.split("-")[1].lower()
        direction = direction.lower()

        check_connect, message = self.login()
        while True:
            print(check_connect, message)
            if check_connect:
                self.__client.change_account("PRACTICE")

                print("Saldo corrente: ", self.__client.get_balance())
                amount = 10
                asset = asset
                direction = direction
                duration = int(os.environ.get("OPERATION_TIME"))
                print(f"[{signal}] : BUY({amount}, {asset}, {direction}, {duration})")
                
                # Se o sinal estiver em OTC
                if isOTC:
                    # Adicionar o otc na frente 
                    asset = asset + "_otc"

                status, buy_info = self.__client.buy(amount, asset, direction, duration)

                print(status, buy_info)
                if status:
                    print("Aguardando resultado...")
                    print(buy_info["id"])
                    if self.__client.check_win(buy_info["id"]):
                        print(f"\nWIN\nLucro: R$ {self.__client.get_profit()}")
                        self.__client.close()
                        return "WIN"
                        
                    else:
                        print(f"\nLOSS\nPrejuízo: R$ {self.__client.get_profit()}")
                        self.__client.close()
                        return "LOSS"
                        
                else:
                    print("Falha na operação!!!")
                print("Saldo Atual: ", self.__client.get_balance())