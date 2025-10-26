from flask import Flask, render_template, request, redirect, flash, session, url_for
import smtplib
from email.message import EmailMessage
from datetime import date
import csv
import os

app = Flask(__name__)
app.secret_key = 'chave_secreta_muito_segura'

# Configurações do email da barbearia
EMAIL_BARBEARIA = 'mrkbarbearia@gmail.com'
SENHA = 'glzr cvrj ttjk eaad'

# Tabela de serviços
servicos_valores = {
    "Corte Navalhado - R$30": 30,
    "Corte Social - R$25": 25,
    "Barba - R$15": 15,
    "Barba + Corte - R$40": 40,
    "Sobrancelhas - R$10": 10
}

# Página de login (admin)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']
        if usuario == 'admin' and senha == '1234':
            session['logado'] = True
            return redirect('/agendamentos-dia')
        else:
            flash('Usuário ou senha incorretos', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logado', None)
    return redirect('/login')


# Página inicial de agendamento
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        nome = request.form['nome']
        telefone = request.form['telefone']
        data_agendamento = request.form['data']
        horario = request.form['horario']
        servico = request.form['servico']

        # Verificar se já existe agendamento para esse dia e horário
        existe = False
        if os.path.exists('agendamentos.csv'):
            with open('agendamentos.csv', 'r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:  # Compara a data e o horário do agendamento atual com os que já existem no arquivo
                    if row[2] == data_agendamento and row[3] == horario:
                        existe = True  #Se encontrar, marca como existente
                        break

        if existe:
            flash('Já existe um agendamento nesse horário!', 'danger') # Mostra mensagem de erro na tela
            return redirect('/') # Redireciona de volta para o formulário

        # Enviar e-mail
        try:
            msg = EmailMessage()
            msg['Subject'] = 'Novo Agendamento - BARBEARIA MRK'
            msg['From'] = EMAIL_BARBEARIA
            msg['To'] = EMAIL_BARBEARIA
            msg.set_content(f"""
            Novo agendamento:

            Nome: {nome}
            Telefone: {telefone}
            Data: {data_agendamento}
            Horário: {horario}
            Serviço: {servico}
            """)

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(EMAIL_BARBEARIA, SENHA)
                smtp.send_message(msg)

            # Salvar em CSV
            with open('agendamentos.csv', 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([nome, telefone, data_agendamento, horario, servico])# Escreve os dados como uma nova linha:

            flash('Agendamento enviado com sucesso!', 'success')
        except Exception as e:
            flash(f'Erro ao enviar e-mail: {e}', 'danger')

        return redirect('/')

    return render_template('index.html', current_date=date.today().isoformat())


# Página com agendamentos do dia (admin)
@app.route('/agendamentos-dia')
def agendamentos_dia():
    if not session.get('logado'):
        return redirect('/login')

    hoje = date.today().isoformat()
    agendamentos = []

    try:# Lê os agendamentos do dia atual
        with open('agendamentos.csv', 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row[2] == hoje:   # compara a data
                    agendamentos.append(row) # adiciona na lista para exibir depois
    except FileNotFoundError:
        agendamentos = []

    return render_template('agendamentos_dia.html', agendamentos=agendamentos, data=hoje)


# Página de faturamento (admin)
@app.route('/faturamento')
def faturamento():
    if not session.get('logado'):
        return redirect('/login')

    hoje = date.today().isoformat()
    total = 0
    agendamentos_hoje = []

    try:
        with open('agendamentos.csv', 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                nome, telefone, data_agendamento, horario, servico = row
                if data_agendamento == hoje:
                    valor = servicos_valores.get(servico.strip(), 0)
                    total += valor
                    agendamentos_hoje.append((nome, servico, valor))
    except FileNotFoundError:
        pass

    return render_template('faturamento.html', data=hoje, agendamentos=agendamentos_hoje, total=total)

@app.route('/excluir/<string:data>/<string:horario>', methods=['POST'])
def excluir_agendamento(data, horario):
    if not session.get('logado'):
        return redirect('/login')

    nova_lista = []
    try:
        with open('agendamentos.csv', 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if not (row[2] == data and row[3] == horario):
                    nova_lista.append(row)

        with open('agendamentos.csv', 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(nova_lista)

        flash('Agendamento excluído com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir: {e}', 'danger')

    return redirect('/agendamentos-dia')

@app.route('/horarios-disponiveis')
def horarios_disponiveis():
    data_escolhida = request.args.get('data')
    todos_horarios = [f"{hora:02d}:00" for hora in range(6, 18)]  
    ocupados = []

    try: # Abre o arquivo CSV onde os agendamentos estão salvos
        with open('agendamentos.csv', 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader: # Verifica se o agendamento é para a mesma data escolhida
                if row[2] == data_escolhida: 
                    ocupados.append(row[3]) # Adiciona o horário agendado à lista de horários ocupados
    except FileNotFoundError:
        pass  

    return {'todos': todos_horarios, 'ocupados': ocupados}


if __name__ == '__main__':
    app.run(debug=True)
