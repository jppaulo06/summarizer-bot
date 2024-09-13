# ChatBot resumidor de E-mail

Este é um ChatBot montado para demonstração no evento Bootcamp 2024, organização
do USPCodelab.

O ChatBot é capaz de resumir e-mails, utilizando a API da MaritacaAI, e
responder ao usuário por Telegram com o resumo do e-mail.

# Arquitetura

O programa foi construído utilizando arquitetura hexagonal, também como uma
demonstração de como é possível construir um ChatBot de tal forma.

# Como rodar o Bot?

Baixe o repositório com
```
git clone https://github.com/jppaulo06/summarizer-bot
```

Entre no diretório do projeto
```
cd summarizer-bot
```

Crie o arquivo de configuração
```
cp .env.example .env
```

Edite o arquivo `.env` e adicione as credenciais do seu bot

Crie um ambiente virtual
```
python -m venv venv
```

Ative o ambiente virtual
```
source venv/bin/activate
```

Instale as dependências
```
pip install -r requirements.txt
```

Rode o programa
```
python src/main.py
```
