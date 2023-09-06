import threading
from datetime import datetime, timedelta
import os,time, json
import chardet
import requests
from dotenv import load_dotenv
from test import QtAPI

load_dotenv() 

def get_time_to_wait(signal):

    signal_time = datetime.strptime(signal.split(';')[2], '%H:%M').time()
    current_time = datetime.now().time()
    return datetime.combine(datetime.today(), signal_time) - datetime.combine(datetime.today(), current_time)

def send_message_to_channel(message):

    base_url = f"https://api.telegram.org/bot{os.environ.get('BOT_TOKEN')}/sendMessage"
    params = {
        "chat_id": os.environ.get("CHAT_ID"),
        "text": message,
        "parse_mode": "HTML"
    }

    response = requests.post(base_url, params=params)
    data = response.json()
    print(data)

def filter_signals_by_hour_interval(signals, start_hour, end_hour):
    filtered_signals = []
    
    start_time = datetime.strptime(start_hour, "%H:%M")
    end_time = datetime.strptime(end_hour, "%H:%M")
    
    for signal in signals:
        parts = signal.split(";")
        
        if len(parts) != 4:
            print(f"Ignoring invalid signal format: {signal}")
            continue
        
        signal_time = datetime.strptime(parts[2], "%H:%M")
        if start_time <= signal_time < end_time:
            filtered_signals.append(signal)
    
    return filtered_signals

def save(sessions):
    enc=chardet.detect(open('data.json','rb').read())['encoding']
    with open('data.json', 'r+', encoding= enc) as f:
        json.dump({ 'sessions': sessions }, f, indent=4)


