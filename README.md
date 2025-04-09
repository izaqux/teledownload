# 📥 Teledownload

#### **Um script simples e eficiente para baixar arquivos de forma automatizada**
---

## 🚀 Instalação

**Para começar a usar o teledownload.py**

### Clone o repositório

```bash
	git clone https://github.com/izaqux/teledownload.git
	
	cd teledownload
```

---

**dependências**

```bash
	pip install telethon tabulate
```

**🔑 Obtenção das Credenciais da API**

<a href="https://my.telegram.org/auth" target="_blank">Telegram API</a>

---

<pre>
<b>
Uso: teledownload.py [-h] or [--help]

Comandos
        -id     API ID do Telegram
        -hash   API Hash do Telegram
        -gc     ID do grupo ou canal para baixar arquivos
        -lgc    Listar todos os chats, grupos ou canais
        --p     Pasta personalizada para downloads
        --ns    Deletar sessão após a execução

Exemplo
        python teledownload.py -id 999 -hash 999 -lgc
        python teledownload.py -id 999 -hash 999 -lgc --ns
        python teledownload.py -id 999 -hash 999 -gc -100999
        python teledownload.py -id 999 -hash 999 -gc -100999 --p "./NomeDaPasta"
        python teledownload.py -id 999 -hash 999 -gc -100999 --ns
</b>
</pre>