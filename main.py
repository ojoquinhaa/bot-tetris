from sender import SignalsSender
from formater import Formater
import schedule
from json import load
import time
import sys
from io import StringIO
import subprocess
from datetime import datetime

def run_process():
    formatter = Formater(signals_file="signals.txt")
    formatter.save_in_file()

    signal_sender = SignalsSender("signals.txt")
    signal_sender.start()

# Abre o arquivo JSON no modo de leitura (substitua 'example.json' pelo caminho para o seu arquivo JSON)
with open('data.json', 'r') as file:
    # Usa json.load() para analisar o conteúdo do arquivo JSON em um objeto Python
    data: dict = load(file)

# Pega a hora atual
now = datetime.now()
now_hour = now.hour
now_minute = now.minute
now_decimal_hour = now_hour + (now_minute / 60)

# Itera por todas as sessões
for session in data["sessions"]:
    # Horario de inicio da sessão em decimal
    initial_hours, initial_minutes = map(int, session["start"].split(":"))
    decimal_initial_hours = initial_hours + (initial_minutes / 60)

    # Horario de fim da sessão em decimal
    final_hours, final_minutes = map(int, session["end"].split(":"))
    decimal_final_hours = final_hours + (final_minutes / 60)

    # Se estiver dentro do horario inicia da mesma forma
    if now_decimal_hour > decimal_initial_hours and now_decimal_hour < decimal_final_hours:
        run_process()

    # Executa o código no início de cada sessão
    schedule.every().day.at(session["start"]).do(run_process)

clear_terminal = False

# Enquanto o código está em execução
while True:
    # Executa as funções agendadas
    schedule.run_pending()

    # Redireciona a saída padrão (stdout) para uma variável
    original_stdout = sys.stdout
    sys.stdout = StringIO()

    # Obtém a saída capturada e a armazena em uma variável
    captured_output = sys.stdout.getvalue()

    # Restaura a saída padrão original
    sys.stdout = original_stdout

    # Reinicia o processo, se for encontrado um erro de conexão
    if 'Não foi possível conectar à API.' in captured_output:
        run_process()
        clear_terminal = True

    # Limpa o terminal, se necessário
    if clear_terminal:
        if sys.platform.startswith("win"):
            subprocess.call("cls", shell=True)  # Limpa o terminal no Windows
        else:
            subprocess.call("clear", shell=True)  # Limpa o terminal em sistemas Unix/Linux

        clear_terminal = False  # Reseta a variável clear_terminal para False

    # Aguarda um segundo
    time.sleep(1)