class SignalsSender:

    def __init__(self, signals):
        self.__is_operating = False
        self.__tasks = [[], [], []]
        self.__signals = []
        self.__api = QtAPI(os.environ.get("EMAIL"), os.environ.get("PASSWORD"))

        # Fazer login a API
        check, resson = self.__api.login()

        print(check)

        if not check:
            print("Não foi possivel conectar com a API." + resson)
            return
        
        time.sleep(1800)
        
        enc=chardet.detect(open('data.json','rb').read())['encoding']
        with open('data.json', 'r+', encoding= enc) as f:
            self.__sessions = json.load(f)["sessions"]  

        self.read_signals(signals)
        self.set_sessions()

    def read_signals(self, signals):
        with open(signals, 'r+') as f:
            for l in f.readlines():
                self.__signals.append(l.strip())
        
    def set_sessions(self):
        session_0_signals = filter_signals_by_hour_interval(self.__signals, self.__sessions[0]['start'], self.__sessions[0]['end'])
        session_1_signals = filter_signals_by_hour_interval(self.__signals, self.__sessions[1]['start'], self.__sessions[1]['end'])
        session_2_signals = filter_signals_by_hour_interval(self.__signals, self.__sessions[2]['start'], self.__sessions[2]['end'])

        self.scheduler(0, session_0_signals)
        self.scheduler(1, session_1_signals)
        self.scheduler(2, session_2_signals)



    def scheduler(self, session, signals):
        for signal in signals:
            time_to_wait = get_time_to_wait(signal)
            time_to_wait -= timedelta(minutes=int(os.environ.get('MINUTES_TO_SEND')))

            print(time_to_wait.total_seconds())

            if time_to_wait.total_seconds() > 5:
                self.__tasks[session].append(threading.Timer(time_to_wait.total_seconds(), self.operate, args=[signal, session]))
                print(f"TIMER SET FOR SIGNAL: {signal}")
            else:
                print(f"Tempo do sinal {signal} já passou")

    def scheduler_relatorio(self, session):
        current_time = datetime.now().time()
        task_timer = datetime.combine(datetime.today(), datetime.strptime(self.__sessions[session]['end'], '%H:%M').time()) - datetime.combine(datetime.today(), current_time)
        if task_timer.total_seconds() > 0:
            threading.Timer(task_timer.total_seconds(), self.relatorio, args=[session]).start()
        return
        

    def operate(self, signal, session):
        if self.__is_operating == True:
            print(f"[{signal}] : Execução Cancelada outro sinal já está em execução")
        else:
            self.__is_operating = True
            asset = signal.split(';')[1]
            asset, check, isOTC = self.__api.check_asset_open(asset)
            print(asset, check, isOTC)

            if check == None:
                print(f"[{signal}] Não existe. Operação cancelada.")
                self.__is_operating = False
                return

            if not check[2]:
                print(f"[{signal}] : Execução Cancelada par está fechado")
                self.__is_operating = False
                return
            
            print(signal)
            signal_time = datetime.strptime(signal.split(";")[2], "%H:%M")
            op_duration = int(os.environ.get('OPERATION_TIME'))
            op_time = signal_time + timedelta(minutes=op_duration / 60)
            gale_1_time = signal_time + timedelta(minutes=(op_duration / 60) * 2)
            gale_2_time = signal_time + timedelta(minutes=(op_duration / 60) * 3)
            print(f"[{signal}] : INICIANDO EXECUÇÃO DA OPERAÇÃO")
            send_message_to_channel(f'''💰5 minutos de expiração
{signal}

🕐TEMPO PARA {op_time.strftime("%H:%M")}

1º GALE —> TEMPO PARA {gale_1_time.strftime("%H:%M")}
2º GALE —> TEMPO PARA {gale_2_time.strftime("%H:%M")}

<a href="https://bit.ly/path">📲 Clique para abrir a corretora</a>
<a href="https://t.me/link">🙋‍♂️ Não sabe operar ainda? Clique aqui</a>''')
                                    
            time.sleep(get_time_to_wait(signal).total_seconds())

            print(f"[{signal}] : REALIZANDO ENTRADA")
            result = self.__api.buy_and_check_win(signal, isOTC)
            print(f"[{signal}] : {result}")

            # GALE 1
            if result == "LOSS":
                print(f"[{signal}] : ENTRANDO NO GALE 1")
                result = self.__api.buy_and_check_win(signal, isOTC)

            # WIN DIRETO
            else:
                print(f"[{signal}] : OPERAÇÃO FINALIZADA, WIN DIRETO")
                send_message_to_channel(f"WIN DIRETO")
                self.__sessions[session]['win'] += 1
                self.__sessions[session]['ops'].append(f'{signal} WIN')
                save(self.__sessions)
                self.finish_op(session)
                self.__is_operating = True
                self.run_activate_operation_thread()
                return

            # GALE 2
            if result == "LOSS":
                print(f"[{signal}] : ENTRANDO NO GALE 2")
                result = self.__api.buy_and_check_win(signal, isOTC)

            # WIN GALE 1
            else:
                print(f"[{signal}] : OPERAÇÃO FINALIZADA, WIN NO GALE 1")
                send_message_to_channel(f"WIN GALE 1")
                self.__sessions[session]['win'] += 1
                self.__sessions[session]['ops'].append(f'{signal} WIN')
                save(self.__sessions)
                self.finish_op(session)
                self.__is_operating = True
                self.run_activate_operation_thread()
                return 

            if result == "LOSS":
                print(f"[{signal}] : OPERAÇÃO FINALIZADA, LOSS")
                send_message_to_channel(f"LOSS")
                self.__sessions[session]['loss'] += 1
                self.__sessions[session]['ops'].append(f'{signal} LOSS')
                save(self.__sessions)
                self.finish_op(session)
                self.__is_operating = True
                self.run_activate_operation_thread()
                return
            
            # WIN GALE 2
            else:
                print(f"[{signal}] : OPERAÇÃO FINALIZADA, WIN NO GALE 2")
                send_message_to_channel(f"WIN GALE 2")
                self.__sessions[session]['win'] += 1
                self.__sessions[session]['ops'].append(f'{signal} WIN')
                save(self.__sessions)
                self.finish_op(session)
                self.__is_operating = True
                self.run_activate_operation_thread()
                return
            
    def relatorio(self, session):
        if len(self.__sessions[session]['ops']) > 0:
            while True:
                if self.__is_operating:
                    continue
                else:
                    r = "\n".join(self.__sessions[session]['ops'])
                    send_message_to_channel(f'RELATÓRIO DA SESSÃO {session}\n\n{r}')
                    break      
        return
        

    def finish_op(self, session):
        if self.__sessions[session]['win'] > self.__sessions[session]['max_win']:
            self.end(session)
            send_message_to_channel("Sessão encerrada, stop win")
        
        if self.__sessions[session]['loss'] > self.__sessions[session]['max_loss']:
            self.end(session)
            send_message_to_channel("Sessão encerrada, stop loss")

        # PRÉVIA DO RESULTADO
        if self.__sessions[session]['win'] >= 4:
            preview = "\n".join(self.__sessions[session]['ops'])
            send_message_to_channel(f'''PRÉVIA DO RESULTADO

{preview}
''')
        
        self.__is_operating = False
        return 
          
    def start(self):
        print(self.__sessions, self.__tasks)
        for s in self.__tasks:
            for t in s:
                t.start()

    def end(self, session):
        for s in self.__tasks[session]:
            s.cancel()

    # Adicionados em manutenção
    def activate_operation_after(self,seconds: int = 1500):
        time.sleep(seconds)
        self.__is_operating = False

    def run_activate_operation_thread(self):
        thread = threading.Thread(
            target=self.activate_operation_after
        )
        thread.start()